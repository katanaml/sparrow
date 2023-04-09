from fastapi import APIRouter, File, UploadFile, Form
from typing import Optional
from PIL import Image
import urllib.request
from io import BytesIO
import re
import time
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from config import settings


router = APIRouter()

from huggingface_hub import login
login(settings.huggingface_key)

processor = DonutProcessor.from_pretrained(settings.donut_processor)
model = VisionEncoderDecoderModel.from_pretrained(settings.donut_model)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def process_document(image):
    start_time = time.time()

    # prepare encoder inputs
    pixel_values = processor(image, return_tensors="pt").pixel_values

    # prepare decoder inputs
    task_prompt = "<s_cord-v2>"
    decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids

    # generate answer
    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    # postprocess
    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()  # remove first task start token

    end_time = time.time()
    print(f"Processing time: {end_time - start_time:.2f} seconds")

    return processor.token2json(sequence)


@router.post("/inference")
async def run_inference(file: Optional[UploadFile] = File(None), image_url: Optional[str] = Form(None)):
    if file:
        # Ensure the uploaded file is a JPG image
        if file.content_type not in ["image/jpeg", "image/jpg"]:
            return {"error": "Invalid file type. Only JPG images are allowed."}

        image = Image.open(BytesIO(await file.read()))
        result = process_document(image)
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg
        with urllib.request.urlopen(image_url) as url:
            image = Image.open(BytesIO(url.read()))
        result = process_document(image)
    else:
        result = {"info": "No input provided"}

    return result


@router.get("/statistics")
async def get_statistics():
    return {"message": "Inference statistics"}