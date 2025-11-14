# ClariFi - Advanced Financial Analysis Platform 📈

**ClariFi** is a comprehensive financial analysis platform that combines machine learning, pattern recognition, real-time market data, and professional-grade investment intelligence. This notebook provides interactive commands to get you started with the platform quickly.

## 🚀 Quick Start

### Launch ClariFi (Recommended)

```warp-runnable-command
python3 run_clarifi.py
```

This command will:

- Check and install missing dependencies automatically
- Create virtual environment if needed
- Start the FastAPI backend server
- Open the web interface in your browser
- Access at: <http://localhost:8000>

### Check System Dependencies

```warp-runnable-command
python3 --version && pip --version
```

### Install Dependencies Manually

```warp-runnable-command
pip install -r requirements.txt
```

## 🏗️ Project Architecture

### View Project Structure

```warp-runnable-command
ls -la
```

### Core Modules Overview

```warp-runnable-command
find core/ -name "*.py" -exec basename {} \; | sort
```

### Documentation Available

```warp-runnable-command
ls -la docs/
```

## 📊 Analysis Features

### 1. AI-Powered Analysis with LLM Integration

**Analyze stocks with quantitative metrics and AI recommendations:**

```warp-runnable-command
python3 core/main.py ai AAPL MSFT --period 1y
```

**Quick analysis without LLM (quantitative only):**

```warp-runnable-command
python3 core/main.py ai TSLA --no-llm --period 6mo
```

**Show structured prompt for debugging:**

```warp-runnable-command
python3 core/main.py ai AAPL --show-prompt
```

### 2. Comprehensive Stock Analysis

**Full analysis with all features:**

```warp-runnable-command
python3 core/main.py analyze AAPL --period 1y
```

**Multiple stocks with specific features:**

```warp-runnable-command
python3 core/main.py analyze AAPL MSFT TSLA --no-seasonal --no-events
```

**Quick analysis (patterns + options + seasonal):**

```warp-runnable-command
python3 core/main.py quick PLTR --period 6mo
```

### 3. Options Analysis

**Black-Scholes options pricing and Greeks:**

```warp-runnable-command
python3 core/main.py options AAPL --strike 150 --expiry 2024-12-20
```

### 4. Seasonal Pattern Analysis

**Identify recurring seasonal patterns:**

```warp-runnable-command
python3 core/main.py seasonal MSFT --period 5y
```

### 5. Real-time Market Monitoring

**Start live monitoring for multiple tickers:**

```warp-runnable-command
python3 core/live_monitor.py --tickers AAPL,MSFT,TSLA
```

### 6. Stock Screening

**Screen stocks with custom criteria:**

```warp-runnable-command
python3 core/stock_screener.py --min-volume 1000000 --max-pe 20
```

## 💼 Portfolio Management

### Portfolio Analysis Tool

```warp-runnable-command
python3 PORTFOLIO_INFO_COMPLETE.py --help
```

### Analyze Portfolio

```warp-runnable-command
python3 PORTFOLIO_INFO_COMPLETE.py analyze "My Portfolio"
```

## 🌐 Web Platform

### Start Web Server

```warp-runnable-command
python3 backend/server.py
```

### Check Web Server Status

```warp-runnable-command
curl -s http://localhost:8000/health 2>/dev/null || echo "Server not running"
```

### View API Documentation

After starting the server, access:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## 🗄️ Database Operations

### Check Database

```warp-runnable-command
ls -la clarifi.db && echo "Database size: $(du -h clarifi.db | cut -f1)"
```

### View Database Schema (if sqlite3 available)

```warp-runnable-command
sqlite3 clarifi.db ".schema" 2>/dev/null || echo "SQLite3 not available or database not accessible"
```

## 📈 Data Management

### Check Data Directory

```warp-runnable-command
ls -la data/ 2>/dev/null || echo "No data directory found"
```

### Check Generated Graphs

```warp-runnable-command
ls -la graphs/ 2>/dev/null || echo "No graphs directory found"
```

### View Recent Data Files

```warp-runnable-command
find data/ -name "*.csv" -type f -mtime -7 2>/dev/null | head -10 || echo "No recent CSV files found"
```

## 🛠️ Development Tools

### Run Code Analysis

```warp-runnable-command
python3 cli_analysis.py --help
```

### Check Virtual Environment

