#!/bin/bash

# Check if the RUN_LOCALLY environment variable is set
if [[ $RUN_LOCALLY = "true" ]]; then
    # Source the script that sets environment variables
    source ./set_env_vars.sh
fi

# Then start FastAPI application
uvicorn endpoints:app --host 0.0.0.0 --port 7860
