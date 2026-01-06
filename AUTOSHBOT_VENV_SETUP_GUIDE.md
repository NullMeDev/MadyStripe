# AutoshBot Virtual Environment Setup Guide

**For Systems with Externally-Managed Python (PEP 668)**

This guide is specifically for systems like Pop!_OS, Ubuntu 23.04+, Debian 12+, and other distributions that enforce PEP 668 and require virtual environments for Python package installation.

---

## Quick Start

```bash
# Navigate to project directory
cd /home/null/Desktop/MadyStripe

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install aiohttp aiogram sqlalchemy python-dotenv requests

# Run the bot
cd AutoshBotSRC/AutoshBotSRC
python bot.py
```

---

## Detailed Setup Instructions

### Step 1: Create Virtual Environment

```bash
cd /home/null/Desktop/MadyStripe
python3 -m venv venv
```

**What this does:**
- Creates a `venv` directory in your project
- Isolates Python packages from system Python
- Complies with PEP 668 requirements

**Expected output:**
```
(Creates venv directory with bin/, lib/, include/ subdirectories)
```

---

### Step 2: Activate Virtual Environment

**On Linux/Mac:**
```bash
source venv/bin/activate
```

**On Windows:**
```cmd
venv\Scripts\activate
```

**You'll know it's activated when you see:**
```bash
(venv) null@pop-os:~/Desktop/MadyStripe$
```

---

### Step 3: Install Dependencies

**Option A: Install from requirements.txt (Recommended)**
```bash
pip install -r AutoshBotSRC/AutoshBotSRC/requirements.txt
```

**Option B: Install manually**
```bash
pip install aiohttp aiogram sqlalchemy python-dotenv requests
```

**Expected output:**
```
Collecting aiohttp
  Downloading aiohttp-3.9.1-cp312-cp312-linux_x86_64.whl
...
Successfully installed aiohttp-3.9.1 aiogram-3.3.0 sqlalchemy-2.0.25 ...
```

---

### Step 4: Configure Bot

**Edit bot.py:**
```bash
nano AutoshBotSRC/AutoshBotSRC/bot.py
```

**Add your Telegram bot token:**
```python
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with actual token
```

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

---

### Step 5: Run the Bot

**With virtual environment activated:**
```bash
cd AutoshBotSRC/AutoshBotSRC
python bot.py
```

**Or use full path without activation:**
```bash
/home/null/Desktop/MadyStripe/venv/bin/python AutoshBotSRC/AutoshBotSRC/bot.py
```

---

## Running Tests

### Test 1: Simple Validation

```bash
# Activate venv
source venv/bin/activate

# Run simple test
python test_autoshbot_simple.py
```

### Test 2: Comprehensive Testing

```bash
# Activate venv
source venv/bin/activate

# Run comprehensive test
python test_autoshbot_comprehensive.py
```

### Test 3: Check Results

```bash
# View test results
cat test_results_comprehensive.json
```

---

## Common Commands