```warp-runnable-command
if [ -d "venv" ]; then echo "✅ Virtual environment exists at: venv/"; else echo "❌ No virtual environment found"; fi
```

### Activate Virtual Environment

```warp-runnable-command
source venv/bin/activate && echo "✅ Virtual environment activated" && python --version
```

### Git Status

```warp-runnable-command
git status
```

### View Recent Git History

```warp-runnable-command
git log --oneline -5
```

## 🧪 Testing & Quality

### Run Tests (if available)

```warp-runnable-command
python -m pytest tests/ 2>/dev/null || echo "No tests found or pytest not installed"
```

### Check Code Style (if flake8 available)

```warp-runnable-command
flake8 core/ --max-line-length=100 --select=E,W 2>/dev/null || echo "flake8 not available"
```

## 🔧 System Diagnostics

### Check Required Python Modules

```warp-runnable-command
python3 -c "
import sys
required = ['yfinance', 'matplotlib', 'pandas', 'numpy', 'fastapi', 'uvicorn']
missing = []
for module in required:
    try:
        __import__(module)
        print(f'✅ {module}')
    except ImportError:
        print(f'❌ {module}')
        missing.append(module)
if missing:
    print(f'\\nMissing modules: {missing}')
else:
    print('\\n🎉 All core modules available!')
"
```

### Check Port Availability

```warp-runnable-command
lsof -i :8000 2>/dev/null && echo "⚠️ Port 8000 is in use" || echo "✅ Port 8000 is available"
```

### System Resource Check

```warp-runnable-command
echo "💻 System Info:"
echo "Memory: $(free -h 2>/dev/null | grep Mem || echo 'N/A (non-Linux)')"
echo "Disk: $(df -h . | tail -1 | awk '{print $4 " available"}')"
echo "Python: $(python3 --version)"
```

## 📚 Learning Resources

### View Available Documentation

```warp-runnable-command
find docs/ -name "*.md" -exec echo "📄 {}" \;
```

### Show Key Configuration Files

```warp-runnable-command
echo "📋 Configuration files:" && ls -1 *.py *.sh *.txt *.md | grep -E "\.(py|sh|txt|md)$" | head -10
```

### Environment Variables

```warp-runnable-command
if [ -f ".env" ]; then echo "✅ .env file exists"; cat .env | grep -v "^#" | grep -v "^$" | sed 's/=.*/=***/' || echo "Empty .env"; else echo "❌ No .env file found"; fi
```

## 🚀 Advanced Usage Examples

### Batch Analysis Multiple Portfolios

```warp-runnable-command
echo "Running batch analysis example..."
python3 core/main.py analyze AAPL GOOGL MSFT --period 6mo --no-events | head -20
```

### Export Analysis Results

```warp-runnable-command
mkdir -p exports && echo "📁 Created exports directory for analysis results"
```

### Performance Benchmark

```warp-runnable-command
echo "⏱️ Performance benchmark:"
time python3 core/main.py quick AAPL --period 3mo > /dev/null && echo "✅ Quick analysis completed"
```

## 💡 Tips & Best Practices

### Recommended First Steps

1. **Launch ClariFi**: `python3 run_clarifi.py`
2. **Test basic analysis**: `python3 core/main.py quick AAPL`
3. **Explore web interface**: Visit <http://localhost:8000>
4. **Try AI analysis**: `python3 core/main.py ai AAPL --period 6mo`

### For Development

1. **Activate virtual environment**: `source venv/bin/activate`
2. **Install in development mode**: `pip install -e .`
3. **Run tests**: `python -m pytest`
4. **Check documentation**: Browse `docs/` directory

### For Production

1. **Use environment variables**: Configure `.env` file
2. **Monitor resources**: Check system performance regularly
3. **Backup database**: Regular backups of `clarifi.db`
4. **Update dependencies**: Keep `requirements.txt` current

---

## 🏁 Getting Started Checklist

- [ ] Run `python3 run_clarifi.py` to launch the platform
- [ ] Test basic analysis with `python3 core/main.py quick AAPL`
- [ ] Access web interface at <http://localhost:8000>
- [ ] Try AI-powered analysis with `python3 core/main.py ai AAPL`
- [ ] Explore portfolio management features
- [ ] Review available documentation in `docs/`

**Happy analyzing! 📈✨**

---
*ClariFi - Making financial analysis clear, comprehensive, and actionable.*
