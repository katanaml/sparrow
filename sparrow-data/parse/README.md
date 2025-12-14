# Sparrow Parse

[![PyPI version](https://badge.fury.io/py/sparrow-parse.svg)](https://badge.fury.io/py/sparrow-parse)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A powerful Python library for parsing and extracting structured information from documents using Vision Language Models (VLMs). Part of the [Sparrow](https://github.com/katanaml/sparrow) ecosystem for intelligent document processing.

## ✨ Features

- 🔍 **Document Data Extraction**: Extract structured data from invoices, forms, tables, and complex documents
- 🤖 **Multiple Backend Support**: MLX (Apple Silicon), Ollama, Docker, Hugging Face Cloud GPU, and local GPU inference
- 📄 **Multi-format Support**: Images (PNG, JPG, JPEG) and multi-page PDFs
- 🎯 **Schema Validation**: JSON schema-based extraction with automatic validation
- 📊 **Table Processing**: Specialized table detection and extraction capabilities
- 🖼️ **Image Annotation**: Bounding box annotations for extracted data
- 💬 **Text Instructions**: Support for instruction-based text processing
- ⚡ **Optimized Processing**: Image cropping, resizing, and preprocessing capabilities

## 🚀 Quick Start

### Installation

To run with MLX on macOS Silicon:

```bash
pip install sparrow-parse[mlx]
```

To run with Ollama on Linux/Windows:

```
pip install sparrow-parse
```

**Additional Requirements:**
- For PDF processing: `brew install poppler` (macOS) or `apt-get install poppler-utils` (Linux)
- For MLX backend: Apple Silicon Mac required
- For Hugging Face: Valid HF token with GPU access

### Basic Usage

```python
from sparrow_parse.vllm.inference_factory import InferenceFactory
from sparrow_parse.extractors.vllm_extractor import VLLMExtractor

# Initialize extractor
extractor = VLLMExtractor()

# Configure backend (MLX example)
config = {
    "method": "mlx",
    "model_name": "mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit"
}

# Create inference instance
factory = InferenceFactory(config)
model_inference_instance = factory.get_inference_instance()

# Prepare input data
input_data = [{
    "file_path": "path/to/your/document.png",
    "text_input": "retrieve [{\"field_name\": \"str\", \"amount\": 0}]. return response in JSON format"
}]

# Run inference
results, num_pages = extractor.run_inference(
    model_inference_instance, 
    input_data,
    debug=True
)

print(f"Extracted data: {results[0]}")
```

## 📖 Detailed Usage

### Backend Configuration

#### MLX Backend (Apple Silicon)
```python
config = {
    "method": "mlx",
    "model_name": "mlx-community/Qwen2.5-VL-72B-Instruct-4bit"
}
```

#### Ollama Backend
```python
config = {
    "method": "ollama",
    "model_name": "mistral-small3.2:24b-instruct-2506-q8_0"
}
```

#### Hugging Face Backend
```python
import os
config = {
    "method": "huggingface",
    "hf_space": "your-username/your-space",
    "hf_token": os.getenv('HF_TOKEN')
}
```

#### Local GPU Backend
```python
config = {
    "method": "local_gpu",
    "device": "cuda",
    "model_path": "path/to/model.pth"
}
```

### Input Data Formats

#### Document Processing
```python
input_data = [{
    "file_path": "invoice.pdf",
    "text_input": "extract invoice data: {\"invoice_number\": \"str\", \"total\": 0, \"date\": \"str\"}"
}]
```

#### Text-Only Processing
```python
input_data = [{
    "file_path": None,
    "text_input": "Summarize the key points about renewable energy."
}]
```

### Advanced Options

#### Table Extraction Only
```python
results, num_pages = extractor.run_inference(
    model_inference_instance,
    input_data,
    tables_only=True  # Extract only tables from document
)
```

#### Image Cropping
```python
results, num_pages = extractor.run_inference(
    model_inference_instance,
    input_data,
    crop_size=60  # Crop 60 pixels from all borders
)
```

#### Bounding Box Annotations
```python
results, num_pages = extractor.run_inference(
    model_inference_instance,
    input_data,
    apply_annotation=True  # Include bounding box coordinates
)
```

#### Generic Data Extraction
```python
results, num_pages = extractor.run_inference(
    model_inference_instance,
    input_data,
    generic_query=True  # Extract all available data
)
```

## 🛠️ Utility Functions

### PDF Processing
```python
from sparrow_parse.helpers.pdf_optimizer import PDFOptimizer

pdf_optimizer = PDFOptimizer()
num_pages, output_files, temp_dir = pdf_optimizer.split_pdf_to_pages(
    file_path="document.pdf",
    debug_dir="./debug",
    convert_to_images=True
)
```

### Image Optimization
```python
from sparrow_parse.helpers.image_optimizer import ImageOptimizer

image_optimizer = ImageOptimizer()
cropped_path = image_optimizer.crop_image_borders(
    file_path="image.jpg",
    temp_dir="./temp",
    debug_dir="./debug",
    crop_size=50
)
```

### Table Detection
```python
from sparrow_parse.processors.table_structure_processor import TableDetector

detector = TableDetector()
cropped_tables = detector.detect_tables(
    file_path="document.png",
    local=True,
    debug=True
)
```

## 🎯 Use Cases & Examples

### Invoice Processing
```python
invoice_schema = {
    "invoice_number": "str",
    "date": "str", 
    "vendor_name": "str",
    "total_amount": 0,
    "line_items": [{
        "description": "str",
        "quantity": 0,
        "price": 0.0
    }]
}

input_data = [{
    "file_path": "invoice.pdf",
    "text_input": f"extract invoice data: {json.dumps(invoice_schema)}"
}]
```

### Financial Tables
```python
table_schema = [{
    "instrument_name": "str",
    "valuation": 0,
    "currency": "str or null"
}]

input_data = [{
    "file_path": "financial_report.png", 
    "text_input": f"retrieve {json.dumps(table_schema)}. return response in JSON format"
}]
```

### Form Processing
```python
form_schema = {
    "applicant_name": "str",
    "application_date": "str",
    "fields": [{
        "field_name": "str",
        "field_value": "str or null"
    }]
}
```

## ⚙️ Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tables_only` | bool | False | Extract only tables from documents |
| `generic_query` | bool | False | Extract all available data without schema |
| `crop_size` | int | None | Pixels to crop from image borders |
| `apply_annotation` | bool | False | Include bounding box coordinates |
| `ocr_callback` | str | None | Callback for OCR |
| `debug_dir` | str | None | Directory to save debug images |
| `debug` | bool | False | Enable debug logging |
| `mode` | str | None | Set to "static" for mock responses |

## 🔧 Troubleshooting

### Common Issues

**Import Errors:**
```bash
# For MLX backend on non-Apple Silicon
pip install sparrow-parse --no-deps
pip install -r requirements.txt --exclude mlx-vlm

# For missing poppler
brew install poppler  # macOS
sudo apt-get install poppler-utils  # Ubuntu/Debian
```

**Memory Issues:**
- Use smaller models or reduce image resolution
- Enable image cropping to reduce processing load
- Process single pages instead of entire PDFs

**Model Loading Errors:**
- Verify model name and availability
- Check HF token permissions for private models
- Ensure sufficient disk space for model downloads

### Performance Tips

- **Image Size**: Resize large images before processing
- **Batch Processing**: Process multiple pages together when possible
- **Model Selection**: Choose appropriate model size for your hardware
- **Caching**: Models are cached after first load

## 📚 API Reference

### VLLMExtractor Class

```python
class VLLMExtractor:
    def run_inference(
        self,
        model_inference_instance,
        input_data: List[Dict],
        tables_only: bool = False,
        generic_query: bool = False, 
        crop_size: Optional[int] = None,
        apply_annotation: bool = False,
        ocr_callback: Optional[str] = None, 
        debug_dir: Optional[str] = None,
        debug: bool = False,
        mode: Optional[str] = None
    ) -> Tuple[List[str], int]
```

### InferenceFactory Class

```python
class InferenceFactory:
    def __init__(self, config: Dict)
    def get_inference_instance(self) -> ModelInference
```

## 🏗️ Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/katanaml/sparrow.git
cd sparrow/sparrow-data/parse

# Create virtual environment
python -m venv .env_sparrow_parse
source .env_sparrow_parse/bin/activate  # Linux/Mac
# or
.env_sparrow_parse\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Build package
pip install setuptools wheel
python setup.py sdist bdist_wheel

# Install locally
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

## 📄 Supported File Formats

| Format | Extension | Multi-page | Notes |
|--------|-----------|------------|-------|
| PNG | .png | ❌ | Recommended for tables/forms |
| JPEG | .jpg, .jpeg | ❌ | Good for photos/scanned docs |
| PDF | .pdf | ✅ | Automatically split into pages |

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

⭐ **Star us on [GitHub](https://github.com/katanaml/sparrow)** if you find Sparrow Parse useful!
