from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from engine import run_from_api
import uvicorn
import warnings
from typing import Annotated
import json


warnings.filterwarnings("ignore", category=DeprecationWarning)


# add asyncio to the pipeline

app = FastAPI(openapi_url="/api/v1/sparrow-llm/openapi.json", docs_url="/api/v1/sparrow-llm/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


class Query(BaseModel):
    fields: str
    types: str
    agent: str = "llamaindex"


@app.get("/")
def root():
    return {"message": "Sparrow LLM API"}


@app.post("/api/v1/sparrow-llm/inference", tags=["LLM Inference"])
def inference(
        q: Annotated[
            Query,
            Body(
                examples=[
                    {
                        "fields": "invoice_number",
                        "types": "int",
                        "agent": "llamaindex"
                    }
                ]
            )
        ]):
    query = 'retrieve ' + q.fields
    query_types = q.types

    query_inputs_arr = [param.strip() for param in q.fields.split(',')]
    query_types_arr = [param.strip() for param in query_types.split(',')]

    try:
        answer = run_from_api(q.agent, query_inputs_arr, query_types_arr, query, False)
    except ValueError as e:
        answer = '{"answer": "Invalid agent name"}'

    if isinstance(answer, (str, bytes, bytearray)):
        answer = json.loads(answer)

    return {"message": answer}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

# run the app with: python api.py
# go to http://127.0.0.1:8000/api/v1/sparrow-llm/docs to see the Swagger UI
