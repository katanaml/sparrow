# Sparrow OCR

[![PyPI version](https://badge.fury.io/py/sparrow-ocr.svg)](https://badge.fury.io/py/sparrow-ocr)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Optical Character Recognition (OCR) and text extraction from documents and images. Part of the [Sparrow](https://github.com/katanaml/sparrow) ecosystem for intelligent document processing.

## ✨ Features

- 🔍 **Text Recognition**: Extract text from images and documents with high accuracy
- 📄 **Multi-format Support**: Images (PNG, JPG, JPEG) and PDFs
- 📍 **Bounding Box Detection**: Optional coordinate extraction for text regions
- 🌐 **Flexible Input**: Support for file upload and image URLs
- 🎯 **Debug Mode**: Visual output with bounding boxes for development
- ⚡ **Fast Processing**: Optimized OCR pipeline for production use
- 🔗 **API Integration**: RESTful API for easy integration

## 🚀 Quick Start

### Installation

**Additional Requirements:**
- For PDF processing: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)

### Basic Usage

```python
import requests

# OCR from uploaded file
with open("document.png", "rb") as f:
    response = requests.post(
        "http://localhost:8003/api/v1/sparrow-ocr/inference",
        files={"file": f}
    )

print(response.json())
```

## 📖 API Reference

### OCR Inference Endpoint

**POST** `/api/v1/sparrow-ocr/inference`

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | No* | Upload file (image or PDF) |
| `image_url` | String | No* | URL to image or PDF |
| `include_bbox` | Boolean | No | Include bounding box coordinates for each text region |
| `debug` | Boolean | No | Save output images with bounding boxes |

*Either `file` or `image_url` must be provided.

#### Request Examples

##### File Upload
```bash
curl -X POST "http://localhost:8003/api/v1/sparrow-ocr/inference" \
  -F "file=@document.pdf" \
  -F "include_bbox=true" \
  -F "debug=false"
```

##### Image URL
```bash
curl -X POST "http://localhost:8003/api/v1/sparrow-ocr/inference" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "image_url=https://example.com/image.jpg" \
  -d "include_bbox=true" \
  -d "debug=false"
```

##### Python Requests
```python
import requests

# File upload with bounding boxes
with open("invoice.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8003/api/v1/sparrow-ocr/inference",
        files={"file": f},
        data={
            "include_bbox": True,
            "debug": False
        }
    )

# Image URL processing
response = requests.post(
    "http://localhost:8003/api/v1/sparrow-ocr/inference",
    data={
        "image_url": "https://example.com/document.png",
        "include_bbox": False,
        "debug": True
    }
)
```

#### Response Format

##### Basic Text Extraction
```json
{
  "text": "Extracted text content from the document...",
  "pages": 1,
  "processing_time": 2.45,
  "status": "success"
}
```

##### With Bounding Boxes
```json
{
  "text": "Full extracted text...",
  "text_regions": [
    {
      "text": "Invoice Number: 12345",
      "bbox": [100, 50, 300, 80],
      "confidence": 0.95,
      "page": 1
    },
    {
      "text": "Date: 2024-01-15",
      "bbox": [100, 90, 250, 120],
      "confidence": 0.92,
      "page": 1
    }
  ],
  "pages": 1,
  "processing_time": 3.12,
  "status": "success"
}
```

## 🛠️ Development Setup

### Environment Setup

```bash
# Clone repository
git clone https://github.com/katanaml/sparrow.git
cd sparrow/sparrow-data/ocr

# Create virtual environment
python -m venv .env_ocr
source .env_ocr/bin/activate  # Linux/Mac
# or
.env_ocr\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install system dependencies
brew install poppler  # macOS
# or
sudo apt-get install poppler-utils  # Ubuntu/Debian
```

### Running the Service

```bash
# Start OCR API server
python api.py --port 8003
```

## 📚 Usage Examples

### Basic Text Extraction

```python
import requests

def extract_text(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "http://localhost:8003/api/v1/sparrow-ocr/inference",
            files={"file": f}
        )
    
    if response.status_code == 200:
        return response.json()["text"]
    else:
        raise Exception(f"OCR failed: {response.text}")

# Extract text from image
text = extract_text("invoice.png")
print(text)
```

### Extract Text with Bounding Boxes

```python
def extract_with_bbox(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "http://localhost:8003/api/v1/sparrow-ocr/inference",
            files={"file": f},
            data={"include_bbox": True}
        )
    
    result = response.json()
    
    # Process text regions
    for region in result["text_regions"]:
        print(f"Text: {region['text']}")
        print(f"Bbox: {region['bbox']}")
        print(f"Confidence: {region['confidence']}")
        print("---")
    
    return result

# Extract with coordinates
result = extract_with_bbox("form.pdf")
```

### Process Image from URL

```python
def process_url(image_url):
    response = requests.post(
        "http://localhost:8003/api/v1/sparrow-ocr/inference",
        data={
            "image_url": image_url,
            "include_bbox": True,
            "debug": False
        }
    )
    
    return response.json()

# Process remote image
result = process_url("https://example.com/receipt.jpg")
```

### Debug Mode for Development

```python
def debug_ocr(file_path):
    with open(file_path, "rb") as f:
        response = requests.post(
            "http://localhost:8003/api/v1/sparrow-ocr/inference",
            files={"file": f},
            data={
                "include_bbox": True,
                "debug": True  # Saves images with bounding boxes
            }
        )
    
    result = response.json()
    print(f"Debug images saved to: {result.get('debug_path', 'N/A')}")
    return result

# Debug OCR processing
debug_ocr("complex_document.pdf")
```

## 🎯 Use Cases

### Invoice Processing
```python
# Extract invoice data with bounding boxes for validation
invoice_result = extract_with_bbox("invoice.pdf")

# Find specific fields
for region in invoice_result["text_regions"]:
    text = region["text"].lower()
    if "invoice" in text and any(char.isdigit() for char in text):
        print(f"Found invoice number: {region['text']}")
        print(f"Location: {region['bbox']}")
```

### Form Processing
```python
# Process form fields with coordinates
form_result = process_with_bbox("application_form.png")

# Map text regions to form fields based on position
fields = {}
for region in form_result["text_regions"]:
    x, y = region["bbox"][:2]  # Top-left coordinates
    
    # Map based on position (example logic)
    if y < 100:
        fields["header"] = region["text"]
    elif 100 <= y < 200:
        fields["name_section"] = region["text"]
    # ... additional field mapping
```

### Receipt Scanning
```python
# Extract receipt data
receipt_text = extract_text("receipt.jpg")

# Parse common receipt patterns
import re

# Find total amount
total_pattern = r'total[:\s]*\$?(\d+\.?\d*)'
total_match = re.search(total_pattern, receipt_text, re.IGNORECASE)
if total_match:
    total = total_match.group(1)
    print(f"Total: ${total}")
```

## 🔧 Troubleshooting

### Common Issues

**Import Errors:**
```bash
# Missing system dependencies
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Ubuntu/Debian

# Python dependencies
pip install -r requirements.txt
```

**Low OCR Accuracy:**
- Ensure image resolution is at least 300 DPI
- Check image quality and contrast
- Try different OCR engines via configuration
- Use `debug=True` to visualize detection regions

**Memory Issues:**
- Reduce image size before processing
- Process large PDFs page by page
- Adjust confidence threshold to filter low-quality detections

**File Format Issues:**
```python
# Verify supported formats
import mimetypes
mime_type, _ = mimetypes.guess_type("document.pdf")
print(f"MIME type: {mime_type}")  # Should be image/* or application/pdf
```

### Performance Tips

- **Image Preprocessing**: Clean and enhance images before OCR
- **Batch Processing**: Process multiple files in parallel
- **Caching**: Cache results for repeated processing
- **Configuration**: Tune confidence thresholds for your use case

## 🤝 Integration with Sparrow Components

### With Sparrow Parse (Vision LLM)
```python
# First extract text with OCR, then process with Vision LLM
ocr_result = extract_with_bbox("invoice.pdf")
extracted_text = ocr_result["text"]

# Use OCR output for Vision LLM preprocessing
# This can improve accuracy for complex documents
```

### With Sparrow Agents
```python
# OCR as preprocessing step in agent workflows
@task
def ocr_preprocessing(file_path):
    return extract_with_bbox(file_path)

@task  
def structure_extraction(ocr_result):
    # Use OCR output for structured data extraction
    pass
```

## 📄 Supported File Formats

| Format | Extension | Multi-page | Notes |
|--------|-----------|------------|-------|
| PNG | .png | ❌ | Best for high-contrast text |
| JPEG | .jpg, .jpeg | ❌ | Good for photos and scanned docs |
| PDF | .pdf | ❌ | Handles single page PDF at the moment |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/katanaml/sparrow/blob/main/CONTRIBUTING.md) for details.

## 📞 Support

- 📖 [Documentation](https://github.com/katanaml/sparrow)
- 🐛 [Issue Tracker](https://github.com/katanaml/sparrow/issues)
- 💼 [Professional Services](mailto:abaranovskis@redsamuraiconsulting.com)

## 📜 License

Licensed under the GPL 3.0. Copyright 2020-2025 Katana ML, Andrej Baranovskij.

**Commercial Licensing:** Free for organizations with revenue under $5M USD annually. [Contact us](mailto:abaranovskis@redsamuraiconsulting.com) for commercial licensing options.

## 👥 Authors

- **[Katana ML](https://katanaml.io)**
- **[Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)**

---

⭐ **Star us on [GitHub](https://github.com/katanaml/sparrow)** if you find Sparrow OCR useful!
