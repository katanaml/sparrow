# Sparrow
Data extraction with ML and LLM

<p align="center">
  <img width="300" height="300" src="https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/sparrow_logo_5.png">
</p>

## The Principle

Sparrow is an innovative open-source solution for efficient data extraction and processing from various documents and images. It seamlessly handles forms, invoices, receipts, and other unstructured data sources. Sparrow stands out with its modular architecture, offering independent services and pipelines all optimized for robust performance. One of the critical functionalities of Sparrow - pluggable architecture. You can easily integrate and run data extraction pipelines using tools and frameworks like LlamaIndex, Haystack, or Unstructured. Sparrow enables local LLM data extraction pipelines through Ollama or Apple MLX. With Sparrow solution you get API, which helps to process and transform your data into structured output, ready to be integrated with custom workflows.

### Services

* **[sparrow-data-ocr](https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr)** - OCR service, providing optical character recognition as part of the Sparrow.
* **[sparrow-ml-llm](https://github.com/katanaml/sparrow/tree/main/sparrow-ml/llm)** - LLM RAG pipeline, Sparrow service for data extraction and document processing.
* **[sparrow-ui](https://github.com/katanaml/sparrow/tree/main/sparrow-ui/)** - Dashboard UI for LLM RAG pipeline.

Sparrow implementation with Donut ML model - <a href="https://github.com/katanaml/sparrow-donut">sparrow-donut</a>

## Installation

### LLM

1. Install Weaviate local DB with Docker:
   
```
docker compose up -d
```

2. Install the requirements: 

```
pip install -r requirements.txt
```

3. Install <a href="https://ollama.ai">Ollama</a> and pull LLM model specified in config.yml

### OCR

Follow the install steps outlined here:

1. Sparrow OCR services <a href="https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr">install steps</a>

## Usage

### LLM

1. Copy text PDF files to the `data` folder or use the sample data provided in the `data` folder.

2. Run the script, to convert text to vector embeddings and save in Weaviate. By default it will use LlamaIndex plugin: 

```
./sparrow.sh ingest
```

You can specify plugin name explicitly, for example:

```
./sparrow.sh ingest Haystack
```

```
./sparrow.sh ingest LlamaIndex
```

3. Run the script, to process data with LLM RAG and return the answer. By default, it will use LlamaIndex plugin. You can specify other plugins (see ingest example), such as Haystack: 

```
./sparrow.sh "invoice_number, invoice_date, client_name, client_address, client_tax_id, seller_name, seller_address,
seller_tax_id, iban, names_of_invoice_items, gross_worth_of_invoice_items, total_gross_worth" "int, str, str, str, str,
str, str, str, str, List[str], List[float], str"
```

Answer:

```json
{
    "invoice_number": 61356291,
    "invoice_date": "09/06/2012",
    "client_name": "Rodriguez-Stevens",
    "client_address": "2280 Angela Plain, Hortonshire, MS 93248",
    "client_tax_id": "939-98-8477",
    "seller_name": "Chapman, Kim and Green",
    "seller_address": "64731 James Branch, Smithmouth, NC 26872",
    "seller_tax_id": "949-84-9105",
    "iban": "GB50ACIE59715038217063",
    "names_of_invoice_items": [
        "Wine Glasses Goblets Pair Clear Glass",
        "With Hooks Stemware Storage Multiple Uses Iron Wine Rack Hanging Glass",
        "Replacement Corkscrew Parts Spiral Worm Wine Opener Bottle Houdini",
        "HOME ESSENTIALS GRADIENT STEMLESS WINE GLASSES SET OF 4 20 FL OZ (591 ml) NEW"
    ],
    "gross_worth_of_invoice_items": [
        66.0,
        123.55,
        8.25,
        14.29
    ],
    "total_gross_worth": "$212,09"
}
```

**FastAPI Endpoint for Local LLM RAG**

Sparrow enables you to run a local LLM RAG as an API using FastAPI, providing a convenient and efficient way to interact with our services.

To set this up:

1. Start the Endpoint

Launch the endpoint by executing the following command in your terminal:

```
python api.py
```

2. Access the Endpoint Documentation

You can view detailed documentation for the API by navigating to:

```
http://127.0.0.1:8000/api/v1/sparrow-llm/docs
```

For visual reference, a screenshot of the FastAPI endpoint

![FastAPI endpoint](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/lemming_2.png)

Example of API call through CURL

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "fields": "invoice_number",
  "types": "int"
}'
```

### OCR

Follow the steps outlined here:

1. Sparrow OCR services <a href="https://github.com/katanaml/sparrow/tree/main/sparrow-data/ocr">usage steps</a>

## Examples

### Inference with local LLM RAG

Request:

```
./sparrow.sh "invoice_number, invoice_date, client_name, client_address, client_tax_id, seller_name, seller_address,
seller_tax_id, iban, names_of_invoice_items, gross_worth_of_invoice_items, total_gross_worth" "int, str, str, str, str,
str, str, str, str, List[str], List[float], str"
```

Response:

![local RAG](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/lemming_1.png)

## Commercial usage

Sparrow is available for free commercial use. This offer applies to organizations with gross revenue below $5 million USD in the past 12 months.

For businesses exceeding this revenue limit and seeking to bypass GPL license restrictions for inference, please contact me at abaranovskis@redsamuraiconsulting.com to discuss dual licensing options. The same applies if you are looking for custom workflows to automate business processes, consulting options, and support/maintenance options.

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
