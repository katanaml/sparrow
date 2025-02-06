from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from engine import run_from_api_engine
import uvicorn
import warnings
from typing import Annotated, Optional
import json
import argparse
from dotenv import load_dotenv
import box
import yaml
from rich import print


warnings.filterwarnings("ignore", category=DeprecationWarning)


# Load environment variables from .env file. Create .env file in the root directory if it doesn't exist
# If you are using Hugging Face GPU - set HF_TOKEN in .env file to the value of your Hugging Face API token
load_dotenv()


# Function to load configuration
def load_config(file_path='config.yml'):
    with open(file_path, 'r', encoding='utf8') as ymlfile:
        return box.Box(yaml.safe_load(ymlfile))

# Function to save configuration
def save_config(cfg, file_path='config.yml'):
    with open(file_path, 'w', encoding='utf8') as ymlfile:
        yaml.safe_dump(cfg.to_dict(), ymlfile)

# Load configuration
config_path = 'config.yml'
cfg = load_config(config_path)


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


def parse_optional_int(value: Optional[str]) -> Optional[int]:
    """Handle empty strings and None values for integer fields."""
    if value is None or value.strip() == "":
        return None
    try:
        return int(value)
    except ValueError:
        raise ValueError("Invalid integer value provided")


@app.post("/api/v1/sparrow-llm/inference", tags=["LLM Inference"])
async def inference(
        query: Annotated[str, Form()],
        pipeline: Annotated[str, Form()],
        options: Annotated[Optional[str], Form()] = None,
        crop_size: Annotated[Optional[str], Form()] = None,
        page_type: Annotated[Optional[str], Form()] = None,
        debug_dir: Annotated[Optional[str], Form()] = None,
        debug: Annotated[Optional[bool], Form()] = False,
        sparrow_key: Annotated[Optional[str], Form()] = None,
        file: UploadFile = File(None)
        ):
    try:
        processed_crop_size = parse_optional_int(crop_size)
    except ValueError:
        raise HTTPException(status_code=422, detail="crop_size must be a valid integer or empty")

    protected_access = cfg.PROTECTED_ACCESS
    if protected_access:
        # Retrieve all sparrow keys from the config file
        sparrow_keys = cfg.get('SPARROW_KEYS', {})

        # Validate and log usage
        key_found = False
        for key, data in sparrow_keys.items():
            if data['value'] == sparrow_key:
                key_found = True

                # Check if usage is within the allowed limit
                usage_count = data.get('usage_count', 0)
                usage_limit = data.get('usage_limit', float('inf'))  # Default to no limit if not set

                if usage_count >= usage_limit:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Usage limit exceeded for key '{sparrow_key}'. Allowed limit: {usage_limit}."
                    )

                # Increment the usage count
                data['usage_count'] = usage_count + 1
                break

        if not key_found:
            raise HTTPException(status_code=403, detail="Protected access. Pipeline not allowed.")

        # Save updated configuration back to the file
        save_config(cfg, config_path)

    options_arr = [param.strip() for param in options.split(',')] if options is not None else None
    page_type_arr = [param.strip() for param in page_type.split(',')] if options is not None else None

    try:
        answer = await run_from_api_engine(pipeline, query, options_arr, processed_crop_size, page_type_arr,
                                           file, debug_dir, debug)
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
    parser.add_argument("-p", "--port", type=int, default=8002, help="Port to run the FastAPI app on")
    args = parser.parse_args()

    uvicorn.run("api:app", host="0.0.0.0", port=args.port, reload=True)

# run the app with: python api.py --port 8000
# go to http://127.0.0.1:8000/api/v1/sparrow-llm/docs to see the Swagger UI
