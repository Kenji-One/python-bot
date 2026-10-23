# Hetzner VPS Setup Guide

Complete guide for deploying the PowerPlay Lead Claimer Bot on a Hetzner VPS.

## VPS Requirements

**Minimum Specs:**
- 2 GB RAM (1 GB might work but 2 GB recommended)
- 1 vCPU
- 20 GB storage
- Ubuntu 22.04 or 24.04 LTS

**Recommended Hetzner Plan:**
- CPX11 (2 vCPU, 2 GB RAM) - €4.51/month
- Or CX21 (2 vCPU, 4 GB RAM) - €5.83/month

---

## Initial VPS Setup

### 1. Connect to VPS

```bash
ssh root@your-vps-ip
```

### 2. Update System

```bash
apt update && apt upgrade -y
```

### 3. Install Python 3.12

```bash
# Add deadsnakes PPA for Python 3.12
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa -y
apt update

# Install Python 3.12
apt install python3.12 python3.12-venv python3.12-dev -y

# Verify installation
python3.12 --version
```

### 4. Install System Dependencies for Playwright

```bash
# Install required libraries for Chromium
apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    wget \
    ca-certificates

# Install git
apt install git -y
```

---

## Deploy the Bot

### 1. Upload Bot Files

**Option A: Using Git (if you have a repo)**
```bash
cd /opt
git clone https://github.com/yourusername/powerplay-lead-claimer.git
cd powerplay-lead-claimer
```

**Option B: Using SCP from your local machine**
```bash
# From your local machine
cd ~/Documents/kenjis-tasks/python-bot
scp -r powerplay-lead-claimer root@your-vps-ip:/opt/
```

**Option C: Manual upload**
```bash
# On VPS
mkdir -p /opt/powerplay-lead-claimer
cd /opt/powerplay-lead-claimer

# Then upload files via SFTP or use rsync
```

### 2. Create Virtual Environment

```bash
cd /opt/powerplay-lead-claimer

# Create venv with Python 3.12
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install Python packages
pip install -r requirements-simple.txt

# Install Playwright browsers
playwright install chromium

# Install Playwright system dependencies
playwright install-deps chromium
```

### 4. Configure Credentials

```bash
# Copy example config
cp .env.example .env

# Edit with your credentials
nano .env
```

**Important VPS settings in .env:**
```env
POWERPLAY_USERNAME=your_email@example.com
POWERPLAY_PASSWORD=your_password_here

# MUST be true for VPS
HEADLESS=true

# Optimize for VPS
POLLING_INTERVAL_MS=400
ENABLE_SOUND_NOTIFICATION=false  # No sound on VPS
ENABLE_SCREENSHOTS=true
ENABLE_AUTO_RESTART=true
LOG_TO_FILE=true
```

### 5. Test Run

```bash
# Activate venv if not already
source venv/bin/activate

# Run the bot
python main.py
```

Press `Ctrl+C` to stop.

---

## Run as Background Service (Recommended)

### Create Systemd Service

```bash
nano /etc/systemd/system/powerplay-bot.service
```

**Add this content:**
```ini
[Unit]
Description=PowerPlay Lead Claimer Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/powerplay-lead-claimer
Environment="PATH=/opt/powerplay-lead-claimer/venv/bin"
ExecStart=/opt/powerplay-lead-claimer/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable service (start on boot)
systemctl enable powerplay-bot

# Start service
systemctl start powerplay-bot

# Check status
systemctl status powerplay-bot
```

### Service Management Commands

```bash
# View logs (live)
journalctl -u powerplay-bot -f

# View logs (last 100 lines)
journalctl -u powerplay-bot -n 100

# Restart service
systemctl restart powerplay-bot

# Stop service
systemctl stop powerplay-bot

# Check if service is running
systemctl is-active powerplay-bot
```

---

## Monitoring & Maintenance

### Check Bot Logs

```bash
# View live logs
tail -f /opt/powerplay-lead-claimer/logs/bot_*.log

# View systemd logs
journalctl -u powerplay-bot -f

# Check last 50 lines
tail -50 /opt/powerplay-lead-claimer/logs/bot_$(date +%Y%m%d).log
```

