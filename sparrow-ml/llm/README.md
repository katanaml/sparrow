# Sparrow RAG - local data extraction LLM RAG

___

Sparrow Agents - with Sparrow you can build independent LLM agents, and use API to invoke them from your system.

### RAG runs offline on a local machine

1. Install Weaviate local DB with Docker:
   
```
docker compose up -d
```

2. Install the requirements: 

```
pip install -r requirements.txt
```

3. Install <a href="https://ollama.ai">Ollama</a> and pull LLM model specified in config.yml

## Usage

Copy text PDF files to the `data` folder or use sample data provided in the `data` folder.

### Ingest

This step is required for `llamaindex` or `haystack` agents only.

Run the script, to convert text to vector embeddings and save in Weaviate. By default it will use `llamaindex` agent. Example with `llamaindex` agent:  

```
./sparrow.sh ingest --file-path /data/invoice_1.pdf --agent llamaindex --index-name Sparrow_llamaindex_doc1
```

Example with `haystack` agent:

```
./sparrow.sh ingest --file-path /data/invoice_1.pdf --agent haystack --index-name Sparrow_haystack_doc1
```

### Inference

Run the script, to process data with LLM RAG and return the answer. By default, it will use `llamaindex` agent. You can specify other agents (see ingest example), such as `haystack`: 

```
./sparrow.sh "invoice_number, invoice_date, client_name, client_address, client_tax_id, seller_name, seller_address,
seller_tax_id, iban, names_of_invoice_items, gross_worth_of_invoice_items, total_gross_worth" "int, str, str, str, str,
str, str, str, str, List[str], List[float], str" --agent llamaindex --index-name Sparrow_llamaindex_doc1
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

Example with `haystack` agent:

```
./sparrow.sh "invoice_number, invoice_date, client_name, client_address, client_tax_id, seller_name, seller_address,
seller_tax_id, iban, names_of_invoice_items, gross_worth_of_invoice_items, total_gross_worth" "int, str, str, str, str,
str, str, str, str, List[str], List[float], str" --agent haystack --index-name Sparrow_haystack_doc1
```

To run multimodal agent, use `vllamaindex` flag:

```
./sparrow.sh "guest_no, cashier_name" "int, str" --agent vllamaindex --file-path /data/inout-20211211_001.jpg
```

Use `vprocessor` agent to run OCR + LLM, this works best to process scanned docs

```
./sparrow.sh "guest_no, cashier_name, transaction_number, names_of_receipt_items, authorized_amount, receipt_date" "int, str, int, List[str], str, str" --agent vprocessor --file-path /data/inout-20211211_001.jpg
```

LLM function call example:

```
./sparrow.sh assistant --agent "fcall" --query "Exxon"
```

Response:

```json
{
  "company": "Exxon",
  "ticker": "XOM"
}
```

```
The stock price of the Exxon is 111.2699966430664. USD
```

## FastAPI Endpoint for Local LLM RAG

Sparrow enables you to run a local LLM RAG as an API using FastAPI, providing a convenient and efficient way to interact with our services. You can pass the name of the plugin to be used for the inference. By default, `llamaindex` agent is used.

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

![FastAPI endpoint](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/assets/lemming_2_.png)

API calls:

### Ingest

Ingest call with `llamaindex` agent:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'agent=llamaindex' \
  -F 'index_name=Sparrow_llamaindex_doc2' \
  -F 'file=@invoice_1.pdf;type=application/pdf'
```

Ingest call with `haystack` agent:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'agent=haystack' \
  -F 'index_name=Sparrow_haystack_doc2' \
  -F 'file=@invoice_1.pdf;type=application/pdf'
```

### Inference

Inference call with `llamaindex` agent:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'fields=invoice_number' \
  -F 'types=int' \
  -F 'agent=llamaindex' \
  -F 'index_name=Sparrow_llamaindex_doc2' \
  -F 'file='
```

Inference call with `haystack` agent:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'fields=invoice_number' \
  -F 'types=int' \
  -F 'agent=haystack' \
  -F 'index_name=Sparrow_haystack_doc2' \
  -F 'file='
```

Inference call with multimodal agent `vllamaindex`:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'fields=guest_no, cashier_name' \
  -F 'types=int, str' \
  -F 'agent=vllamaindex' \
  -F 'index_name=' \
  -F 'file=@inout-20211211_001.jpg;type=image/jpeg'
```

Inference call with OCR + LLM agent `vprocessor`:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'fields=guest_no, cashier_name, transaction_number, names_of_receipt_items, authorized_amount, receipt_date' \
  -F 'types=int, str, int, List[str], str, str' \
  -F 'agent=vprocessor' \
  -F 'index_name=' \
  -F 'file=@inout-20211211_001.jpg;type=image/jpeg'
```

## Author

[Katana ML](https://katanaml.io), [Andrej Baranovskij](https://github.com/abaranovskis-redsamurai)

## License

Licensed under the Apache License, Version 2.0. Copyright 2020-2024 Katana ML, Andrej Baranovskij. [Copy of the license](https://github.com/katanaml/sparrow/blob/main/LICENSE).
