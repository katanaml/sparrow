from transformers import LayoutLMv2Processor, LayoutLMv2ForTokenClassification
from datasets import load_dataset

dataset = load_dataset('katanaml/cord')

# processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased")
# model = LayoutLMv2ForTokenClassification.from_pretrained("nielsr/layoutlmv2-finetuned-funsd")
processor = LayoutLMv2Processor.from_pretrained("microsoft/layoutlmv2-base-uncased", revision="no_ocr")
model = LayoutLMv2ForTokenClassification.from_pretrained("microsoft/layoutlmv2-base-uncased")