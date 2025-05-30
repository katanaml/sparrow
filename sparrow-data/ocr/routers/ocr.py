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
import tempfile
from typing import Dict, List, Tuple


router = APIRouter()


@lru_cache(maxsize=1)
def load_ocr_model():
    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False)

    return ocr


def extract_text_from_json(result_json: Dict, include_bbox: bool = False) -> Dict:
    """
    Extract text and optionally bounding boxes from OCR result

    Args:
        result_json: The JSON structure from res.json
        include_bbox: Whether to include bounding box information

    Returns:
        Simple text extraction with optional bounding boxes
    """

    # Extract the 'res' part which contains the actual OCR data
    ocr_data = result_json.get('res', {})

    # Get the basic components
    rec_texts = ocr_data.get('rec_texts', [])
    rec_scores = ocr_data.get('rec_scores', [])
    rec_boxes = ocr_data.get('rec_boxes', []) if include_bbox else []

    # Clean and filter text
    clean_texts = []
    text_regions = []

    for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
        if text and text.strip() and score > 0.3:  # Basic quality filter
            clean_text = text.strip()
            clean_texts.append(clean_text)

            # Add bounding box info if requested
            if include_bbox and i < len(rec_boxes):
                box = rec_boxes[i]
                if len(box) >= 4:
                    x1, y1, x2, y2 = box[:4]
                    text_regions.append({
                        "text": clean_text,
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2),
                            "width": int(x2 - x1),
                            "height": int(y2 - y1)
                        },
                        "confidence": round(float(score), 3)
                    })

    # Create output
    simple_output = {
        "extracted_text": " ".join(clean_texts),
        "text_count": len(clean_texts),
        "avg_confidence": round(sum(rec_scores) / len(rec_scores), 2) if rec_scores else 0
    }

    # Add bounding boxes if requested
    if include_bbox:
        simple_output["text_regions"] = text_regions

    return simple_output


def invoke_ocr(doc, content_type, include_bbox: bool = False):
    worker_pid = os.getpid()
    print(f"Handling OCR request with worker PID: {worker_pid}")
    start_time = time.time()

    ocr = load_ocr_model()

    # Determine file extension based on content type
    if content_type == "image/png":
        file_suffix = ".png"
        format_img = "PNG"
    else:
        file_suffix = ".jpg"
        format_img = "JPEG"

    # Use temporary file with automatic cleanup
    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as temp_file:
        temp_path = temp_file.name
        doc.save(temp_path, format=format_img)

    try:
        # Pass the file path to OCR model
        result = ocr.predict(temp_path)

        # Process results - keep it simple
        ocr_results = []
        for i, res in enumerate(result):
            # Get JSON directly from result object
            result_json = res.json

            # for debug purpose
            res.save_to_img("output")

            # Extract simple text
            simple_text = extract_text_from_json(result_json, include_bbox)
            ocr_results.append(simple_text)


        end_time = time.time()
        processing_time = end_time - start_time
        print(f"OCR done, worker PID: {worker_pid}")

        return ocr_results, processing_time

    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
            print(f"Temporary file {temp_path} cleaned up successfully")
        except OSError as e:
            print(f"Error cleaning up temporary file {temp_path}: {e}")


@router.post("/inference")
async def inference(file: UploadFile = File(None),
                    image_url: Optional[str] = Form(None),
                    include_bbox: Optional[bool] = Form(False)):
    """
    OCR inference endpoint

    Args:
        file: Upload file (image or PDF)
        image_url: URL to image or PDF
        include_bbox: Whether to include bounding box coordinates for each text region
    """
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

        result, processing_time = invoke_ocr(doc, file.content_type, include_bbox)

        print(f"Processing time OCR: {processing_time:.2f} seconds")
    elif image_url:
        # test image url: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/inout-20211211_001.jpg
        # test PDF: https://raw.githubusercontent.com/katanaml/sparrow/main/sparrow-ml/llm/data/invoice_1.pdf
        headers = {"User-Agent": "Mozilla/5.0"} # to avoid 403 error
        req = Request(image_url, headers=headers)
        with urlopen(req) as response:
            content_type = response.info().get_content_type()

            if content_type in ["image/jpeg", "image/jpg", "image/png"]:
                doc = Image.open(BytesIO(response.read()))
            elif content_type in ["application/pdf", "application/octet-stream"]:
                pdf_bytes = response.read()
                pages = convert_from_bytes(pdf_bytes, 300)
                doc = pages[0]
            else:
                return {"error": "Invalid file type. Only JPG/PNG images and PDF are allowed."}

        result, processing_time = invoke_ocr(doc, content_type, include_bbox)

        print(f"Processing time OCR: {processing_time:.2f} seconds")
    else:
        result = {"info": "No input provided"}

    if result is None:
        raise HTTPException(status_code=400, detail=f"Failed to process the input.")

    return JSONResponse(status_code=status.HTTP_200_OK, content=result)