### Activate Virtual Environment
```bash
source venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

### Check Installed Packages
```bash
pip list
```

### Update a Package
```bash
pip install --upgrade package_name
```

### Install New Package
```bash
pip install package_name
```

---

## Troubleshooting

### Issue 1: "externally-managed-environment" Error

**Problem:**
```
error: externally-managed-environment
```

**Solution:**
You forgot to activate the virtual environment. Run:
```bash
source venv/bin/activate
```

---

### Issue 2: Virtual Environment Not Found

**Problem:**
```
bash: venv/bin/activate: No such file or directory
```

**Solution:**
Create the virtual environment first:
```bash
python3 -m venv venv
```

---

### Issue 3: Permission Denied

**Problem:**
```
Permission denied: 'venv/bin/python'
```

**Solution:**
Make sure you have write permissions:
```bash
chmod +x venv/bin/python
```

---

### Issue 4: Module Not Found

**Problem:**
```
ModuleNotFoundError: No module named 'aiohttp'
```

**Solution:**
Install dependencies in the virtual environment:
```bash
source venv/bin/activate
pip install -r AutoshBotSRC/AutoshBotSRC/requirements.txt
```

---

### Issue 5: Wrong Python Version

**Problem:**
```
Python 3.8 required, but 3.12 found
```

**Solution:**
Specify Python version when creating venv:
```bash
python3.8 -m venv venv
```

---

## Virtual Environment Best Practices

### 1. Always Activate Before Working

```bash
# Start of every session
cd /home/null/Desktop/MadyStripe
source venv/bin/activate
```

### 2. Keep Requirements Updated

```bash
# After installing new packages
pip freeze > requirements.txt
```

### 3. Don't Commit venv Directory

Add to `.gitignore`:
```
venv/
__pycache__/
*.pyc
*.db
```

### 4. Use Separate Venvs for Different Projects

```bash
# Project 1
cd /path/to/project1
python3 -m venv venv

# Project 2
cd /path/to/project2
python3 -m venv venv
```

---

## Alternative: Using pipx

If you prefer not to use virtual environments manually, you can use `pipx`:

### Install pipx

```bash
sudo apt install pipx
pipx ensurepath
```

### Install Bot with pipx

```bash
pipx install /path/to/AutoshBotSRC
```

**Note:** This is less flexible for development but good for production deployment.

---

## Systemd Service (Production Deployment)

### Create Service File

```bash
sudo nano /etc/systemd/system/autoshbot.service
```

### Service Configuration

```ini
[Unit]
Description=AutoshBot Telegram Bot
After=network.target

[Service]
Type=simple
User=null
WorkingDirectory=/home/null/Desktop/MadyStripe/AutoshBotSRC/AutoshBotSRC
ExecStart=/home/null/Desktop/MadyStripe/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable autoshbot

# Start service
sudo systemctl start autoshbot

# Check status
sudo systemctl status autoshbot

# View logs
sudo journalctl -u autoshbot -f
```

---

## Docker Alternative (Advanced)

If you prefer containerization:

### Create Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY AutoshBotSRC/AutoshBotSRC/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY AutoshBotSRC/AutoshBotSRC/ .

CMD ["python", "bot.py"]
```

### Build and Run

```bash
# Build image
docker build -t autoshbot .

# Run container
docker run -d --name autoshbot --restart unless-stopped autoshbot

# View logs
docker logs -f autoshbot
```

---

## Environment Variables (Recommended for Production)

### Create .env File

```bash
nano AutoshBotSRC/AutoshBotSRC/.env
```

### Add Configuration

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite:///cocobot.db
LOG_LEVEL=INFO
```

### Update bot.py to Use .env

```python
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id) for id in os.getenv('ADMIN_IDS', '').split(',')]
```

---

## Quick Reference Card

```bash
# Setup (one-time)
python3 -m venv venv
source venv/bin/activate
pip install -r AutoshBotSRC/AutoshBotSRC/requirements.txt

# Daily use
source venv/bin/activate
cd AutoshBotSRC/AutoshBotSRC
python bot.py

# Testing
source venv/bin/activate
python test_autoshbot_comprehensive.py

# Cleanup
deactivate
```

---

## Summary

**Why Virtual Environments?**
- ✅ Complies with PEP 668
- ✅ Isolates project dependencies
- ✅ Prevents system Python conflicts
- ✅ Easy to reproduce environment
- ✅ Safe to experiment

**Key Commands:**
- Create: `python3 -m venv venv`
- Activate: `source venv/bin/activate`
- Install: `pip install package_name`
- Deactivate: `deactivate`

**Remember:**
Always activate the virtual environment before running the bot or installing packages!

---

**Last Updated:** January 2025  
**Compatible With:** Pop!_OS 22.04+, Ubuntu 23.04+, Debian 12+, and other PEP 668-compliant systems
