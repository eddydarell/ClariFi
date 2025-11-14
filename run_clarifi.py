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

# Initialize colorama for cross-platform colored output
try:
    import colorama
    colorama.init(autoreset=True)
    from colorama import Fore, Back, Style
    HAS_COLORAMA = True
except ImportError:
    # Fallback if colorama not available
    class Fore:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
        MAGENTA = ''
        CYAN = ''
        WHITE = ''
        BLACK = ''
    class Back:
        GREEN = ''
        RED = ''
        YELLOW = ''
        BLUE = ''
    class Style:
        BRIGHT = ''
        DIM = ''
        NORMAL = ''
    HAS_COLORAMA = False

def main():
    print(f"{Fore.CYAN}Starting ClariFi - Clarify your Finances{Style.RESET_ALL}")

    # Get the current directory
    script_dir = Path(__file__).parent

    # Check if we're in the right directory
    if not (script_dir / "core").exists():
        print(f"{Fore.RED}Error: core directory not found{Style.RESET_ALL}")
        print("Please run this script from the ClariFi root directory")
        sys.exit(1)

    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        import yfinance
        print(f"{Fore.GREEN}Dependencies check passed{Style.RESET_ALL}")
    except ImportError as e:
        print(f"{Fore.RED}Missing dependency: {e}{Style.RESET_ALL}")
        print("Installing requirements...")

        # Check if we're in a virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

        if not in_venv:
            print(f"{Fore.YELLOW}Not in virtual environment. Creating one...{Style.RESET_ALL}")
            venv_path = script_dir / "venv"
            if not venv_path.exists():
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)])
                print(f"{Fore.GREEN}Virtual environment created{Style.RESET_ALL}")

            # Get the python executable from the venv
            if os.name == 'nt':  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
                pip_exe = venv_path / "Scripts" / "pip.exe"
            else:  # Unix/Linux/macOS
                python_exe = venv_path / "bin" / "python"
                pip_exe = venv_path / "bin" / "pip"

            # Install requirements using venv pip
            subprocess.run([str(pip_exe), "install", "-r", "requirements.txt"])
            print(f"{Fore.GREEN}Requirements installed in virtual environment{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Please restart the script to use the virtual environment{Style.RESET_ALL}")
            print("   Run: source venv/bin/activate && python3 run_clarifi.py")
            sys.exit(0)
        else:
            # We're already in a venv, try to install requirements
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print(f"{Fore.GREEN}Requirements installed{Style.RESET_ALL}")

    # Initialize database
    print(f"{Fore.BLUE}Initializing database...{Style.RESET_ALL}")
    try:
        from database.models import DatabaseManager
        db = DatabaseManager()
        print(f"{Fore.GREEN}Database initialized{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Database initialization failed: {e}{Style.RESET_ALL}")
        sys.exit(1)

    # Start the server
    print(f"{Fore.BLUE}Starting web server...{Style.RESET_ALL}")
    server_file = script_dir / "backend" / "server.py"

    if not server_file.exists():
        print(f"{Fore.RED}Error: server.py not found{Style.RESET_ALL}")
        sys.exit(1)

    # Change to backend directory and start server
    os.chdir(script_dir / "backend")


    try:
        # Start server in background
        print(f"{Fore.GREEN}Server starting at http://localhost:8181{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Opening ClariFi in your browser...{Style.RESET_ALL}")

        # Give server a moment to start
        time.sleep(2)

        # Open browser
        webbrowser.open("http://localhost:8181")

        # Start server (this will block)
        subprocess.run([sys.executable, "server.py", "--port", "8181"])

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}ClariFi server stopped{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error starting server: {e}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
