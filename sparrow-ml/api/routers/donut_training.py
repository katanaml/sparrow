# !pip install -q git+https://github.com/huggingface/transformers.git datasets sentencepiece
# !pip install -q pytorch-lightning==1.9.5 wandb

from config import settings
from datasets import load_dataset
from transformers import VisionEncoderDecoderConfig
from transformers import DonutProcessor, VisionEncoderDecoderModel

import json
import random
from typing import Any, List, Tuple

import torch
from torch.utils.data import Dataset

from torch.utils.data import DataLoader

import re
from nltk import edit_distance
import numpy as np
import os
import time

import pytorch_lightning as pl
from functools import lru_cache

from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import Callback
from config import settings

added_tokens = []

dataset_name = settings.dataset
base_config_name = settings.base_config
base_processor_name = settings.base_processor
base_model_name = settings.base_model
model_name = settings.model

@lru_cache(maxsize=1)
def prepare_job():
    print("Preparing job...")

    dataset = load_dataset(dataset_name)

    max_length = 768
    image_size = [1280, 960]

    # update image_size of the encoder
    # during pre-training, a larger image size was used
    config = VisionEncoderDecoderConfig.from_pretrained(base_config_name)
    config.encoder.image_size = image_size  # (height, width)
    # update max_length of the decoder (for generation)
    config.decoder.max_length = max_length
    # TODO we should actually update max_position_embeddings and interpolate the pre-trained ones:
    # https://github.com/clovaai/donut/blob/0acc65a85d140852b8d9928565f0f6b2d98dc088/donut/model.py#L602

    processor = DonutProcessor.from_pretrained(base_processor_name)
    model = VisionEncoderDecoderModel.from_pretrained(base_model_name, config=config)

    return model, processor, dataset, config, image_size, max_length


