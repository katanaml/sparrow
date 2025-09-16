# Sparrow

[![PyPI - Python](https://img.shields.io/badge/python-v3.12+-blue.svg)](https://github.com/katanaml/sparrow)
[![GitHub Stars](https://img.shields.io/github/stars/katanaml/sparrow.svg)](https://github.com/katanaml/sparrow/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/katanaml/sparrow.svg)](https://github.com/katanaml/sparrow/issues)
[![Current Version](https://img.shields.io/badge/version-0.4.3-green.svg)](https://github.com/katanaml/sparrow)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Structured data extraction and instruction calling with ML, LLM and Vision LLM**

<p align="center">
  <img width="300" height="300" src="https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_logo_5.png">
</p>

<p align="center">
  <strong>🚀 <a href="https://sparrow.katanaml.io">Try Sparrow Online</a> | 📖 <a href="#-quickstart">Quick Start</a> | 🛠️ <a href="#️-installation">Installation</a> | 📚 <a href="#-examples">Examples</a> | 🤖 <a href="#-sparrow-agent">Agents</a></strong>
</p>

---

## 🌟 Sparrow UI

Interactive web interface for document processing.

### Try Online
Visit [sparrow.katanaml.io](https://sparrow.katanaml.io) for a live demo running on Mac Mini M4 Pro.

![Sparrow UI](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_ui.png)

### Sparrow UI Features
- **Drag & Drop**: Upload documents directly
- **Real-time Processing**: See results instantly  
- **Data Query**: JSON based schema for data query
- **Structured Output**: JSON structured output
- **Result Annotation**: View bounding boxes

## 📑 Table of Contents

- [✨ Key Features](#-key-features)
- [🏗️ Architecture](#️-architecture)
- [🚀 Quickstart](#-quickstart)
- [🛠️ Installation](#️-installation)
- [📚 Examples](#-examples)
- [💻 CLI Usage](#-cli-usage)
- [🌐 API Usage](#-api-usage)
- [🤖 Sparrow Agent](#-sparrow-agent)
- [📊 Dashboard](#-dashboard)
- [🔧 Pipeline Comparison](#-pipeline-comparison)
- [⚡ Performance Tips](#-performance-tips)
- [🔍 Troubleshooting](#-troubleshooting)
- [⭐ Star History](#-star-history)
- [📜 License](#-license)

## ✨ Key Features

🎯 **Universal Document Processing**: Handle invoices, receipts, forms, bank statements, tables    
🔧 **Pluggable Architecture**: Mix and match different pipelines (Sparrow Parse, Instructor, Agents)  
🖥️ **Multiple Backends**: MLX (Apple Silicon), Ollama, vLLM, Docker, Hugging Face Cloud GPU  
📱 **Multi-format Support**: Images (PNG, JPG) and multi-page PDFs  
🎨 **Schema Validation**: JSON schema-based extraction with automatic validation  
🌐 **API-First Design**: RESTful APIs for easy integration  
💬 **Instruction Calling**: Beyond document extraction - text processing, validation, decision making  
📊 **Visual Monitoring**: Built-in dashboard and agent workflow tracking  
🔒 **Enterprise Ready**: Rate limiting, usage analytics, commercial licensing available  
🚀 **Local Vision LLMs**: Mistral Small, QwenVL, olmOCR, Gemma3  

## 🏗️ Architecture

![Sparrow Architecture](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_architecture.jpeg)

### Core Components

| Component | Purpose | Use Case |
|-----------|---------|----------|
| **[Sparrow ML LLM](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/llm)** | Main API engine | Document processing pipelines |
| **[Sparrow Parse](https://github.com/katanaml/sparrow/tree/main/sparrow-data/parse)** | Vision LLM library | Structured JSON extraction |
| **[Sparrow Agents](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/agents)** | Workflow orchestration | Complex multi-step processing |
| **[Sparrow OCR](https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr)** | Text recognition | OCR preprocessing |
| **[Sparrow UI](https://github.com/katanaml/sparrow/tree/main/sparrow-ui/)** | Web interface | Interactive document processing |

## 🚀 Quickstart

### Prerequisites
- **Python 3.12.10+** (use `pyenv` for version management)
- **macOS** (for MLX backend) or **Linux/Windows** (for other backends)
- **GPU** (make sure GPU have enough memory to run selected Vision LLM)

### 30-Second Setup

```bash
# 1. Install pyenv and Python 3.12.10
pyenv install 3.12.10
pyenv global 3.12.10

# 2. Create virtual environment
python -m venv .env_sparrow_parse
source .env_sparrow_parse/bin/activate  # Linux/Mac
# or .env_sparrow_parse\Scripts\activate  # Windows

# 3. Install Sparrow Parse pipeline
git clone https://github.com/katanaml/sparrow.git
cd sparrow/sparrow-ml/llm
pip install -r requirements_sparrow_parse.txt

# 4. For macOS: Install poppler for PDF processing
brew install poppler

# 5. Start the API server
python api.py
```

Before running `pip install -r requirements_sparrow_parse.txt`, check your platform. If you are on macOS and want to run MLX backend, go to `requirements_sparrow_parse.txt` and make sure `sparrow-parse[mlx]` libary reference is defined. If you are running Sparrow on Linux/Windows, make sure to use `sparrow-parse` library reference, this will skip MLX related libraries.

### First Document Extraction

```bash
# Extract data from a bonds table
./sparrow.sh '[{"instrument_name":"str", "valuation":0}]' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "data/bonds_table.png"
```

**Result:**
```json
{
  "data": [
    {"instrument_name": "UNITS BLACKROCK...", "valuation": 19049},
    {"instrument_name": "UNITS ISHARES...", "valuation": 83488}
  ],
  "valid": "true"
}
```

Use `--options mlx` for MLX backend, `--options ollama` for Ollama backend. Make sure to provide correct Vision LLM model name, download model first separately with MLX or Ollama.

## 🛠️ Installation

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/katanaml/sparrow.git
cd sparrow
```

📖 **For complete installation instructions**, see our [detailed environment setup guide](environment_setup.md).

### Essential Steps Summary

1. **Python Environment**: Install Python 3.12.10 using pyenv
2. **Virtual Environments**: Create separate environments for different pipelines:
   - `.env_sparrow_parse` - for Sparrow Parse (Vision LLM)
   - `.env_instructor` - for Instructor (Text LLM) 
   - `.env_ocr` - for OCR service (optional)
3. **System Dependencies**: Install poppler for PDF processing
4. **Requirements**: Install pipeline-specific dependencies, for example `pip install -r requirements_sparrow_parse.txt`

### Platform-Specific Notes

**macOS:**
```bash
brew install poppler  # Required for PDF processing
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils libpoppler-cpp-dev
```

**Apple Silicon**: MLX backend available for optimal performance  
**NVIDIA/AMD GPU**: Use Ollama backend  
**CPU Only**: Use smaller models or Hugging Face cloud backend  

### Verification

```bash
# Test installation
python api.py --port 8002
# Visit http://localhost:8002/api/v1/sparrow-llm/docs
```

## 📚 Examples

### 🏦 Bank Statement Processing

![Bank Statement](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/bank_statement.png)

```bash
# Extract all data from bank statement
./sparrow.sh "*" \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "data/bank_statement.pdf"
```

<details>
<summary><strong>📄 View Complete JSON Output</strong></summary>

```json
{
  "bank": "First Platypus Bank",
  "address": "1234 Kings St., New York, NY 12123",
  "account_holder": "Mary G. Orta",
  "account_number": "1234567890123",
  "statement_date": "3/1/2022",
  "period_covered": "2/1/2022 - 3/1/2022",
  "account_summary": {
    "balance_on_march_1": "$25,032.23",
    "total_money_in": "$10,234.23",
    "total_money_out": "$10,532.51"
  },
  "transactions": [
    {
      "date": "02/01",
      "description": "PGD EasyPay Debit",
      "withdrawal": "203.24",
      "deposit": "",
      "balance": "22,098.23"
    },
    {
      "date": "02/02",
      "description": "AB&B Online Payment*****",
      "withdrawal": "71.23",
      "deposit": "",
      "balance": "22,027.00"
    },
    {
      "date": "02/04",
      "description": "Check No. 2345",
      "withdrawal": "",
      "deposit": "450.00",
      "balance": "22,477.00"
    },
    {
      "date": "02/05",
      "description": "Payroll Direct Dep 23422342 Giants",
      "withdrawal": "",
      "deposit": "2,534.65",
      "balance": "25,011.65"
    },
    {
      "date": "02/06",
      "description": "Signature POS Debit - TJP",
      "withdrawal": "84.50",
      "deposit": "",
      "balance": "24,927.15"
    },
    {
      "date": "02/07",
      "description": "Check No. 234",
      "withdrawal": "1,400.00",
      "deposit": "",
      "balance": "23,527.15"
    },
    {
      "date": "02/08",
      "description": "Check No. 342",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    },
    {
      "date": "02/09",
      "description": "FPB AutoPay***** Credit Card",
      "withdrawal": "456.02",
      "deposit": "",
      "balance": "23,096.13"
    },
    {
      "date": "02/08",
      "description": "Check No. 123",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    },
    {
      "date": "02/09",
      "description": "FPB AutoPay***** Credit Card",
      "withdrawal": "156.02",
      "deposit": "",
      "balance": "23,096.13"
    },
    {
      "date": "02/08",
      "description": "Cash Deposit",
      "withdrawal": "",
      "deposit": "25.00",
      "balance": "23,552.15"
    }
  ],
  "valid": "true"
}
```

</details>

### 📊 Financial Tables

![Bonds Table](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/bonds_table.png)

```bash
# Extract structured data from financial table
./sparrow.sh '[{"instrument_name":"str", "valuation":0}]' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "data/bonds_table.png"
```

<details>
<summary><strong>📄 View JSON Output</strong></summary>

```json
{
  "data": [
    {
      "instrument_name": "UNITS BLACKROCK FIX INC DUB FDS PLC ISHS EUR INV GRD CP BD IDX/INST/E",
      "valuation": 19049
    },
    {
      "instrument_name": "UNITS ISHARES III PLC CORE EUR GOVT BOND UCITS ETF/EUR",
      "valuation": 83488
    },
    {
      "instrument_name": "UNITS ISHARES III PLC EUR CORP BOND 1-5YR UCITS ETF/EUR",
      "valuation": 213030
    },
    {
      "instrument_name": "UNIT ISHARES VI PLC/JP MORGAN USD E BOND EUR HED UCITS ETF DIST/HDGD/",
      "valuation": 32774
    },
    {
      "instrument_name": "UNITS XTRACKERS II SICAV/EUR HY CORP BOND UCITS ETF/-1D-/DISTR.",
      "valuation": 23643
    }
  ],
  "valid": "true"
}
```

</details>

### 🧾 Invoice Processing

```bash
# Extract invoice with cropping for better accuracy
./sparrow.sh "*" \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --crop-size 60 \
  --file-path "data/invoice.pdf"
```

<details>
<summary><strong>📄 View Complete JSON Output</strong></summary>

```json
{
  "invoice_number": "61356291",
  "date_of_issue": "09/06/2012",
  "seller": {
    "name": "Chapman, Kim and Green",
    "address": "64731 James Branch, Smithmouth, NC 26872",
    "tax_id": "949-84-9105",
    "iban": "GB50ACIE59715038217063"
  },
  "client": {
    "name": "Rodriguez-Stevens",
    "address": "2280 Angela Plain, Hortonshire, MS 93248",
    "tax_id": "939-98-8477"
  },
  "items": [
    {
      "description": "Wine Glasses Goblets Pair Clear",
      "quantity": 5,
      "unit": "each",
      "net_price": 12.0,
      "net_worth": 60.0,
      "vat_percentage": 10,
      "gross_worth": 66.0
    },
    {
      "description": "With Hooks Stemware Storage Multiple Uses Iron Wine Rack Hanging",
      "quantity": 4,
      "unit": "each", 
      "net_price": 28.08,
      "net_worth": 112.32,
      "vat_percentage": 10,
      "gross_worth": 123.55
    },
    {
      "description": "Replacement Corkscrew Parts Spiral Worm Wine Opener Bottle Houdini",
      "quantity": 1,
      "unit": "each",
      "net_price": 7.5,
      "net_worth": 7.5,
      "vat_percentage": 10,
      "gross_worth": 8.25
    },
    {
      "description": "HOME ESSENTIALS GRADIENT STEMLESS WINE GLASSES SET OF 4 20 FL OZ (591 ml) NEW",
      "quantity": 1,
      "unit": "each",
      "net_price": 12.99,
      "net_worth": 12.99,
      "vat_percentage": 10,
      "gross_worth": 14.29
    }
  ],
  "summary": {
    "total_net_worth": 192.81,
    "total_vat": 19.28,
    "total_gross_worth": 212.09
  }
}
```

</details>

### 📄 Multi-page PDF Processing

```bash
# Process multi-page PDF with structured output per page
./sparrow.sh '{"table": [{"description": "str", "latest_amount": 0, "previous_amount": 0}]}' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "data/financial_report.pdf" \
  --debug-dir "debug/"
```

<details>
<summary><strong>📄 View JSON Output</strong></summary>

```json
[
    {
        "table": [
            {
                "description": "Revenues",
                "latest_amount": 12453,
                "previous_amount": 11445
            },
            {
                "description": "Operating expenses",
                "latest_amount": 9157,
                "previous_amount": 8822
            }
        ],
        "valid": "true",
        "page": 1
    },
    {
        "table": [
            {
                "description": "Revenues", 
                "latest_amount": 12453,
                "previous_amount": 11445
            },
            {
                "description": "Operating expenses",
                "latest_amount": 9157,
                "previous_amount": 8822
            }
        ],
        "valid": "true",
        "page": 2
    }
]
```

</details>

### 💬 Text Instruction Processing

```bash
# Instruction-based processing
./sparrow.sh "instruction: do arithmetic operation, payload: 2+2=" \
  --pipeline "sparrow-instructor" \
  --options mlx \
  --options mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit

# Instruction processing with document input
./sparrow.sh "check if business entity Chapman, Kim and Green is invoice issuing party" 
  --pipeline "sparrow-parse" 
  --instruction 
  --options mlx --options mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit 
  --file-path "invoice_1.jpg"
```


**JSON Output:**
```
The result of 2 + 2 is:

4
```


### 📈 Stock Data Function Calling

```bash
# Function calling example
./sparrow.sh assistant --pipeline "stocks" --query "Oracle"
```

**JSON Output:**
```json
{
  "company": "Oracle Corporation",
  "ticker": "ORCL"
}
```

**Additional Output:**
```
The stock price of the Oracle Corporation is 186.3699951171875. USD
```

## 💻 CLI Usage

### Basic Syntax

```bash
./sparrow.sh "<JSON_SCHEMA>" --pipeline "<PIPELINE>" [OPTIONS] --file-path "<FILE>"
```

### Command Line Arguments

| Argument | Type | Description | Example |
|----------|------|-------------|---------|
| `query` | JSON/String | Schema or instruction | `'[{"field":"str"}]'` |
| `--pipeline` | String | Pipeline to use | `sparrow-parse` |
| `--file-path` | Path | Input document | `data/invoice.pdf` |
| `--options` | String | Backend configuration | `mlx,model-name` |
| `--instruction` | Boolean | Sparrow query will be used as instruction | `--instruction` |
| `--validation` | Boolean | Sparrow query will be used for field validation | `--validation` |
| `--crop-size` | Integer | Border cropping pixels | `60` |
| `--page-type` | String | Page classification | `financial_table` |
| `--debug` | Boolean | Enable debug mode | `--debug` |
| `--debug-dir` | Path | Debug output folder | `./debug/` |

### Pipeline Options

#### Sparrow Parse (Vision LLM)
```bash
# MLX Backend (Apple Silicon)
./sparrow.sh '[{"instrument_name":"str", "valuation":0}]' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "data/bonds_table.png"

# Hugging Face Cloud GPU
--options huggingface --options your-space/model-name

# Additional flags
--options tables_only        # Extract only tables
--options validation_off     # Disable schema validation
--options apply_annotation   # Include bounding boxes
--page-type financial_table  # Classify page type
```

#### Sparrow Instructor (Text LLM)
```bash
# Instruction-based processing
./sparrow.sh "instruction: do arithmetic operation, payload: 2+2=" \
  --pipeline "sparrow-instructor" \
  --options mlx \
  --options mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit
```

### Advanced Examples

```bash
# Multi-page PDF with page classification
./sparrow.sh "*" \
  --page-type invoice \
  --page-type table \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "multi_page.pdf"

# Handle missing fields with null values
./sparrow.sh '[{"required_field":"str", "optional_field":"str or null"}]' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --file-path "document.png"

# Table extraction with cropping
./sparrow.sh '*' \
  --pipeline "sparrow-parse" \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --options tables_only \
  --crop-size 100 \
  --file-path "scan.pdf"

# Instruction execution
./sparrow.sh "check if business entity Chapman, Kim and Green is invoice issuing party" 
  --pipeline "sparrow-parse" 
  --instruction 
  --options mlx --options mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit 
  --file-path "invoice_1.jpg"

# Field validation
./sparrow.sh "tax_id,shipment_code,total_gross_worth" 
  --pipeline "sparrow-parse" 
  --validation 
  --options mlx --options mlx-community/Mistral-Small-3.1-24B-Instruct-2503-8bit 
  --file-path "invoice_1.jpg"

{
  "tax_id": true,
  "shipment_code": false,
  "total_gross_worth": true
}
```

## 🌐 API Usage

### Starting the Server

```bash
# Default port (8002)
python api.py

# Custom port
python api.py --port 8001

# Multiple instances
python api.py --port 8002 &  # Sparrow Parse
python api.py --port 8003 &  # Instructor
```

### API Endpoints

#### Document Extraction (`/inference`)

```bash
curl -X POST 'http://localhost:8002/api/v1/sparrow-llm/inference' \
  -H 'Content-Type: multipart/form-data' \
  -F 'query=[{"field_name":"str", "amount":0}]' \
  -F 'pipeline=sparrow-parse' \
  -F 'options=mlx,mlx-community/Qwen2.5-VL-72B-Instruct-4bit' \
  -F 'file=@document.pdf'
```

#### Text Instructions (`/instruction-inference`)

```bash
curl -X POST 'http://localhost:8002/api/v1/sparrow-llm/instruction-inference' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'query=instruction: analyze data, payload: {...}' \
  -d 'pipeline=sparrow-instructor' \
  -d 'options=mlx,mlx-community/Qwen2.5-VL-72B-Instruct-4bit'
```

### API Documentation

Visit `http://localhost:8002/api/v1/sparrow-llm/docs` for interactive Swagger documentation.

![API Documentation](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_api.png)

## 🤖 Sparrow Agent

![Sparrow Agents](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_agent.png)

Orchestrate complex document processing workflows with visual monitoring powered by Prefect.

### Features
- **Multi-step Workflows**: Chain classification, extraction, and validation
- **Visual Monitoring**: Real-time pipeline tracking
- **Error Handling**: Robust failure recovery
- **Extensible**: Custom agents for specific use cases

### Usage

```bash
# Start agent server
cd sparrow-ml/agents
python api.py --port 8001

# Process medical prescriptions
curl -X POST 'http://localhost:8001/api/v1/sparrow-agents/execute/file' \
  -F 'agent_name=medical_prescriptions' \
  -F 'extraction_params={"sparrow_key":"123456"}' \
  -F 'file=@prescription.pdf'
```

## 📊 Dashboard

Built-in analytics and monitoring dashboard at [sparrow.katanaml.io](https://sparrow.katanaml.io). This is part of Sparrow UI, requires local Oracle Database 23ai Free. 

![Dashboard](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_ui_3.png)

### Features
- **Usage Analytics**: Track API calls, success rates, performance
- **Geographic Distribution**: See usage by country
- **Model Performance**: Compare different model performance
- **Real-time Monitoring**: Live processing statistics

## 🔧 Pipeline Comparison

| Feature | Sparrow Parse | Sparrow Instructor | Sparrow Agents |
|---------|---------------|-------------------|----------------|
| **Input** | Documents + JSON schema | Text instructions | Complex workflows |
| **Output** | Structured JSON | Free-form text | Multi-step results |
| **Use Cases** | Data extraction, forms | Summarization, analysis | Enterprise workflows |
| **Validation** | Schema-based | Manual | Custom rules |
| **Complexity** | Simple | Medium | High |
| **Best For** | Invoices, tables, forms | Text processing | Multi-document flows |

### When to Use What

**Sparrow Parse**: Use for structured data extraction from documents  
**Sparrow Instructor**: Use for text analysis, summarization, Q&A  
**Sparrow Agents**: Use for complex multi-step document processing workflows  

## ⚡ Performance Tips

### Hardware Optimization

**Apple Silicon (MLX)**
- ✅ Best performance with unified memory
- ✅ Models: Qwen2.5-VL-72B, Mistral-Small-3.2-24B
- ⚠️ Requires macOS with Apple Silicon

**NVIDIA GPU**
- ✅ Use Ollama backends
- ✅ Recommended: Nvidia DGX Spark with 12GB+ VRAM or AMD GPU
- ⚠️ Requires CUDA setup

**CPU Only**
- ⚠️ Significantly slower
- ✅ Use smaller models (7B parameters max)
- ✅ Consider Hugging Face cloud backend

### Memory Management

```bash
# Reduce memory usage
--crop-size 100        # Crop large images
--options tables_only  # Process only tables

# For large PDFs
--debug-dir ./temp     # Monitor processing
# Split large PDFs manually if needed
```

### Model Selection

| Use Case | Recommended Model | Memory | Speed |
|----------|------------------|---------|--------|
| **Forms/Invoices** | Mistral-Small-3.1-24B | 35GB | Fast |
| **Complex Tables** | Qwen2.5-VL-72B | 50GB | Slower |
| **Quick Testing** | Qwen2.5-VL-7B | 20GB | Fastest |

## 🔍 Troubleshooting

### Common Issues

<details>
<summary>🚫 Installation Problems</summary>

**Python Version Issues:**
```bash
# Verify Python version
python --version  # Should be 3.12.10+

# Fix with pyenv
pyenv install 3.12.10
pyenv global 3.12.10
```

**MLX Installation (Apple Silicon):**
```bash
# If MLX fails to install
pip install --upgrade pip
pip install mlx-vlm --no-cache-dir
```

```bash
# If pip install command throws AttributeError: 'NoneType' object has no attribute 'get'
# POTENTIAL SECURITY RISK - SSL verification is bypassed. Apply if you know what you are doing
pip install mlx-vlm --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

**Poppler Missing:**
```bash
# macOS
brew install poppler

# Ubuntu/Debian  
sudo apt-get install poppler-utils

# Verify installation
pdftoppm -h
```

</details>

<details>
<summary>🔧 Runtime Issues</summary>

**Memory Errors:**
- Use smaller models (7B instead of 72B)
- Enable image cropping: `--crop-size 100`
- Process single pages instead of entire PDFs

**Model Loading Fails:**
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/
rm -rf ~/.mlx/

# Redownload models
python -c "from mlx_vlm import load; load('model-name')"
```

**API Connection Issues:**
```bash
# Check if server is running
curl http://localhost:8002/health

# Check logs
python api.py --debug
```

</details>

<details>
<summary>📄 Document Processing Issues</summary>

**Poor Extraction Quality:**
- Try image cropping: `--crop-size 60`
- Use `--options tables_only` for table documents
- Ensure image resolution is adequate (300+ DPI)
- Use schema validation: avoid `--options validation_off`

**PDF Processing Fails:**
```bash
# Test PDF manually
pdftoppm -png input.pdf output

# Check page count
python -c "
import pypdf
with open('file.pdf', 'rb') as f:
    reader = pypdf.PdfReader(f)
    print(f'Pages: {len(reader.pages)}')
"
```

**JSON Schema Errors:**
- Validate JSON syntax: Use [jsonlint.com](https://jsonlint.com)
- Use proper field types: `"str"`, `0`, `0.0`, `"str or null"`
- Test with simple schema first

</details>

### Getting Help

1. **📖 Check Documentation**: Review this README and component docs
2. **🐛 Search Issues**: [GitHub Issues](https://github.com/katanaml/sparrow/issues)  
3. **💬 Create Issue**: Provide logs, system info, minimal example
4. **📧 Commercial Support**: [abaranovskis@redsamuraiconsulting.com](mailto:abaranovskis@redsamuraiconsulting.com)

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=katanaml/sparrow&type=Date)](https://star-history.com/#katanaml/sparrow&Date)

## 📜 License

**Open Source**: Licensed under GPL 3.0. Free for open source projects and organizations under $5M revenue.

**Commercial**: Dual licensing available for proprietary use, enterprise features, and dedicated support.

**Contact**: [abaranovskis@redsamuraiconsulting.com](mailto:abaranovskis@redsamuraiconsulting.com) for commercial licensing and consulting.

## 👥 Authors

- **[Katana ML](https://katanaml.io)** - AI/ML consulting and solutions
- **[Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)** - Lead developer

---

<p align="center">
  <strong>⭐ Star us on GitHub if Sparrow is useful for your projects!</strong><br>
  <a href="https://github.com/katanaml/sparrow">github.com/katanaml/sparrow</a>
</p>
