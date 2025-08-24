#!/bin/bash

# ClariFi Virtual Environment Setup
# This script creates and configures the virtual environment for ClariFi

echo "🔧 Setting up ClariFi Virtual Environment"

# Check if we're in the right directory
if [ ! -d "clarifi_engine" ]; then
    echo "❌ Error: clarifi_engine directory not found"
    echo "Please run this script from the ClariFi root directory"
    exit 1
fi

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "🗑️  Removing existing virtual environment..."
    rm -rf venv
fi

# Create new virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment manually, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start ClariFi, run:"
echo "  ./start_clarifi.sh"