class DonutDataset(Dataset):
    """
    DonutDataset which is saved in huggingface datasets format. (see details in https://huggingface.co/docs/datasets)
    Each row, consists of image path(png/jpg/jpeg) and gt data (json/jsonl/txt),
    and it will be converted into input_tensor(vectorized image) and input_ids(tokenized string).
    Args:
        dataset_name_or_path: name of dataset (available at huggingface.co/datasets) or the path containing image files and metadata.jsonl
        max_length: the max number of tokens for the target sequences
        split: whether to load "train", "validation" or "test" split
        ignore_id: ignore_index for torch.nn.CrossEntropyLoss
        task_start_token: the special token to be fed to the decoder to conduct the target task
        prompt_end_token: the special token at the end of the sequences
        sort_json_key: whether or not to sort the JSON keys
    """

    def __init__(
            self,
            dataset_name_or_path: str,
            max_length: int,
            split: str = "train",
            ignore_id: int = -100,
            task_start_token: str = "<s>",
            prompt_end_token: str = None,
            sort_json_key: bool = True,
    ):
        super().__init__()

        model, processor, dataset, config, image_size, p1 = prepare_job()

        self.max_length = max_length
        self.split = split
        self.ignore_id = ignore_id
        self.task_start_token = task_start_token
        self.prompt_end_token = prompt_end_token if prompt_end_token else task_start_token
        self.sort_json_key = sort_json_key

        self.dataset = load_dataset(dataset_name_or_path, split=self.split)
        self.dataset_length = len(self.dataset)

        self.gt_token_sequences = []
        for sample in self.dataset:
            ground_truth = json.loads(sample["ground_truth"])
            if "gt_parses" in ground_truth:  # when multiple ground truths are available, e.g., docvqa
                assert isinstance(ground_truth["gt_parses"], list)
                gt_jsons = ground_truth["gt_parses"]
            else:
                assert "gt_parse" in ground_truth and isinstance(ground_truth["gt_parse"], dict)
                gt_jsons = [ground_truth["gt_parse"]]

            self.gt_token_sequences.append(
                [
                    self.json2token(
                        gt_json,
                        update_special_tokens_for_json_key=self.split == "train",
                        sort_json_key=self.sort_json_key,
                    )
                    + processor.tokenizer.eos_token
                    for gt_json in gt_jsons  # load json from list of json
                ]
            )

        self.add_tokens([self.task_start_token, self.prompt_end_token])
        self.prompt_end_token_id = processor.tokenizer.convert_tokens_to_ids(self.prompt_end_token)

    def json2token(self, obj: Any, update_special_tokens_for_json_key: bool = True, sort_json_key: bool = True):
        """
        Convert an ordered JSON object into a token sequence
        """
        if type(obj) == dict:
            if len(obj) == 1 and "text_sequence" in obj:
                return obj["text_sequence"]
            else:
                output = ""
                if sort_json_key:
                    keys = sorted(obj.keys(), reverse=True)
                else:
                    keys = obj.keys()
                for k in keys:
                    if update_special_tokens_for_json_key:
                        self.add_tokens([fr"<s_{k}>", fr"</s_{k}>"])
                    output += (
                            fr"<s_{k}>"
                            + self.json2token(obj[k], update_special_tokens_for_json_key, sort_json_key)
                            + fr"</s_{k}>"
                    )
                return output
        elif type(obj) == list:
            return r"<sep/>".join(
                [self.json2token(item, update_special_tokens_for_json_key, sort_json_key) for item in obj]
            )
        else:
            obj = str(obj)
            if f"<{obj}/>" in added_tokens:
                obj = f"<{obj}/>"  # for categorical special tokens
            return obj

    def add_tokens(self, list_of_tokens: List[str]):
        """
        Add special tokens to tokenizer and resize the token embeddings of the decoder
        """
        model, processor, dataset, config, image_size, p1 = prepare_job()

        newly_added_num = processor.tokenizer.add_tokens(list_of_tokens)
        if newly_added_num > 0:
            model.decoder.resize_token_embeddings(len(processor.tokenizer))
            added_tokens.extend(list_of_tokens)

    def __len__(self) -> int:
        return self.dataset_length

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Load image from image_path of given dataset_path and convert into input_tensor and labels
        Convert gt data into input_ids (tokenized string)
        Returns:
            input_tensor : preprocessed image
            input_ids : tokenized gt_data
            labels : masked labels (model doesn't need to predict prompt and pad token)
        """

        model, processor, dataset, config, image_size, p1 = prepare_job()

        sample = self.dataset[idx]

        # inputs
        pixel_values = processor(sample["image"], random_padding=self.split == "train",
                                 return_tensors="pt").pixel_values
        pixel_values = pixel_values.squeeze()

        # targets
        target_sequence = random.choice(self.gt_token_sequences[idx])  # can be more than one, e.g., DocVQA Task 1
        input_ids = processor.tokenizer(
            target_sequence,
            add_special_tokens=False,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )["input_ids"].squeeze(0)

        labels = input_ids.clone()
        labels[labels == processor.tokenizer.pad_token_id] = self.ignore_id  # model doesn't need to predict pad token
        # labels[: torch.nonzero(labels == self.prompt_end_token_id).sum() + 1] = self.ignore_id  # model doesn't need to predict prompt (for VQA)
        return pixel_values, labels, target_sequence


def build_data_loaders():
    print("Building data loaders...")

    model, processor, dataset, config, image_size, max_length = prepare_job()

    # we update some settings which differ from pretraining; namely the size of the images + no rotation required
    # source: https://github.com/clovaai/donut/blob/master/config/train_cord.yaml
    processor.feature_extractor.size = image_size[::-1]  # should be (width, height)
    processor.feature_extractor.do_align_long_axis = False

    train_dataset = DonutDataset(dataset_name, max_length=max_length,
                                 split="train", task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>",
                                 sort_json_key=False,  # cord dataset is preprocessed, so no need for this
                                 )

    val_dataset = DonutDataset(dataset_name, max_length=max_length,
                               split="validation", task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>",
                               sort_json_key=False,  # cord dataset is preprocessed, so no need for this
                               )

    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids(['<s_cord-v2>'])[0]

    # feel free to increase the batch size if you have a lot of memory
    # I'm fine-tuning on Colab and given the large image size, batch size > 1 is not feasible
    # Set num_workers=4
    train_dataloader = DataLoader(train_dataset, batch_size=1, shuffle=True, num_workers=4)
    val_dataloader = DataLoader(val_dataset, batch_size=1, shuffle=False, num_workers=4)

    return train_dataloader, val_dataloader, max_length


class DonutModelPLModule(pl.LightningModule):
    def __init__(self, config, processor, model):
        super().__init__()
        self.config = config
        self.processor = processor
        self.model = model

        self.train_dataloader, self.val_dataloader, self.max_length = build_data_loaders()

    def training_step(self, batch, batch_idx):
        pixel_values, labels, _ = batch

        outputs = self.model(pixel_values, labels=labels)
        loss = outputs.loss
        self.log_dict({"train_loss": loss}, sync_dist=True)
        return loss

    def validation_step(self, batch, batch_idx, dataset_idx=0):
        pixel_values, labels, answers = batch
        batch_size = pixel_values.shape[0]
        # we feed the prompt to the model
        decoder_input_ids = torch.full((batch_size, 1), self.model.config.decoder_start_token_id, device=self.device)

        outputs = self.model.generate(pixel_values,
                                      decoder_input_ids=decoder_input_ids,
                                      max_length=self.max_length,
                                      early_stopping=True,
                                      pad_token_id=self.processor.tokenizer.pad_token_id,
                                      eos_token_id=self.processor.tokenizer.eos_token_id,
                                      use_cache=True,
                                      num_beams=1,
                                      bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                                      return_dict_in_generate=True, )

        predictions = []
        for seq in self.processor.tokenizer.batch_decode(outputs.sequences):
            seq = seq.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            seq = re.sub(r"<.*?>", "", seq, count=1).strip()  # remove first task start token
            predictions.append(seq)

        scores = list()
        for pred, answer in zip(predictions, answers):
            pred = re.sub(r"(?:(?<=>) | (?=</s_))", "", pred)
            # NOT NEEDED ANYMORE
            # answer = re.sub(r"<.*?>", "", answer, count=1)
            answer = answer.replace(self.processor.tokenizer.eos_token, "")
            scores.append(edit_distance(pred, answer) / max(len(pred), len(answer)))

            if self.config.get("verbose", False) and len(scores) == 1:
                print(f"Prediction: {pred}")
                print(f"    Answer: {answer}")
                print(f" Normed ED: {scores[0]}")

        return scores

    def validation_epoch_end(self, validation_step_outputs):
        # I set this to 1 manually
        # (previously set to len(self.config.dataset_name_or_paths))
        num_of_loaders = 1
        if num_of_loaders == 1:
            validation_step_outputs = [validation_step_outputs]
        assert len(validation_step_outputs) == num_of_loaders
        cnt = [0] * num_of_loaders
        total_metric = [0] * num_of_loaders
        val_metric = [0] * num_of_loaders
        for i, results in enumerate(validation_step_outputs):
            for scores in results:
                cnt[i] += len(scores)
                total_metric[i] += np.sum(scores)
            val_metric[i] = total_metric[i] / cnt[i]
            val_metric_name = f"val_metric_{i}th_dataset"
            self.log_dict({val_metric_name: val_metric[i]}, sync_dist=True)
        self.log_dict({"val_metric": np.sum(total_metric) / np.sum(cnt)}, sync_dist=True)

    def configure_optimizers(self):
        # TODO add scheduler
        optimizer = torch.optim.Adam(self.parameters(), lr=self.config.get("lr"))

        return optimizer

    def train_dataloader(self):
        return self.train_dataloader

    def val_dataloader(self):
        return self.val_dataloader


class PushToHubCallback(Callback):
    def on_train_epoch_end(self, trainer, pl_module):
        print(f"Pushing model to the hub, epoch {trainer.current_epoch}")
        pl_module.model.push_to_hub(model_name,
                                    commit_message=f"Training in progress, epoch {trainer.current_epoch}")

    def on_train_end(self, trainer, pl_module):
        print(f"Pushing model to the hub after training")
        pl_module.processor.push_to_hub(model_name,
                                        commit_message=f"Training done")
        pl_module.model.push_to_hub(model_name,
                                    commit_message=f"Training done")


def run_training_donut(max_epochs_param, val_check_interval_param, warmup_steps_param):
    worker_pid = os.getpid()
    print(f"Handling training request with worker PID: {worker_pid}")

    start_time = time.time()

    # Set epochs = 30
    # Set num_training_samples_per_epoch = training set size
    # Set val_check_interval = 0.4
    # Set warmup_steps: 425 / 8 = 54, 54 * 10 = 540, 540 * 0.15 = 81
    config_params = {"max_epochs": max_epochs_param,
                     "val_check_interval": val_check_interval_param,  # how many times we want to validate during an epoch
                     "check_val_every_n_epoch": 1,
                     "gradient_clip_val": 1.0,
                     "num_training_samples_per_epoch": 425,
                     "lr": 3e-5,
                     "train_batch_sizes": [8],
                     "val_batch_sizes": [1],
                     # "seed":2022,
                     "num_nodes": 1,
                     "warmup_steps": warmup_steps_param,  # 425 / 8 = 54, 54 * 10 = 540, 540 * 0.15 = 81
                     "result_path": "./result",
                     "verbose": False,
                     }

    model, processor, dataset, config, image_size, p1 = prepare_job()

    model_module = DonutModelPLModule(config, processor, model)

    # wandb_logger = WandbLogger(project="sparrow", name="invoices-donut-v5")

    # trainer = pl.Trainer(
    #     accelerator="gpu",
    #     devices=1,
    #     max_epochs=config_params.get("max_epochs"),
    #     val_check_interval=config_params.get("val_check_interval"),
    #     check_val_every_n_epoch=config_params.get("check_val_every_n_epoch"),
    #     gradient_clip_val=config_params.get("gradient_clip_val"),
    #     precision=16,  # we'll use mixed precision
    #     num_sanity_val_steps=0,
    #     # logger=wandb_logger,
    #     callbacks=[PushToHubCallback()],
    # )

    # trainer.fit(model_module)

    end_time = time.time()
    processing_time = end_time - start_time

    print(f"Training done, worker PID: {worker_pid}")

    return processing_time
