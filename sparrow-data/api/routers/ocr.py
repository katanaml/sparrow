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
from pdf2image import convert_from_bytes
import io


router = APIRouter()

@lru_cache(maxsize=1)
def load_ocr_model():
    model = PaddleOCR(use_angle_cls=True, lang='en')
    return model


def invoke_ocr(doc, content_type):
    worker_pid = os.getpid()
    print(f"Handling OCR request with worker PID: {worker_pid}")
    start_time = time.time()

    model = load_ocr_model()

    bytes_img = io.BytesIO()

    format_img = "JPEG"
    if content_type == "image/png":
        format_img = "PNG"

    doc.save(bytes_img, format=format_img)
    bytes_data = bytes_img.getvalue()
    bytes_img.close()

    result = model.ocr(bytes_data, cls=True)

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
        if file.content_type in ["image/jpeg", "image/jpg", "image/png"]:
            doc = Image.open(BytesIO(await file.read()))
        elif file.content_type == "application/pdf":
            pdf_bytes = await file.read()
            pages = convert_from_bytes(pdf_bytes, 300)
            doc = pages[0]
        else:
            return {"error": "Invalid file type. Only JPG/PNG images and PDF are allowed."}

        result, processing_time = invoke_ocr(doc, file.content_type)

        utils.log_stats(settings.ocr_stats_file, [processing_time, file.filename])
        print(f"Processing time OCR: {processing_time:.2f} seconds")
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/invoices/processed/images/invoice_10.jpg
        # test PDF: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-data/docs/input/receipts/2021/us/bestbuy-20211211_006.pdf
        with urllib.request.urlopen(image_url) as response:
            content_type = response.info().get_content_type()

            if content_type in ["image/jpeg", "image/jpg", "image/png"]:
                doc = Image.open(BytesIO(response.read()))
            elif content_type == "application/octet-stream":
                pdf_bytes = response.read()
                pages = convert_from_bytes(pdf_bytes, 300)
                doc = pages[0]
            else:
                return {"error": "Invalid file type. Only JPG/PNG images and PDF are allowed."}

        result, processing_time = invoke_ocr(doc, content_type)

        # parse file name from url
        file_name = image_url.split("/")[-1]
        utils.log_stats(settings.ocr_stats_file, [processing_time, file_name])
        print(f"Processing time OCR: {processing_time:.2f} seconds")
    else:
        result = {"info": "No input provided"}

    return result
