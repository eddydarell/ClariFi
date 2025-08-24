#!/usr/bin/env python3
"""
ClariFi Application Launcher
Run this script to start the ClariFi application
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("🚀 Starting ClariFi - Clarify your Finances")

    # Get the current directory
    script_dir = Path(__file__).parent

    # Check if we're in the right directory
    if not (script_dir / "clarifi_engine").exists():
        print("❌ Error: clarifi_engine directory not found")
        print("Please run this script from the ClariFi root directory")
        sys.exit(1)

    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        import yfinance
        print("✅ Dependencies check passed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing requirements...")

        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

        if not in_venv:
            print("⚠️  Not in virtual environment. Creating one...")
            venv_path = script_dir / "venv"
            if not venv_path.exists():
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
                print("✅ Virtual environment created")

            # Get the python executable from the venv
            if os.name == 'nt':  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:  # Unix/Linux/macOS
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"

            # Install requirements using venv pip
            subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"])
            print("✅ Requirements installed in virtual environment")
            print("🔄 Please restart the script to use the virtual environment")
            print("   Run: source venv/bin/activate && python3 run_clarifi.py")
            sys.exit(0)
        else:
            # We're already in a venv, try to install requirements
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Requirements installed")

    # Initialize database
    print("🗄️  Initializing database...")
    try:
        from database.models import DatabaseManager
        db = DatabaseManager()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

    # Start the server
    print("🌐 Starting web server...")
    server_file = script_dir / "backend" / "server.py"

    if not server_file.exists():
        print("❌ Error: server.py not found")
        sys.exit(1)

    # Change to backend directory and start server
    os.chdir(script_dir / "backend")


    try:
        # Start server in background
        print("🎯 Server starting at http://localhost:8181")
        print("📊 Opening ClariFi in your browser...")

        # Give server a moment to start
        time.sleep(2)

        # Open browser
        webbrowser.open("http://localhost:8181")

        # Start server (this will block)
        subprocess.run([sys.executable, "server.py", "--port", "8181"])

    except KeyboardInterrupt:
        print("\n👋 ClariFi server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
