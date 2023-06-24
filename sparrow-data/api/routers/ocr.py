from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import Response, JSONResponse
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
import json
from routers.ocr_utils import merge_data
from routers.ocr_utils import store_data
from routers.ocr_utils import get_receipt_data
import motor.motor_asyncio
from typing import Optional
from pymongo import ASCENDING


router = APIRouter()

client = None
db = None


async def create_unique_index(db, collection_name, field):
    # Get a reference to your collection
    collection = db[collection_name]
    # Create an index on the specified field
    index_result = await collection.create_index([(field, ASCENDING)], unique=True)
    print(f"Unique index created or already exists: {index_result}")


@router.on_event("startup")
async def startup_event():
    if "MONGODB_URL" in os.environ:
        global client
        global db
        client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
        db = client.chatgpt_plugin
        print("Connected to MongoDB!")

        await create_unique_index(db, 'uploads', 'receipt_key')


@router.on_event("shutdown")
async def shutdown_event():
    if "MONGODB_URL" in os.environ:
        global client
        client.close()


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
            values.append(line)

    values = merge_data(values)

    end_time = time.time()
    processing_time = end_time - start_time
    print(f"OCR done, worker PID: {worker_pid}")

    return values, processing_time

@router.post("/ocr")
async def run_ocr(file: Optional[UploadFile] = File(None), image_url: Optional[str] = Form(None),
                  post_processing: Optional[bool] = Form(False), sparrow_key: str = Form(None)):

    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

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

        utils.log_stats(settings.ocr_stats_file, [processing_time, file.filename])
        print(f"Processing time OCR: {processing_time:.2f} seconds")

        if post_processing and "MONGODB_URL" in os.environ:
            print("Postprocessing...")
            result = await store_data(result, db)
            print(f"Stored data with key: {result}")
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

        if post_processing and "MONGODB_URL" in os.environ:
            print("Postprocessing...")
            result = await store_data(result, db)
            print(f"Stored data with key: {result}")
    else:
        result = {"info": "No input provided"}

    if result is None:
        raise HTTPException(status_code=404, detail=f"Failed to process the input.")

    return JSONResponse(status_code=status.HTTP_200_OK, content=result)


@router.get("/receipt_by_key/")
async def get_receipt_by_key(receipt_key: str, sparrow_key: str):
    if sparrow_key != settings.sparrow_key:
        return {"error": "Invalid Sparrow key."}

    if "MONGODB_URL" in os.environ:
        result = await get_receipt_data(receipt_key, db)

        if result is None:
            raise HTTPException(status_code=404, detail=f"Receipt {receipt_key} not found")

        return result

    return {"error": "No MongoDB URL provided."}


@router.get("/statistics")
async def get_statistics():
    file_path = settings.ocr_stats_file

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
