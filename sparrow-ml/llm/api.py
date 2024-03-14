from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from engine import run_from_api_engine
from ingest import run_from_api_ingest
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


@app.get("/")
def root():
    return {"message": "Sparrow LLM API"}


@app.post("/api/v1/sparrow-llm/inference", tags=["LLM Inference"])
async def inference(
        fields: Annotated[str, Form()],
        types: Annotated[str, Form()],
        agent: Annotated[str, Form()],
        index_name: Annotated[str, Form()] = None,
        file: UploadFile = File(None)
        ):
    query = 'retrieve ' + fields
    query_types = types

    query_inputs_arr = [param.strip() for param in fields.split(',')]
    query_types_arr = [param.strip() for param in query_types.split(',')]

    try:
        answer = await run_from_api_engine(agent, query_inputs_arr, query_types_arr, query, index_name, file,
                                           False)
    except ValueError as e:
        raise HTTPException(status_code=418, detail=str(e))

    if isinstance(answer, (str, bytes, bytearray)):
        answer = json.loads(answer)

    return {"message": answer}


@app.post("/api/v1/sparrow-llm/ingest", tags=["LLM Ingest"])
async def ingest(
        agent: Annotated[str, Form()],
        index_name: Annotated[str, Form()],
        file: UploadFile = File()
        ):
    try:
        answer = await run_from_api_ingest(agent, index_name, file, False)
    except ValueError as e:
        raise HTTPException(status_code=418, detail=str(e))

    if isinstance(answer, (str, bytes, bytearray)):
        answer = json.loads(answer)

    return {"message": answer}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

# run the app with: python api.py
# go to http://127.0.0.1:8000/api/v1/sparrow-llm/docs to see the Swagger UI
