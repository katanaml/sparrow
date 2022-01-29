import pandas as pd

#

train = pd.read_pickle('data/cord/out/train.pkl')
val = pd.read_pickle('data/cord/out/dev.pkl')
test = pd.read_pickle('data/cord/out/test.pkl')

#

from collections import Counter

all_labels = [item for sublist in train[1] for item in sublist] + [item for sublist in val[1] for item in sublist] + [
    item for sublist in test[1] for item in sublist]

#

replacing_labels = {'menu.etc': 'O', 'menu.itemsubtotal': 'O', 'menu.sub_etc': 'O', 'menu.sub_unitprice': 'O',
                    'menu.vatyn': 'O',
                    'void_menu.nm': 'O', 'void_menu.price': 'O', 'sub_total.othersvc_price': 'O'}


#

def replace_elem(elem):
    try:
        return replacing_labels[elem]
    except KeyError:
        return elem


def replace_list(ls):
    return [replace_elem(elem) for elem in ls]


train[1] = [replace_list(ls) for ls in train[1]]
val[1] = [replace_list(ls) for ls in val[1]]
test[1] = [replace_list(ls) for ls in test[1]]

#

all_labels = [item for sublist in train[1] for item in sublist] + [item for sublist in val[1] for item in sublist] + [
    item for sublist in test[1] for item in sublist]
Counter(all_labels)

#

labels = list(set(all_labels))

#

label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for idx, label in enumerate(labels)}

#

from os import listdir
from torch.utils.data import Dataset
import torch
from PIL import Image


class CORDDataset(Dataset):
    """CORD dataset."""

    def __init__(self, annotations, image_dir, processor=None, max_length=512):
        """
        Args:
            annotations (List[List]): List of lists containing the word-level annotations (words, labels, boxes).
            image_dir (string): Directory with all the document images.
            processor (LayoutLMv2Processor): Processor to prepare the text + image.
        """
        self.words, self.labels, self.boxes = annotations
        self.image_dir = image_dir
        self.image_file_names = [f for f in listdir(image_dir)]
        self.processor = processor

    def __len__(self):
        return len(self.image_file_names)

    def __getitem__(self, idx):
        # first, take an image
        item = self.image_file_names[idx]
        image = Image.open(self.image_dir + item).convert("RGB")

        # get word-level annotations
        words = self.words[idx]
        boxes = self.boxes[idx]
        word_labels = self.labels[idx]

        assert len(words) == len(boxes) == len(word_labels)

        word_labels = [label2id[label] for label in word_labels]
        # use processor to prepare everything
        encoded_inputs = self.processor(image, words, boxes=boxes, word_labels=word_labels,
                                        padding="max_length", truncation=True,
                                        return_tensors="pt")

        # remove batch dimension
        for k, v in encoded_inputs.items():
            encoded_inputs[k] = v.squeeze()

        assert encoded_inputs.input_ids.shape == torch.Size([512])
        assert encoded_inputs.attention_mask.shape == torch.Size([512])
        assert encoded_inputs.token_type_ids.shape == torch.Size([512])
        assert encoded_inputs.bbox.shape == torch.Size([512, 4])
        assert encoded_inputs.image.shape == torch.Size([3, 224, 224])
        assert encoded_inputs.labels.shape == torch.Size([512])

        return encoded_inputs


#

from transformers import LayoutLMv2Processor

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased", revision="no_ocr")

train_dataset = CORDDataset(annotations=train,
                            image_dir='data/cord/CORD/train/image/',
                            processor=processor)
val_dataset = CORDDataset(annotations=val,
                          image_dir='data/cord/CORD/dev/image/',
                          processor=processor)
test_dataset = CORDDataset(annotations=test,
                           image_dir='data/cord/CORD/test/image/',
                           processor=processor)

#

encoding = train_dataset[0]
print(encoding.keys())
print()

#

for k,v in encoding.items():
  print(k, v.shape)
print()

#

print(processor.tokenizer.decode(encoding['input_ids']))
print()

#

from torch.utils.data import DataLoader

train_dataloader = DataLoader(train_dataset, batch_size=2, shuffle=True)
val_dataloader = DataLoader(val_dataset, batch_size=2, shuffle=True)
test_dataloader = DataLoader(test_dataset, batch_size=2)

#

from transformers import LayoutLMv2ForTokenClassification, AdamW
import torch
from tqdm import tqdm

model = LayoutLMv2ForTokenClassification.from_pretrained('microsoft/layoutlmv2-base-uncased',
                                                         num_labels=len(labels))

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
optimizer = AdamW(model.parameters(), lr=5e-5)

global_step = 0
num_train_epochs = 4

# put the model in training mode
model.train()
for epoch in range(num_train_epochs):
    print("Epoch:", epoch)
    for batch in tqdm(train_dataloader):
        # get the inputs;
        input_ids = batch['input_ids'].to(device)
        bbox = batch['bbox'].to(device)
        image = batch['image'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        token_type_ids = batch['token_type_ids'].to(device)
        labels = batch['labels'].to(device)

        # zero the parameter gradients
        optimizer.zero_grad()

        # forward + backward + optimize
        outputs = model(input_ids=input_ids,
                        bbox=bbox,
                        image=image,
                        attention_mask=attention_mask,
                        token_type_ids=token_type_ids,
                        labels=labels)
        loss = outputs.loss

        # print loss every 100 steps
        if global_step % 100 == 0:
            print(f"Loss after {global_step} steps: {loss.item()}")

        loss.backward()
        optimizer.step()
        global_step += 1

model.save_pretrained("data/cord/model")

def process_document(image):
    print('PROCESS DOCUMENT')

    return image
