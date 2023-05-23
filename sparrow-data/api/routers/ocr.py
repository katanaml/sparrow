from fastapi import APIRouter, File, UploadFile, Form
from typing import Optional
from config import settings
from PIL import Image
import urllib.request
from io import BytesIO
import utils
import os
import time
from functools import lru_cache
from paddleocr import PaddleOCR


router = APIRouter()

@lru_cache(maxsize=1)
def load_ocr_model():
    model = PaddleOCR(use_angle_cls=True, lang='en')
    return model

def invoke_ocr(doc):
    worker_pid = os.getpid()
    print(f"Handling OCR request with worker PID: {worker_pid}")
    start_time = time.time()

    model = load_ocr_model()

    doc.save("data/tmp.jpeg", "JPEG")
    result = model.ocr("data/tmp.jpeg", cls=True)
    values = []
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            print(line)
            values.append(line[1][0])

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"OCR done, worker PID: {worker_pid}")

    return values, processing_time

@router.post("/ocr")
async def run_ocr(file: Optional[UploadFile] = File(None), image_url: Optional[str] = Form(None),
                  sparrow_key: str = Form(None)):

    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    result = []
    if file:
        # Ensure the uploaded file is a JPG image
        if file.content_type not in ["image/jpeg", "image/jpg", "image/png"]:
            return {"error": "Invalid file type. Only JPG and PNG images are allowed."}

        doc = Image.open(BytesIO(await file.read()))

        result, processing_time = invoke_ocr(doc)

        utils.log_stats(settings.ocr_stats_file, [processing_time, file.filename])
        print(f"Processing time OCR: {processing_time:.2f} seconds")
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg
        with urllib.request.urlopen(image_url) as url:
            doc = Image.open(BytesIO(url.read()))

        result, processing_time = invoke_ocr(doc)

        # parse file name from url
        file_name = image_url.split("/")[-1]
        utils.log_stats(settings.ocr_stats_file, [processing_time, file_name])
        print(f"Processing time OCR: {processing_time:.2f} seconds")
    else:
        result = {"info": "No input provided"}

    return result
