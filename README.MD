# Sparrow
[![PyPI - Python](https://img.shields.io/badge/python-v3.10+-blue.svg)](https://github.com/katanaml/sparrow)
[![GitHub Stars](https://img.shields.io/github/stars/katanaml/sparrow.svg)](https://github.com/katanaml/sparrow/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/katanaml/sparrow.svg)](https://github.com/katanaml/sparrow/issues)
[![Current Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/katanaml/sparrow)


Data processing with ML, LLM and Vision LLM

<p align="center">
  <img width="300" height="300" src="https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_logo_5.png">
</p>

## Overview

Sparrow is an innovative open-source solution for efficient data extraction and processing from various documents and images. It seamlessly handles forms, invoices, receipts, and other unstructured data sources. Sparrow stands out with its modular architecture, offering independent services and agents all optimized for robust performance. One of the critical functionalities of Sparrow - pluggable architecture. You can easily integrate and run data extraction pipelines using tools and frameworks like Sparrow Parse (with vision-language models support) or Instructor with Unstructured. Sparrow enables local LLM data extraction pipelines through various backends, such as vLLM, Ollama, PyTorch or Apple MLX. Sparrow Parse with VL model can run either on premise, or it can execute inference on cloud GPU. With Sparrow solution you get API, which helps to process and transform your data into structured output, ready to be integrated with custom workflows.

Sparrow Agents - with Sparrow you can build independent LLM agents, and use API to invoke them from your system.

![Sparrow](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_architecture.jpeg)

### Sparrow Components

* **[Sparrow ML LLM](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/llm)** - Sparrow main engine that runs various agents
* **[Sparrow Data Parse](https://github.com/katanaml/sparrow/tree/main/sparrow-data/parse)** - Sparrow library enabling Sparrow Parse agent functionality using VL LLM. Works great for structured JSON response generation
* **[Sparrow Data OCR](https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr)** - OCR service, providing optical character recognition
* **[Sparrow UI](https://github.com/katanaml/sparrow/tree/main/sparrow-ui/)** - Dashboard UI for Sparrow

## Sparrow UI

Try [Sparrow](https://katanaml-sparrow-ui.hf.space) UI shell app

![Sparrow UI](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_ui.png)

## Examples - data extraction with Sparrow

### Bank statement

![Bank statement](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/bank_statement.png)

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
  ]
}
```

### Bonds table

![Bank statement](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/bonds_table.png)

```json
[
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
]
```

## Quickstart

1. Install `pyenv` and then install Python into your environment
2. Create virtual environment for the Sparrow agent you want to run
3. Install requirements for the Sparrow agent you want to use. Keep in mind, depending on OS, it could be required to do additional install steps for some of the libraries (for example PaddleOCR)
4. Run Sparrow either from CLI or from API. You need to start API endpoint
5. Pass query in the form of JSON schema to extract data from the document

See detailed instructions below.

## Installation

1. Python environment

For more details, check out the [extended section](environment_setup.md).

2. Run Sparrow

You can run Sparrow on CLI or through API. To run on CLI, use `sparrow.sh` script. Run it from corresponding virtual environment, depending which agent you want to execute. `sparrow-parse` agent is using VL LLM model and it doesn't use Ollama. `sparrow-parse` agent runs VL LLM either locally or using cloud GPU.

## Inference

✅ Sparrow Parse agent, with GPU backend on Hugging Face

```
./sparrow.sh "[{"instrument_name":"string", "valuation":0}]" --agent "sparrow-parse" --debug --options huggingface --options katanaml/sparrow-qwen2-vl-7b --file-path "/data/bonds_table.png"
```

Answer:

```json
[
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
]
```

✅ LLM function call example:

```
./sparrow.sh assistant --agent "fcall" --query "Exxon"
```

Answer:

```json
{
  "company": "Exxon",
  "ticker": "XOM"
}
```

```
The stock price of the Exxon is 111.2699966430664. USD
```

✅ Use `instructor` agent to run RAG pipeline with Unstructured and Instructor libraries. Unstructured helps to pre-process data for better LLM responses. Instructor simplifies RAG pipeline and ensures JSON responses. This agent supports both PDF, JPG and PNG files

```
./sparrow.sh "names_of_invoice_items, gross_worth_of_invoice_items, total_gross_worth" "List[str], List[str], str" --agent instructor --file-path /data/invoice_1.pdf
```

## FastAPI Endpoint for Local LLM RAG

Sparrow enables you to run a local LLM RAG as an API using FastAPI, providing a convenient and efficient way to interact with our services. You can pass the name of the plugin to be used for the inference. By default, `sparrow-parse` agent is used.

To set this up:

1. Start the Endpoint

Launch the endpoint by executing the following command in your terminal:

```
python api.py
```

If you want to run agents from different Python virtual environments simultaneously, you can specify port, to avoid conflicts:

```
python api.py --port 8001
```

2. Access the Endpoint Documentation

You can view detailed documentation for the API by navigating to:

```
http://127.0.0.1:8000/api/v1/sparrow-llm/docs
```

For visual reference, a screenshot of the FastAPI endpoint

![FastAPI endpoint](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_api.png)

### API call inference

✅ `sparrow-parse` agent, this agent runs Visual LLM with GPU backend on Hugging Face

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'query=[{"instrument_name":"string","valuation":0}]' \
  -F 'agent=sparrow-parse' \
  -F 'options=huggingface,katanaml/sparrow-qwen2-vl-7b' \
  -F 'debug=false' \
  -F 'sparrow_key=' \
  -F 'file=@bonds_table.png;type=image/png'
```

## Commercial usage

Sparrow is available under the GPL 3.0 license, promoting freedom to use, modify, and distribute the software while ensuring any modifications remain open source under the same license. This aligns with our commitment to supporting the open-source community and fostering collaboration.

Additionally, we recognize the diverse needs of organizations, including small to medium-sized enterprises (SMEs). Therefore, Sparrow is also offered for free commercial use to organizations with gross revenue below $5 million USD in the past 12 months, enabling them to leverage Sparrow without the financial burden often associated with high-quality software solutions.

For businesses that exceed this revenue threshold or require usage terms not accommodated by the GPL 3.0 license—such as integrating Sparrow into proprietary software without the obligation to disclose source code modifications—we offer dual licensing options. Dual licensing allows Sparrow to be used under a separate proprietary license, offering greater flexibility for commercial applications and proprietary integrations. This model supports both the project's sustainability and the business's needs for confidentiality and customization.

If your organization is seeking to utilize Sparrow under a proprietary license, or if you are interested in custom workflows, consulting services, or dedicated support and maintenance options, please contact us at abaranovskis@redsamuraiconsulting.com. We're here to provide tailored solutions that meet your unique requirements, ensuring you can maximize the benefits of Sparrow for your projects and workflows.

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the GPL 3.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
