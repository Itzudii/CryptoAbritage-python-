# 🚀 Complete Connection & Usage Guide

## 📥 STEP 1: Create Project Files (5 minutes)

### Option A: Create Files Manually

1. **Create project folder:**
   ```bash
   mkdir triangular-arbitrage-bot
   cd triangular-arbitrage-bot
   ```

2. **Create each Python file:**
   
   Copy content from the artifacts I provided above:
   
   ```bash
   # Create files one by one
   touch config.py logger.py exchange.py calculator.py
   touch trader.py database.py bot.py main.py
   touch requirements.txt .env.example .gitignore setup.sh
   ```

3. **Copy the content:**
   - Open `COMPLETE_PROJECT_ALL_FILES.txt` (artifact 1)
   - Copy content of `config.py` → paste into your `config.py` file
   - Copy content of `logger.py` → paste into your `logger.py` file
   - Repeat for all files from all 3 artifacts

4. **Create directories:**
   ```bash
   mkdir logs
   mkdir data
   ```

### Option B: Quick Script Method (Recommended)

Save this as `create_project.sh` and run it:

```bash
#!/bin/bash

# Create project directory
mkdir -p triangular-arbitrage-bot
cd triangular-arbitrage-bot

# Create subdirectories
mkdir -p logs data

# Create all Python files
touch config.py logger.py exchange.py calculator.py
touch trader.py database.py bot.py main.py

# Create config files
touch requirements.txt .env.example .gitignore setup.sh

# Create documentation
touch README.md QUICKSTART.md INSTALL.md PROJECT_STRUCTURE.md

echo "✅ Project structure created!"
echo "Now copy the file contents from the artifacts."
```

Run it:
```bash
chmod +x create_project.sh
./create_project.sh
```

---

## 🔧 STEP 2: Install Python & Dependencies (5 minutes)

### Check Python Version

```bash
python3 --version
# Should show Python 3.8 or higher
```

**Don't have Python?**

- **Ubuntu/Debian:** `sudo apt-get install python3 python3-pip`
- **Mac:** `brew install python3`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install packages
pip install --upgrade pip
pip install requests
```

---

## 🔑 STEP 3: Get Binance API Keys (3 minutes)

### For Testing (RECOMMENDED - Use Fake Money):

1. **Go to Binance Testnet:**
   - Visit: https://testnet.binance.vision/
   
2. **Generate Keys:**
   - Click: **"Generate HMAC_SHA256 Key"**
   - You'll see:
     ```
     API Key: xxxxxxxxxxxxxx
     Secret Key: xxxxxxxxxxxxxx
     ```
   
3. **Copy both keys** (you'll need them next)

### For Live Trading (ONLY AFTER EXTENSIVE TESTING):

1. Login to https://www.binance.com/
2. Go to: Profile → API Management
3. Create New Key
4. **IMPORTANT Security Settings:**
   - ✅ Enable: "Spot & Margin Trading"
   - ❌ Disable: "Enable Withdrawals" (NEVER enable)
   - ✅ Enable: "IP Access Restrictions" (add your IP)

---

## ⚙️ STEP 4: Configure the Bot (2 minutes)

### Create `.env` File

```bash
# Copy template
cp .env.example .env

# Edit the file
nano .env  # or use any text editor
```

**Add your API keys:**
```bash
# For TESTNET (recommended):
BINANCE_API_KEY=your_testnet_api_key_paste_here
BINANCE_API_SECRET=your_testnet_secret_paste_here

# Leave these commented for now:
# TELEGRAM_BOT_TOKEN=
# TELEGRAM_CHAT_ID=
```

**Save and close** (Ctrl+X, then Y, then Enter in nano)

### Verify config.py Settings

Open `config.py` and ensure:
```python
USE_TESTNET = True  # ✅ MUST BE TRUE for testing!
INITIAL_CAPITAL = 1000  # Starting amount
MIN_PROFIT_THRESHOLD = 0.5  # 0.5% minimum profit
```

---

## ✅ STEP 5: Test Connection (1 minute)

```bash
# Make sure venv is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Test connection
python main.py --test
```

**Expected output:**
```
Testing exchange connection...
✅ Successfully fetched 2000+ ticker prices
✅ Connection test passed!
```

**If you see errors:**
- ❌ "API keys invalid" → Check your `.env` file
- ❌ "Connection failed" → Check internet connection
- ❌ "Module not found" → Run `pip install requests`

---

## 🎮 STEP 6: Run Your First Scan (30 seconds)

```bash
python main.py --scan
```

**You should see:**
```
Running single opportunity scan...
Found 0 opportunities:
(or)
Found 2 opportunities:
1. USDT -> BTC -> ETH -> USDT: 5.23 USDT (0.52%)
2. USDT -> ETH -> BNB -> USDT: 3.14 USDT (0.31%)
```

**Note:** It's NORMAL to see 0 opportunities! Arbitrage is rare.

---

## 🏃 STEP 7: Run the Bot in Simulation Mode (SAFE!)

```bash
python main.py --dry-run
```

**You'll see:**
```
==========================================
🚀 ARBITRAGE BOT STARTED
==========================================
Mode: DRY RUN (Simulation)
Monitoring 4 triangular paths
Min profit threshold: 0.5%
Initial capital: 1000 USDT
==========================================
```

**The bot is now running!**
- It scans for opportunities every second
- If it finds one, it SIMULATES the trade (no real money)
- Press `Ctrl+C` to stop

---

## 📊 STEP 8: Check Results

### View Logs
```bash
# Real-time monitoring
tail -f logs/arbitrage.log

