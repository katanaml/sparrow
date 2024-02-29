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

4. Copy text PDF files to the `data` folder or use the sample data provided in the `data` folder.

5. Run the script, to convert text to vector embeddings and save in Weaviate. By default it will use `llamaindex` agent: 

```
./sparrow.sh ingest
```

You can specify agent name explicitly, for example:

```
./sparrow.sh ingest --agent haystack
```

```
./sparrow.sh ingest --agent llamaindex
```

6. Run the script, to process data with LLM RAG and return the answer. By default, it will use `llamaindex` agent. You can specify other agents (see ingest example), such as `haystack`: 

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

7. To run multimodal agent, use `vllamaindex` flag:

```
./sparrow.sh "guest_no, cashier_name" "int, str" --agent vllamaindex
```

### FastAPI Endpoint for Local LLM RAG

Sparrow enables you to run a local LLM RAG as an API using FastAPI, providing a convenient and efficient way to interact with our services. You can pass the name of the agent to be used for the inference. By default, `llamaindex` agent is used.

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

Example of API call through CURL:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "fields": "invoice_number",
  "types": "int",
  "agent": "LlamaIndex"
}'
```

Example of API call for multimodal request:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/sparrow-llm/inference' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "fields": "guest_no, cashier_name",
  "types": "int, str",
  "agent": "vllamaindex"
}'
```
