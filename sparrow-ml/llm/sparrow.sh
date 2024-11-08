#!/bin/bash

command -v python >/dev/null 2>&1 || { echo >&2 "Python is required but it's not installed. Aborting."; exit 1; }

# Check Python version
PYTHON_VERSION=$(python --version 2>&1) # Capture both stdout and stderr
echo "Detected Python version: $PYTHON_VERSION"
if [[ ! "$PYTHON_VERSION" == *"3.10.4"* ]]; then
  echo "Python version 3.10.4 is required. Current version is $PYTHON_VERSION. Aborting."
  exit 1
fi

PYTHON_SCRIPT_PATH="engine.py"

if [ "$1" == "assistant" ]; then
    PYTHON_SCRIPT_PATH="assistant.py"
    shift # Shift the arguments to exclude the first one
fi

python "${PYTHON_SCRIPT_PATH}" "$@"

# make script executable with: chmod +x sparrow.sh