### Check Screenshots

```bash
# List recent screenshots
ls -lth /opt/powerplay-lead-claimer/screenshots/ | head -10

# Download screenshot to local machine
scp root@your-vps-ip:/opt/powerplay-lead-claimer/screenshots/filename.png ~/Downloads/
```

### Monitor Resource Usage

```bash
# Check CPU and memory
htop

# Or simpler
top

# Check disk space
df -h

# Check bot process specifically
ps aux | grep python
```

### Update Bot Code

```bash
# Stop the service
systemctl stop powerplay-bot

# Update code (if using git)
cd /opt/powerplay-lead-claimer
git pull

# Or upload new files via SCP

# Restart service
systemctl start powerplay-bot
```

---

## Firewall Configuration (Optional but Recommended)

```bash
# Install UFW
apt install ufw -y

# Allow SSH
ufw allow 22/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

---

## Performance Optimization

### Reduce Memory Usage

Edit [config.py](config.py) and add:

```python
# In bot.py, browser launch args
self.browser = await self.playwright.chromium.launch(
    headless=Config.HEADLESS,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",  # Add this
        "--disable-software-rasterizer",  # Add this
        "--single-process",  # Add this for lower memory
    ],
)
```

### Auto-restart on Crash

The systemd service already has `Restart=always`, but you can also add a cron job:

```bash
crontab -e
```

Add:
```
# Restart bot daily at 3 AM
0 3 * * * systemctl restart powerplay-bot
```

---

## Troubleshooting

### Bot Won't Start

```bash
# Check detailed errors
journalctl -u powerplay-bot -xe

# Check if Playwright is installed
/opt/powerplay-lead-claimer/venv/bin/playwright --version

# Reinstall Playwright
cd /opt/powerplay-lead-claimer
source venv/bin/activate
playwright install chromium
playwright install-deps
```

### "Error: Could not find browser"

```bash
# Reinstall Playwright browsers
playwright install chromium
playwright install-deps chromium
```

### High Memory Usage

```bash
# Check memory
free -h

# If low, add swap (if not already)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Login Fails

```bash
# Check credentials in .env
cat /opt/powerplay-lead-claimer/.env

# Check screenshots for errors
ls -lth /opt/powerplay-lead-claimer/screenshots/
```

---

## Security Best Practices

1. **Change SSH Port** (optional)
   ```bash
   nano /etc/ssh/sshd_config
   # Change Port 22 to Port 2222
   systemctl restart sshd
   ```

2. **Set up SSH Keys** instead of password
3. **Keep system updated**
   ```bash
   apt update && apt upgrade -y
   ```

4. **Secure .env file**
   ```bash
   chmod 600 /opt/powerplay-lead-claimer/.env
   ```

---

## Cost Estimate

**Hetzner CPX11:**
- €4.51/month (2 vCPU, 2 GB RAM)
- ~€55/year

**Total cost to run bot 24/7: ~€55/year**

---

## Quick Command Reference

```bash
# Start bot
systemctl start powerplay-bot

# Stop bot
systemctl stop powerplay-bot

# Restart bot
systemctl restart powerplay-bot

# View live logs
journalctl -u powerplay-bot -f

# Check status
systemctl status powerplay-bot

# View file logs
tail -f /opt/powerplay-lead-claimer/logs/bot_*.log
```

---

## Alternative: Using Screen (Simpler but Less Robust)

If you don't want to use systemd:

```bash
# Install screen
apt install screen -y

# Start a screen session
screen -S powerplay

# Navigate to bot directory
cd /opt/powerplay-lead-claimer
source venv/bin/activate

# Run bot
python main.py

# Detach from screen: Press Ctrl+A then D

# Reattach to screen
screen -r powerplay

# List sessions
screen -ls
```

---

## Next Steps

After setup is complete, the bot will run 24/7 automatically claiming leads!

Monitor it regularly via logs and screenshots to ensure it's working properly.
