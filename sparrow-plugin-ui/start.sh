#!/bin/bash

# Check if the RUN_LOCALLY environment variable is set
if [[ $RUN_LOCALLY = "true" ]]; then
    # Source the script that sets environment variables
    source ./set_env_vars.sh
fi

# Then start Streamlit application, set to 0.0.0.0 to allow external connections from Docker container
streamlit run main.py --server.port=7860 --server.address=127.0.0.1