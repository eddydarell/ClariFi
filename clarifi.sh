#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_ENV="$VENV_DIR/bin/python"
REQS_FILE="$SCRIPT_DIR/requirements.txt"

init() {
    echo "ClariFi: Clarify your Finances"
    echo "================================="

    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: python3 not found. Install Python 3 first."
        exit 1
    fi

    echo "Setting up virtual environment..."
    if [ ! -f "$PYTHON_ENV" ]; then
        echo "Creating virtual environment at $VENV_DIR"
        if ! python3 -m venv "$VENV_DIR"; then
            echo "Error: Failed to create virtual environment"
            exit 1
        fi
    else
        echo "Virtual environment already exists at $VENV_DIR"
    fi

    echo "Upgrading pip..."
    if ! "$PYTHON_ENV" -m pip install --upgrade pip; then
        echo "Error: Failed to upgrade pip"
        exit 1
    fi

    echo "Installing dependencies from requirements.txt..."
    if ! "$PYTHON_ENV" -m pip install -r "$REQS_FILE"; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi

    echo ""
    echo "Setup complete!"
    echo "Try it out: ./clarifi.sh analyze AAPL --period 10y"
}

if [ "${1:-}" = "init" ]; then
    init
    exit 0
fi

if [ ! -f "$PYTHON_ENV" ]; then
    echo "Warning: virtual environment not found. Run './clarifi.sh init' to install dependencies." >&2
    PYTHON_ENV="python3"
fi

cd "$SCRIPT_DIR" || exit 1
exec "$PYTHON_ENV" clarifi_cli.py "$@"
