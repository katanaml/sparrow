from fastapi import APIRouter, File, UploadFile, Form, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Tuple, List
from functools import lru_cache
from paddleocr import PaddleOCR
from PIL import Image
from urllib.request import Request, urlopen
from io import BytesIO
from pdf2image import convert_from_bytes
import os
import time
import tempfile
from rich import print


# Import experimental table processing (with fallback)
EXPERIMENTAL_AVAILABLE = False
try:
    from routers.experimental import enhance_tables, get_available_features
    EXPERIMENTAL_AVAILABLE = True
    print("[SUCCESS] Experimental table processing features loaded successfully")
except ImportError as e:
    print(f"[ERROR] WARNING: Experimental features not available: {e}")
    print("Table enhancement will be disabled. Install experimental package to enable.")


router = APIRouter()


@lru_cache(maxsize=1)
def load_ocr_model():
    ocr = PaddleOCR(
        text_detection_model_name="PP-OCRv5_server_det",
        text_recognition_model_name="PP-OCRv5_server_rec",
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


def invoke_ocr(doc: Image.Image, content_type: str, include_bbox: bool = False, enhance_tables: bool = False, debug: bool = False):
    """
    Enhanced OCR with optional table detection and grid drawing

    Args:
        doc: PIL Image to process
        content_type: MIME type of the image
        include_bbox: Whether to include bounding box coordinates
        enhance_tables: Whether to apply experimental table enhancement
        debug: Whether to save debug output

    Returns:
        Tuple of (ocr_results, processing_time, enhanced_image_base64, tables_info)
    """
    worker_pid = os.getpid()
    print(f"[INFO] Handling OCR request with worker PID: {worker_pid}")
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

            if debug:
                res.save_to_img("output")

            # Extract simple text
            simple_text = extract_text_from_json(result_json, include_bbox)

            ocr_results.append(simple_text)

        end_time = time.time()
        processing_time = end_time - start_time
        print(f"[SUCCESS] OCR processing completed in {processing_time:.2f}s, worker PID: {worker_pid}")

        return ocr_results, processing_time

    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
            print(f"[INFO] Temporary file {temp_path} cleaned up successfully")
        except OSError as e:
            print(f"[WARNING] Error cleaning up temporary file {temp_path}: {e}")


@router.post("/inference")
async def inference(file: UploadFile = File(None),
                    image_url: Optional[str] = Form(None),
                    include_bbox: Optional[bool] = Form(False),
                    enhance_tables: Optional[bool] = Form(False),
                    debug: Optional[bool] = Form(False)):
    """
    OCR inference endpoint with optional experimental table enhancement

    Args:
        file: Upload file (image or PDF)
        image_url: URL to image or PDF
        include_bbox: Whether to include bounding box coordinates for each text region
        enhance_tables: Whether to detect tables and draw grid lines (experimental feature)
        debug: Whether to save output images with bounding boxes

    Returns:
        JSON response with OCR results and optional table enhancement data
    """

    # Check if table enhancement is requested but not available
    if enhance_tables and not EXPERIMENTAL_AVAILABLE:
        print("[WARNING] Table enhancement requested but experimental features not available")
        # Continue processing without enhancement rather than failing
        enhance_tables = False

    result = None
    enhanced_image_base64 = None
    tables_info = None

    try:
        if file:
            # Process uploaded file
            if file.content_type in ["image/jpeg", "image/jpg", "image/png"]:
                doc = Image.open(BytesIO(await file.read()))
            elif file.content_type == "application/pdf":
                pdf_bytes = await file.read()
                pages = convert_from_bytes(pdf_bytes, 300)
                doc = pages[0]  # Process first page only
            else:
                print(f"[ERROR] Invalid file type: {file.content_type}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only JPG/PNG images and PDF are allowed."
                )

            result, processing_time = invoke_ocr(doc, file.content_type, include_bbox, enhance_tables, debug)
        elif image_url:
            # Process image from URL
            headers = {"User-Agent": "Mozilla/5.0"}  # to avoid 403 error
            req = Request(image_url, headers=headers)

            try:
                with urlopen(req) as response:
                    content_type = response.info().get_content_type()

                    if content_type in ["image/jpeg", "image/jpg", "image/png"]:
                        doc = Image.open(BytesIO(response.read()))
                    elif content_type in ["application/pdf", "application/octet-stream"]:
                        pdf_bytes = response.read()
                        pages = convert_from_bytes(pdf_bytes, 300)
                        doc = pages[0]  # Process first page only
                    else:
                        print(f"[ERROR] Invalid URL content type: {content_type}")
                        raise HTTPException(
                            status_code=400,
                            detail="Invalid file type. Only JPG/PNG images and PDF are allowed."
                        )

                result, processing_time = invoke_ocr(doc, content_type, include_bbox, enhance_tables, debug)
            except Exception as url_error:
                print(f"[ERROR] Failed to process URL {image_url}: {str(url_error)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to process URL: {str(url_error)}"
                )
        else:
            # No input provided
            available_features = {}
            if EXPERIMENTAL_AVAILABLE:
                try:
                    available_features = get_available_features()
                except Exception as feature_error:
                    print(f"[WARNING] Error getting available features: {str(feature_error)}")

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "info": "No input provided. Please upload a file or provide an image URL.",
                    "experimental_features_available": EXPERIMENTAL_AVAILABLE,
                    "available_features": available_features
                }
            )

        if result is None:
            print("[ERROR] OCR processing returned no results")
            raise HTTPException(status_code=400, detail="Failed to process the input.")

        # Prepare response data
        response_data = result

        # Add processing metadata
        if isinstance(response_data, list) and len(response_data) > 0:
            response_data[0]['processing_info'] = {
                'processing_time_seconds': processing_time,
                'experimental_features_used': enhance_tables and EXPERIMENTAL_AVAILABLE,
                'worker_pid': os.getpid()
            }

        return JSONResponse(status_code=status.HTTP_200_OK, content=response_data)

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"[ERROR] Unexpected error during OCR processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during OCR processing: {str(e)}"
        )


@router.get("/features")
async def get_experimental_features():
    """
    Get information about available experimental features

    Returns:
        JSON response with feature availability and descriptions
    """
    response = {
        "experimental_features_available": EXPERIMENTAL_AVAILABLE,
        "features": {}
    }

    if EXPERIMENTAL_AVAILABLE:
        try:
            response["features"] = get_available_features()
        except Exception as e:
            print(f"[ERROR] Error getting experimental features: {e}")
            response["error"] = "Error accessing experimental features"

    return JSONResponse(status_code=status.HTTP_200_OK, content=response)