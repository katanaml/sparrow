from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from functools import lru_cache
from paddleocr import PaddleOCR
from PIL import Image
from urllib.request import Request, urlopen
from io import BytesIO
from pdf2image import convert_from_bytes
import os
import time
import io


router = APIRouter()


@lru_cache(maxsize=1)
def load_ocr_model():
    model = PaddleOCR(use_angle_cls=True, lang='en')
    return model


def merge_data(values):
    data = []
    for idx in range(len(values)):
        data.append([values[idx][1][0]])
        # print(data[idx])

    return data


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
            values.append(line)

    values = merge_data(values)

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"OCR done, worker PID: {worker_pid}")

    return values, processing_time


@router.post("/inference")
async def inference(file: UploadFile = File(None),
                    image_url: Optional[str] = Form(None)):
    result = None
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

        print(f"Processing time OCR: {processing_time:.2f} seconds")
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/inout-20211211_001.jpg
        # test PDF: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/invoice_1.pdf
        headers = {'User-Agent': 'Mozilla/5.0'} # to avoid 403 error
        req = Request(image_url, headers=headers)
        with urlopen(req) as response:
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

        print(f"Processing time OCR: {processing_time:.2f} seconds")
    else:
        result = {"info": "No input provided"}

    if result is None:
        raise HTTPException(status_code=400, detail=f"Failed to process the input.")

    return JSONResponse(status_code=status.HTTP_200_OK, content=result)