from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from engine import run_from_api_engine
import uvicorn
import warnings
from typing import Annotated
import json
import argparse
from dotenv import load_dotenv
import box
import yaml
import os
from rich import print


warnings.filterwarnings("ignore", category=DeprecationWarning)


# Load environment variables from .env file. Create .env file in the root directory if it doesn't exist
# If you are using Hugging Face GPU - set HF_TOKEN in .env file to the value of your Hugging Face API token
load_dotenv()

# Import config vars
with open('config.yml', 'r', encoding='utf8') as ymlfile:
    cfg = box.Box(yaml.safe_load(ymlfile))

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
        query: Annotated[str, Form()],
        agent: Annotated[str, Form()],
        options: Annotated[str, Form()] = None,
        debug_dir: Annotated[str, Form()] = None,
        debug: Annotated[bool, Form()] = False,
        sparrow_key: Annotated[str, Form()] = None,
        file: UploadFile = File(None)
        ):

    protected_access = cfg.PROTECTED_ACCESS
    if protected_access:
        # Retrieve all environment variables that start with 'SPARROW_KEY_'
        sparrow_keys = {key: value for key, value in os.environ.items() if key.startswith('SPARROW_KEY_')}

        # Check if the provided sparrow_key matches any of the environment variables
        if sparrow_key not in sparrow_keys.values():
            raise HTTPException(status_code=403, detail="Protected access. Agent not allowed.")

    options_arr = [param.strip() for param in options.split(',')] if options is not None else None

    try:
        answer = await run_from_api_engine(agent, query, options_arr, file, debug_dir, debug)
    except ValueError as e:
        raise HTTPException(status_code=418, detail=str(e))

    try:
        if isinstance(answer, (str, bytes, bytearray)):
            answer = json.loads(answer)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=418, detail=answer)

    if debug:
        print(f"\nJSON response:\n")
        print(answer)

    return {"message": answer}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FastAPI App")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to run the FastAPI app on")
    args = parser.parse_args()

    uvicorn.run("api:app", host="0.0.0.0", port=args.port, reload=True)

# run the app with: python api.py --port 8000
# go to http://127.0.0.1:8000/api/v1/sparrow-llm/docs to see the Swagger UI
