#!/bin/bash

# ClariFi Application Launcher
# Make sure you're in the ClariFi directory before running this script

echo "🚀 Starting ClariFi - Clarify your Finances"

# Check if we're in the right directory
if [ ! -d "core" ]; then
    echo "❌ Error: core directory not found"
    echo "Please run this script from the ClariFi root directory"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install requirements if needed
echo "📦 Installing/updating requirements..."
pip install -r requirements.txt


# Build the frontend (Vue + Vuetify + Vite)
echo "🛠️  Building ClariFi frontend (Vite)..."
cd frontend/ClariFi
npm install
npm run build
cd ../..

# Make run script executable
chmod +x run_clarifi.py

# Run the application
echo "🎯 Launching ClariFi..."
python3 run_clarifi.py
