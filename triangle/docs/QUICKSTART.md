# ⚡ Quick Start Guide

Get the Triangular Arbitrage Bot running in **5 minutes**!

## 🎯 Prerequisites

- Python 3.8+ installed
- Terminal/Command Prompt access
- 5 minutes of your time

## 🚀 5-Minute Setup

### Step 1: Download & Extract (30 seconds)

Download the project and extract to a folder.

```bash
cd triangular-arbitrage-bot
```

### Step 2: Auto Setup (2 minutes)

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Step 3: Get Test API Keys (1 minute)

1. Go to https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Copy the keys

### Step 4: Configure (1 minute)

Edit `.env` file:
```bash
BINANCE_API_KEY=paste_your_testnet_key_here
BINANCE_API_SECRET=paste_your_testnet_secret_here
```

Verify `config.py` has:
```python
USE_TESTNET = True  # ✅ MUST be True for testing
```

### Step 5: Test & Run (30 seconds)

```bash
# Test connection
python main.py --test

# Run single scan
python main.py --scan

# Start bot in simulation mode
python main.py --dry-run
```

## 🎉 You're Running!

You should see:
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

Press `Ctrl+C` to stop.

## 📊 Check Results

```bash
# View statistics
python main.py --stats

# Check logs
cat logs/arbitrage.log
```

## ⚠️ Important Notes

✅ **You're in SAFE MODE**
- Using testnet (fake money)
- No real trades
- Perfect for learning

❌ **Don't rush to live trading**
- Test for days/weeks first
- Understand how it works
- Only use money you can afford to lose

## 🎯 Next Steps

1. **Let it run** for a few hours
2. **Check statistics** to see what it found
3. **Read the full README.md**
4. **Understand the code**
5. **Customize settings** in `config.py`
6. **Only then** consider live trading (if profitable)

## 🐛 Quick Troubleshooting

**"Command not found"**
```bash
# Use python3 instead of python
python3 main.py --test
```

**"Module not found"**
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# Reinstall
pip install -r requirements.txt
```

**"API keys invalid"**
- Double-check you copied them correctly
- Make sure no extra spaces
- Verify `USE_TESTNET = True` in config.py

**"No opportunities found"**
- This is normal! Real arbitrage is rare
- Lower `MIN_PROFIT_THRESHOLD` to 0.1% in config.py
- Let it run longer

## 🆘 Need Help?

1. Read the full **README.md**
2. Check **INSTALL.md** for detailed steps
3. Review **PROJECT_STRUCTURE.md** to understand files
4. Check logs: `logs/arbitrage.log`

## 📚 Full Documentation

- **README.md** - Complete user guide
- **INSTALL.md** - Detailed installation
- **PROJECT_STRUCTURE.md** - Code architecture

---

**🎊 Congratulations! You're now running an arbitrage bot!**

*Remember: Start small, test thoroughly, understand the risks.* 🚀
