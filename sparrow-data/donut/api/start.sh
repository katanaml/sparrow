#!/bin/bash

# Check if the RUN_LOCALLY environment variable is set
if [[ $RUN_LOCALLY = "true" ]]; then
    # Source the script that sets environment variables
    source ./set_env_vars.sh
fi

# Then start FastAPI application, set to 0.0.0.0 to allow external connections from Docker container.
# Remove --reload for production.
uvicorn endpoints:app --host 127.0.0.1 --port 8000 --reload
