from datasets import load_dataset

datasets = load_dataset("katanaml/cord")

#

example = datasets["validation"][1]

#

from PIL import Image, ImageDraw, ImageFont

image = Image.open(example['image_path'])
image = image.convert("RGB")

#

from transformers import LayoutLMv2Processor

processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")

encoding = processor(image, return_offsets_mapping=True, return_tensors="pt")
offset_mapping = encoding.pop('offset_mapping')

#

import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

for k,v in encoding.items():
  encoding[k] = v.to(device)

#

from transformers import LayoutLMv2ForTokenClassification

# load the fine-tuned model from the hub
model = LayoutLMv2ForTokenClassification.from_pretrained("katanaml/layoutlmv2-finetuned-cord")
id2label = model.config.id2label
model.to(device)

# forward pass
outputs = model(**encoding)

#

def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 1000),
        height * (bbox[1] / 1000),
        width * (bbox[2] / 1000),
        height * (bbox[3] / 1000),
    ]


predictions = outputs.logits.argmax(-1).squeeze().tolist()
token_boxes = encoding.bbox.squeeze().tolist()

width, height = image.size

#

import numpy as np

is_subword = np.array(offset_mapping.squeeze().tolist())[:,0] != 0

true_predictions = [id2label[pred] for idx, pred in enumerate(predictions) if not is_subword[idx]]
# true_predictions = [id2label[pred] for idx, pred in enumerate(predictions)]
true_boxes = [unnormalize_box(box, width, height) for idx, box in enumerate(token_boxes) if not is_subword[idx]]
# true_boxes = [unnormalize_box(box, width, height) for idx, box in enumerate(token_boxes)]

#

print(true_predictions)
print(true_boxes)
print(is_subword)

#

from PIL import ImageDraw
import numpy as np
import PIL

draw = ImageDraw.Draw(image)
font = ImageFont.load_default()


def iob_to_label(label):
    label = label[2:]
    if not label:
        return 'other'
    return label


label_ints = np.random.randint(0, len(PIL.ImageColor.colormap.items()), 30)

label_color_pil = [k for k, _ in PIL.ImageColor.colormap.items()]

label_color = [label_color_pil[i] for i in label_ints]
label2color = {}
for k, v in id2label.items():
    label2color[v[2:]] = label_color[k]

for prediction, box in zip(true_predictions, true_boxes):
    predicted_label = iob_to_label(prediction).lower()
    draw.rectangle(box, outline=label2color[predicted_label])
    draw.text((box[0] + 10, box[1] - 10), text=predicted_label, fill=label2color[predicted_label], font=font)

#

image.save('docs/invoice_inference_result.jpg')

def process_document(image):
    print('PROCESS DOCUMENT')

    return image