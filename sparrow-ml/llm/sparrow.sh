#!/bin/bash

command -v python3 >/dev/null 2>&1 || { echo >&2 "Python 3 is required but it's not installed. Aborting."; exit 1; }

PYTHON_SCRIPT_PATH="engine.py"

# Check if the "ingest" flag is passed
if [ "$1" == "ingest" ]; then
    PYTHON_SCRIPT_PATH="ingest.py"
    shift # Shift the arguments to exclude the first one
fi

if [ "$1" == "assistant" ]; then
    PYTHON_SCRIPT_PATH="assistant.py"
    shift # Shift the arguments to exclude the first one
fi

python3 "${PYTHON_SCRIPT_PATH}" "$@"

# make script executable with: chmod +x sparrow.sh