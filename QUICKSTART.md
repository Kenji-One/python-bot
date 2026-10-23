# Quick Start Guide - PowerPlay Lead Claimer Bot

Get up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
cd powerplay-lead-claimer

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

## Step 2: Configure Credentials

```bash
# Copy example config
cp .env.example .env

# Edit with your credentials
nano .env
```

**Minimum required settings:**
```env
POWERPLAY_USERNAME=your_email@example.com
POWERPLAY_PASSWORD=your_password_here
HEADLESS=false  # Keep false for first run to watch it work
```

## Step 3: Run the Bot

```bash
python main.py
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║           PowerPlay Lead Claimer Bot v1.0                    ║
╚══════════════════════════════════════════════════════════════╝

2024-03-15 10:30:00 - INFO - Starting PowerPlay Lead Claimer Bot...
2024-03-15 10:30:01 - INFO - Initializing browser...
2024-03-15 10:30:03 - INFO - Navigating to login page...
2024-03-15 10:30:05 - INFO - ✓ Login successful!
2024-03-15 10:30:06 - INFO - 🔍 Starting lead monitoring loop...
```

## Step 4: Test and Verify

1. Watch the browser window (since HEADLESS=false)
2. Verify it successfully logs in
3. Observe the monitoring loop
4. Wait for a lead to appear and watch it get claimed automatically

## Step 5: Run in Background (Production)

Once verified:

```bash
# Edit .env
nano .env
```

Change:
```env
HEADLESS=true
```

Run again:
```bash
python main.py
```

## Stopping the Bot

Press `Ctrl+C` to stop gracefully.

## Next Steps

- Read [README.md](README.md) for full documentation
- Check logs in `logs/` directory
- Review screenshots in `screenshots/` directory
- Customize settings in `.env` as needed

## Common Commands

```bash
# View logs
tail -f logs/bot_*.log

# List screenshots
ls -lh screenshots/

# Reactivate virtual environment (after closing terminal)
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade
```

## Troubleshooting

**"Module not found" error:**
```bash
source venv/bin/activate  # Make sure venv is activated
pip install -r requirements.txt
```

**"playwright not found" error:**
```bash
playwright install chromium
```

**Login fails:**
- Check credentials in `.env`
- Run with `HEADLESS=false` to see what's happening
- Check `logs/` for errors

---

**You're ready to go!** The bot will now automatically claim leads as they appear.
