from fastapi import APIRouter, File, UploadFile, Form
from typing import Optional
from PIL import Image
import urllib.request
from io import BytesIO
from config import settings
import utils
import os
import json
from routers.donut_inference import process_document_donut


router = APIRouter()

def count_values(obj):
    if isinstance(obj, dict):
        count = 0
        for value in obj.values():
            count += count_values(value)
        return count
    elif isinstance(obj, list):
        count = 0
        for item in obj:
            count += count_values(item)
        return count
    else:
        return 1


@router.post("/inference")
async def run_inference(file: Optional[UploadFile] = File(None), image_url: Optional[str] = Form(None),
                        model_in_use: str = Form('donut'), sparrow_key: str = Form(None)):

    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    result = []
    if file:
        # Ensure the uploaded file is a JPG image
        if file.content_type not in ["image/jpeg", "image/jpg"]:
            return {"error": "Invalid file type. Only JPG images are allowed."}

        image = Image.open(BytesIO(await file.read()))
        processing_time = 0
        if model_in_use == 'donut':
            result, processing_time = process_document_donut(image)
        utils.log_stats(settings.inference_stats_file, [processing_time, count_values(result), file.filename, settings.model])
        print(f"Processing time: {processing_time:.2f} seconds")
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg
        with urllib.request.urlopen(image_url) as url:
            image = Image.open(BytesIO(url.read()))

        processing_time = 0
        if model_in_use == 'donut':
            result, processing_time = process_document_donut(image)
        # parse file name from url
        file_name = image_url.split("/")[-1]
        utils.log_stats(settings.inference_stats_file, [processing_time, count_values(result), file_name, settings.model])
        print(f"Processing time inference: {processing_time:.2f} seconds")
    else:
        result = {"info": "No input provided"}

    return result


@router.get("/statistics")
async def get_statistics():
    file_path = settings.inference_stats_file

    # Check if the file exists, and read its content
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                content = json.load(file)
            except json.JSONDecodeError:
                content = []
    else:
        content = []

    return content