# View all logs
cat logs/arbitrage.log
```

### Check Statistics
```bash
python main.py --stats
```

**Output:**
```
📊 TRADING STATISTICS
Total trades executed: 5
Profitable trades: 3
Success rate: 60.00%
Total profit: 12.45 USDT
```

### Check Database
```bash
sqlite3 data/trades.db

# Run queries:
SELECT * FROM trades LIMIT 5;
SELECT * FROM opportunities LIMIT 10;
.exit
```

---

## 🎯 Usage Examples

### Daily Workflow

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Quick scan
python main.py --scan

# 3. Run for a few hours
python main.py --dry-run

# 4. Stop with Ctrl+C

# 5. Check results
python main.py --stats
```

### Customize Settings

**To find more opportunities:**
```python
# Edit config.py
MIN_PROFIT_THRESHOLD = 0.1  # Lower = more opportunities
```

**To add more triangles:**
```python
# Edit config.py
TRADING_TRIANGLES.append({
    'path': ['USDT', 'XRP', 'BNB', 'USDT'],
    'pairs': ['XRPUSDT', 'BNBXRP', 'BNBUSDT']
})
```

---

## 🚨 TROUBLESHOOTING

### Problem: "Module 'requests' not found"

**Solution:**
```bash
source venv/bin/activate
pip install requests
```

### Problem: "No opportunities found"

**Solution:** This is NORMAL! Try:
```python
# In config.py, lower the threshold
MIN_PROFIT_THRESHOLD = 0.1  # From 0.5 to 0.1
```

### Problem: "API Error 403"

**Solutions:**
1. Check API keys are correct
2. Verify `USE_TESTNET = True` if using testnet keys
3. Check IP restrictions on Binance

### Problem: Bot stops immediately

**Check logs:**
```bash
tail -20 logs/arbitrage.log
```

Look for error messages and fix accordingly.

---

## 📱 Connect from Different Devices

### Run on Cloud Server (AWS/DigitalOcean)

```bash
# SSH into server
ssh user@your-server-ip

# Install Python
sudo apt-get update
sudo apt-get install python3 python3-pip

# Transfer files
scp -r triangular-arbitrage-bot user@your-server-ip:~/

# Run in background
nohup python main.py --dry-run > output.log 2>&1 &

# Check if running
ps aux | grep python
```

### Run on Windows

```powershell
# Create venv
python -m venv venv

# Activate
venv\Scripts\activate

# Install
pip install requests

# Run
python main.py --test
python main.py --dry-run
```

### Run on Mac

```bash
# Same as Linux
python3 -m venv venv
source venv/bin/activate
pip install requests
python main.py --test
```

---

## 🔄 Daily Operations

### Morning Routine
```bash
cd triangular-arbitrage-bot
source venv/bin/activate
python main.py --scan  # Check for opportunities
python main.py --stats  # Check yesterday's performance
```

### Start Bot
```bash
python main.py --dry-run  # Simulation
# OR (only after weeks of testing!)
python main.py --live  # Real trading
```

### Stop Bot
```
Press Ctrl+C
```

### Check Performance
```bash
python main.py --stats
cat logs/arbitrage.log | grep OPPORTUNITY
```

---

## ⚠️ Before Going LIVE

### Testing Checklist

- [ ] Ran on testnet for 1+ week
- [ ] Dry-run mode for several days
- [ ] Checked logs for errors
- [ ] Verified calculations are correct
- [ ] Understand all risks
- [ ] Read all documentation
- [ ] Start with $100-500 max
- [ ] Monitor every hour for first day

### Going Live

```bash
# 1. Edit config.py
USE_TESTNET = False  # ⚠️ CAREFUL!

# 2. Edit .env with LIVE keys
BINANCE_API_KEY=your_LIVE_api_key
BINANCE_API_SECRET=your_LIVE_secret

# 3. Run with confirmation
python main.py --live
# Type 'YES' when prompted
```

---

## 📚 Next Steps

1. **Let it run** in dry-run mode for 24 hours
2. **Check statistics** regularly
3. **Read the logs** to understand what it's doing
4. **Adjust parameters** in config.py
5. **Add more triangles** if you want
6. **Monitor performance** over days/weeks
7. **Only then consider** live trading (if profitable)

---

## 🆘 Need Help?

### Quick Checks
1. Is Python 3.8+ installed? `python3 --version`
2. Is venv activated? You should see `(venv)` in terminal
3. Are API keys correct in `.env`?
4. Is `USE_TESTNET = True` in config.py?
5. Are logs showing errors? `cat logs/arbitrage.log`

### Resources
- **README.md** - Full documentation
- **QUICKSTART.md** - Fast setup
- **INSTALL.md** - Installation troubleshooting
- **Logs** - Check `logs/arbitrage.log` for errors

---

## ✅ Connection Checklist

- [ ] All files created
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] API keys added to `.env`
- [ ] `USE_TESTNET = True` in config.py
- [ ] Connection test passes
- [ ] Single scan works
- [ ] Dry-run mode runs successfully
- [ ] Can stop with Ctrl+C
- [ ] Can check statistics

---

**🎉 You're now connected and ready to use the bot!**

Start with `python main.py --dry-run` and let it run for a while. Good luck! 🚀
