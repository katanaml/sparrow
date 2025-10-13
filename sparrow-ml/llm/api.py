from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from engine import run_from_api_engine, run_from_api_engine_instruction
import uvicorn
import warnings
from typing import Annotated, Optional
import json
import argparse
from dotenv import load_dotenv
from rich import print
from config_utils import get_config
import time
import tempfile
import os
import db_pool
from contextlib import asynccontextmanager


warnings.filterwarnings("ignore", category=DeprecationWarning)


# Load environment variables from .env file. Create .env file in the root directory if it doesn't exist
# If you are using Hugging Face GPU - set HF_TOKEN in .env file to the value of your Hugging Face API token
load_dotenv()


# Get config instance
config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for database connection pool management.
    This replaces the deprecated on_event handlers.
    """
    # Initialize resources on startup
    db_pool.initialize_connection_pool()
    print("Database connection pool initialized")

    yield  # Application runs here

    # Clean up resources on shutdown
    db_pool.close_connection_pool()
    print("Database connection pool closed")


app = FastAPI(lifespan=lifespan,
              title="Sparrow LLM API",
              description="Data processing with ML, LLM and Vision LLM",
              openapi_url="/api/v1/sparrow-llm/openapi.json",
              docs_url="/api/v1/sparrow-llm/docs")


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


def validate_key_from_config(config, sparrow_key):
    """
    Validates and increments usage count for a sparrow key using config.

    Args:
        config: Configuration object containing sparrow keys
        sparrow_key (str): The key to validate (must not be None or empty)

    Returns:
        bool: True if key is valid and was successfully incremented

    Raises:
        HTTPException: If key is invalid, disabled, or exceeded usage limit
    """
    # Get all Sparrow keys
    sparrow_keys = config.get_sparrow_keys()

    # Validate and log usage
    key_found = False
    for key_name, data in sparrow_keys.items():
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
            config.update_key_usage(key_name, usage_count + 1)
            return True

    if not key_found:
        raise HTTPException(status_code=403, detail="Protected access. Pipeline not allowed.")

    return False


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
        instruction: Annotated[Optional[bool], Form()] = False,
        validation: Annotated[Optional[bool], Form()] = False,
        precision: Annotated[Optional[bool], Form()] = False,
        page_type: Annotated[Optional[str], Form()] = None,
        debug_dir: Annotated[Optional[str], Form()] = None,
        debug: Annotated[Optional[bool], Form()] = False,
        sparrow_key: Annotated[Optional[str], Form()] = None,
        client_ip: Annotated[Optional[str], Form()] = "127.0.0.1",  # Default to localhost
        country: Annotated[Optional[str], Form()] = "Unknown",      # Default to Unknown
        file: UploadFile = File(None)
        ):
    try:
        processed_crop_size = parse_optional_int(crop_size)
    except ValueError:
        raise HTTPException(status_code=422, detail="crop_size must be a valid integer or empty")

    protected_access = config.get_bool('settings', 'protected_access', False)
    if protected_access:
        # Check if key is provided - common for both database and config validation
        if not sparrow_key:
            raise HTTPException(
                status_code=403,
                detail="Sparrow key is required for protected access."
            )

        # Check if database is enabled
        use_database = config.get_bool('settings', 'use_database', False)

        if use_database:
            # Use the database function to validate and increment the key
            is_valid = db_pool.validate_and_increment_key(sparrow_key)

            if not is_valid:
                raise HTTPException(
                    status_code=403,
                    detail="Invalid, disabled, or usage limit exceeded for key."
                )
        else:
            # Use the config-based validation
            validate_key_from_config(config, sparrow_key)

    options_arr = [param.strip() for param in options.split(',')] if options is not None else None
    page_type_arr = [param.strip() for param in page_type.split(',')] if options is not None and page_type else None

    try:
        # Calculate page count if file is a PDF
        page_count = 1  # Default to 1 if not a PDF or unable to determine

        if file and file.filename and file.filename.lower().endswith('.pdf'):
            # Create a temporary file to analyze
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            try:
                # Read the file content into memory
                file_content = await file.read()
                temp_file.write(file_content)
                temp_file.flush()

                # Rewind the file for the API
                await file.seek(0)

                # Use PyPDF2 to get the page count
                import pypdf
                with open(temp_file.name, 'rb') as pdf_file:
                    pdf_reader = pypdf.PdfReader(pdf_file)
                    page_count = len(pdf_reader.pages)
            except Exception as e:
                print(f"Error determining PDF page count: {str(e)}")
                # Continue with default page_count=1
            finally:
                # Close and remove the temporary file
                temp_file.close()
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

        # Extract the model name from options_arr (it's the second element)
        model_name = None
        if options_arr and len(options_arr) > 1:
            model_name = options_arr[1]

        # Log the start of inference processing and get the ID
        log_id = db_pool.log_inference_start(
            client_ip=client_ip,
            country_name=country,
            sparrow_key=sparrow_key,
            page_count=page_count,
            model_name=model_name,
            inference_type='DATA_EXTRACTION',
            source='UI'
        )

        # Start timing
        start_time = time.time()

        # Call the engine to process the request
        answer = await run_from_api_engine(pipeline, query, options_arr, processed_crop_size, instruction, validation,
                                           precision, page_type_arr, file, debug_dir, debug)

        # Calculate duration
        duration = time.time() - start_time

        # Update the record with actual duration
        db_pool.update_inference_duration(log_id, duration)
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

    return answer


@app.post("/api/v1/sparrow-llm/instruction-inference", tags=["LLM Inference"])
async def instruction_inference(
        query: Annotated[str, Form()],
        pipeline: Annotated[str, Form()],
        options: Annotated[Optional[str], Form()] = None,
        debug_dir: Annotated[Optional[str], Form()] = None,
        debug: Annotated[Optional[bool], Form()] = False,
        sparrow_key: Annotated[Optional[str], Form()] = None,
        client_ip: Annotated[Optional[str], Form()] = "127.0.0.1",  # Default to localhost
        country: Annotated[Optional[str], Form()] = "Unknown"      # Default to Unknown
        ):
    """
    Process instruction-only LLM inference without document upload.
    """
    try:
        # Handle protected access checking
        protected_access = config.get_bool('settings', 'protected_access', False)
        if protected_access:
            # Check if key is provided - common for both database and config validation
            if not sparrow_key:
                raise HTTPException(
                    status_code=403,
                    detail="Sparrow key is required for protected access."
                )

            # Check if database is enabled
            use_database = config.get_bool('settings', 'use_database', False)

            if use_database:
                # Use the database function to validate and increment the key
                is_valid = db_pool.validate_and_increment_key(sparrow_key)

                if not is_valid:
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid, disabled, or usage limit exceeded for key."
                    )
            else:
                # Use the config-based validation
                validate_key_from_config(config, sparrow_key)

        options_arr = [param.strip() for param in options.split(',')] if options is not None else None

        # Extract the model name from options_arr (it's the second element)
        model_name = None
        if options_arr and len(options_arr) > 1:
            model_name = options_arr[1]

        # Log the start of inference processing and get the ID
        log_id = db_pool.log_inference_start(
            client_ip=client_ip,
            country_name=country,
            sparrow_key=sparrow_key,
            page_count=1,  # Text inference is counted as one page
            model_name=model_name,
            inference_type='INSTRUCTION_PROCESSING',
            source='UI'
        )

        # Start timing
        start_time = time.time()

        # Call the engine to process the instruction-only request
        answer = await run_from_api_engine_instruction(
            pipeline, query, options_arr, debug_dir, debug
        )

        # Calculate duration
        duration = time.time() - start_time

        # Update the record with actual duration
        db_pool.update_inference_duration(log_id, duration)
    except ValueError as e:
        raise HTTPException(status_code=418, detail=str(e))

    try:
        if isinstance(answer, (str, bytes, bytearray)):
            answer = json.loads(answer)
    except json.JSONDecodeError as e:
        # Keep the text answer as is if it's not valid JSON
        pass

    if debug:
        print(f"\nSparrow Response:\n")
        print(answer)

    return answer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run FastAPI App")
    parser.add_argument("-p", "--port", type=int, default=8002, help="Port to run the FastAPI app on")
    args = parser.parse_args()

    uvicorn.run("api:app", host="0.0.0.0", port=args.port, reload=True)

# run the app with: python api.py --port 8000
# go to http://127.0.0.1:8000/api/v1/sparrow-llm/docs to see the Swagger UI
