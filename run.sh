#!/bin/bash

# ClariFi: Clarify your Finances
# Advanced Market Intelligence & Pattern Analysis Tool
# Wrapper script for the Python financial analysis tool with venv setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="/Users/eddyntambwe/Dev/scripts-project"
VENV_DIR="$PROJECT_ROOT/venv"
PYTHON_ENV="$VENV_DIR/bin/python"
PIP_ENV="$VENV_DIR/bin/pip"

echo "🚀 ClariFi: Clarify your Finances"
echo "================================="

# Function to create and setup virtual environment
setup_venv() {
    echo "🔧 Setting up virtual environment..."

    # Create venv if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "📦 Creating virtual environment at $VENV_DIR"
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to create virtual environment"
            exit 1
        fi
    fi

    # Upgrade pip
    echo "⬆️ Upgrading pip..."
    "$PIP_ENV" install --upgrade pip

    # Install requirements
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "📚 Installing requirements..."
        "$PIP_ENV" install -r "$SCRIPT_DIR/requirements.txt"
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install requirements"
            exit 1
        fi
    else
        echo "⚠️ No requirements.txt found"
    fi

    echo "✅ Virtual environment setup complete!"
}

# Check if we need to initialize (--init flag or missing venv)
if [ "$1" = "--init" ] || [ "$1" = "init" ]; then
    setup_venv
    echo "🎉 Initialization complete! You can now run analysis commands."
    exit 0
fi

# Check if Python environment exists
if [ ! -f "$PYTHON_ENV" ]; then
    echo "❌ Python environment not found at: $PYTHON_ENV"
    echo "💡 Run './run.sh init' to set up the virtual environment"
    exit 1
fi

# Check if requirements are installed by testing a key import
if ! "$PYTHON_ENV" -c "import yfinance, pandas, matplotlib" >/dev/null 2>&1; then
    echo "⚠️ Missing dependencies detected. Installing requirements..."
    setup_venv
fi

# Change to the script directory
cd "$SCRIPT_DIR" || exit 1

# Run the Python script with all arguments
"$PYTHON_ENV" main.py "$@"
