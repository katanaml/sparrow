from transformers import DonutProcessor, VisionEncoderDecoderModel
import locale

import re
import json
import torch
from tqdm.auto import tqdm
import numpy as np
from donut import JSONParseEvaluator
from datasets import load_dataset
from functools import lru_cache
import os
import time
from config import settings

locale.getpreferredencoding = lambda: "UTF-8"


@lru_cache(maxsize=1)
def prepare_model():
    processor = DonutProcessor.from_pretrained(settings.processor)
    model = VisionEncoderDecoderModel.from_pretrained(settings.model)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    model.eval()
    model.to(device)

    dataset = load_dataset(settings.dataset, split="test")

    return processor, model, device, dataset


def run_evaluate_donut():
    worker_pid = os.getpid()
    print(f"Handling evaluation request with worker PID: {worker_pid}")

    start_time = time.time()

    output_list = []
    accs = []

    processor, model, device, dataset = prepare_model()

    for idx, sample in tqdm(enumerate(dataset), total=len(dataset)):
        # prepare encoder inputs
        pixel_values = processor(sample["image"].convert("RGB"), return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        # prepare decoder inputs
        task_prompt = "<s_cord-v2>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
        decoder_input_ids = decoder_input_ids.to(device)

        # autoregressively generate sequence
        outputs = model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=model.decoder.config.max_position_embeddings,
            early_stopping=True,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True,
            num_beams=1,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )

        # turn into JSON
        seq = processor.batch_decode(outputs.sequences)[0]
        seq = seq.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        seq = re.sub(r"<.*?>", "", seq, count=1).strip()  # remove first task start token
        seq = processor.token2json(seq)

        ground_truth = json.loads(sample["ground_truth"])
        ground_truth = ground_truth["gt_parse"]
        evaluator = JSONParseEvaluator()
        score = evaluator.cal_acc(seq, ground_truth)

        accs.append(score)
        output_list.append(seq)

    end_time = time.time()
    processing_time = end_time - start_time

    scores = {"accuracies": accs, "mean_accuracy": np.mean(accs)}
    print(scores, f"length : {len(accs)}")
    print("Mean accuracy:", np.mean(accs))
    print(f"Evaluation done, worker PID: {worker_pid}")

    return scores, np.mean(accs), processing_time
