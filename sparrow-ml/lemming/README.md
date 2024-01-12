# Sparrow RAG - local data extraction LLM RAG

___

## Quickstart

### RAG runs offline on local CPU

1. Install Weaviate local DB with Docker:
   
```
docker compose up -d
```

2. Install the requirements: 

```
pip install -r requirements.txt
```

3. Install <a href="https://ollama.ai">Ollama</a> and pull LLM model specified in config.yml

4. Copy text PDF files to the `data` folder or use the sample data provided in the `data` folder.

5. Run the script, to convert text to vector embeddings and save in Weaviate: 

```
./sparrow.sh ingest
```

6. Run the script, to process data with LLM RAG and return the answer: 

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

### FastAPI endpoint

There is option to run local LLM RAG as API

1. Run endpoint

```
python api.py
```

2. Access endpoint docs

```
http://127.0.0.1:8000/api/v1/sparrow-llm/docs
```

![FastAPI endpoint](https://github.com/katanaml/sparrow/blob/main/sparrow-ui/donut/assets/lemming_2.png)
