#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
PYTHON_ENV="$VENV_DIR/bin/python"

if [ ! -f "$PYTHON_ENV" ]; then
    PYTHON_ENV="python3"
fi

cd "$SCRIPT_DIR" || exit 1
"$PYTHON_ENV" clarifi_cli.py "$@"
