# 🔺 Triangular Arbitrage Trading Bot

A production-ready cryptocurrency arbitrage bot that detects and executes triangular arbitrage opportunities on Binance.

## 📋 What is Triangular Arbitrage?

Triangular arbitrage exploits price inefficiencies between three trading pairs. For example:
1. Start with **USDT**
2. Trade **USDT → BTC** 
3. Trade **BTC → ETH**
4. Trade **ETH → USDT**

If the final amount > initial amount (after fees), you've made a profit!

## 🏗️ Project Structure

```
triangular-arbitrage-bot/
│
├── config.py              # Configuration and settings
├── logger.py              # Logging system
├── exchange.py            # Binance API wrapper
├── calculator.py          # Arbitrage calculations
├── trader.py              # Trade execution engine
├── database.py            # SQLite database for history
├── bot.py                 # Main bot controller
├── main.py                # Entry point
│
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variables template
│
├── logs/                 # Log files (auto-created)
│   └── arbitrage.log
│
└── data/                 # Database files (auto-created)
    └── trades.db
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd triangular-arbitrage-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file (copy from `.env.example`):

```bash
# For testnet (recommended for testing)
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# For live trading (BE CAREFUL!)
# BINANCE_API_KEY=your_live_api_key
# BINANCE_API_SECRET=your_live_api_secret
```

Edit `config.py` to customize:
- `USE_TESTNET`: Set to `True` for testing, `False` for live
- `MIN_PROFIT_THRESHOLD`: Minimum profit % to execute trades
- `INITIAL_CAPITAL`: Starting capital amount
- `TRADING_TRIANGLES`: Which triangular paths to monitor

### 3. Running the Bot

#### Dry Run Mode (Simulation - Recommended for Testing)
```bash
python main.py --dry-run
```

#### Test Connection
```bash
python main.py --test
```

#### Single Scan (Check for Opportunities)
```bash
python main.py --scan
```

#### Show Statistics
```bash
python main.py --stats
```

#### Live Trading (⚠️ USES REAL MONEY!)
```bash
python main.py --live
```

## 📊 Features

### ✅ Core Features
- **Real-time price monitoring** via Binance API
- **Automatic opportunity detection** across multiple triangular paths
- **Profit calculation** with fees and slippage consideration
- **Trade execution** with proper order handling
- **Risk management** with configurable thresholds
- **Database storage** for trade history and analytics
- **Comprehensive logging** with file and console output

### 🛡️ Safety Features
- **Dry-run mode** for testing without real money
- **Rate limiting** to respect API limits
- **Error handling** with trade reversal capability
- **Configurable risk parameters**
- **Confirmation prompt** for live trading

### 📈 Analytics
- Real-time profit tracking
- Success rate monitoring
- Trade history database
- Performance metrics
- Detailed execution logs

## ⚙️ Configuration Options

### Trading Parameters (`config.py`)

```python
INITIAL_CAPITAL = 1000           # Starting capital in USDT
MIN_PROFIT_THRESHOLD = 0.5       # Minimum profit % (0.5%)
MAX_TRADE_SIZE = 5000            # Maximum trade size
MAKER_FEE = 0.001                # 0.1% maker fee
TAKER_FEE = 0.001                # 0.1% taker fee
MAX_SLIPPAGE = 0.002             # 0.2% slippage tolerance
```

### Monitored Triangles

By default, the bot monitors these paths:
- USDT → BTC → ETH → USDT
- USDT → BTC → BNB → USDT
- USDT → ETH → BNB → USDT
- BTC → ETH → BNB → BTC

You can add more in `config.py`:

```python
TRADING_TRIANGLES = [
    {
        'path': ['USDT', 'BTC', 'ETH', 'USDT'],
        'pairs': ['BTCUSDT', 'ETHBTC', 'ETHUSDT']
    },
    # Add more...
]
```

## 📝 Usage Examples

### Example 1: Test and Scan
```bash
# Test connection
python main.py --test

# Run a single scan to see current opportunities
python main.py --scan
```

### Example 2: Run in Simulation Mode
```bash
# Run continuously in dry-run mode
python main.py --dry-run

# Stop with Ctrl+C
```

### Example 3: Check Statistics
```bash
python main.py --stats
```

## 🎯 How It Works

1. **Price Fetching**: Bot continuously fetches live prices from Binance
2. **Opportunity Detection**: Calculates potential profit for each triangle
3. **Validation**: Checks if profit exceeds minimum threshold (after fees + slippage)
4. **Execution**: Places market orders in sequence to complete the triangle
5. **Logging**: Records all trades and opportunities in database

## 🧮 Profit Calculation

The bot calculates profit considering:

```
Final Amount = Initial × Rate1 × Rate2 × Rate3 × (1-fee)³ × (1-slippage)

Profit = Final Amount - Initial Amount
Profit % = (Profit / Initial) × 100
```

**Example:**
- Start: 1000 USDT
- Rate1 (USDT→BTC): 0.00002 BTC/USDT
- Rate2 (BTC→ETH): 15 ETH/BTC
- Rate3 (ETH→USDT): 3400 USDT/ETH
- Fees: 0.1% per trade
- Slippage: 0.2%

```
1000 USDT → 0.02 BTC → 0.3 ETH → 1020 USDT
After fees & slippage: ~1012 USDT
Profit: 12 USDT (1.2%)
```

## ⚠️ Important Warnings

### ⚠️ Risk Factors

1. **Market Volatility**: Prices can change between detection and execution
2. **Slippage**: Actual execution price may differ from expected
3. **Network Latency**: Delays can eliminate profit opportunities
4. **Exchange Fees**: Must be accurately calculated
5. **API Rate Limits**: Exceeding limits can result in temporary bans
6. **Capital Loss**: Losses are possible, especially in volatile markets

### ⚠️ Before Live Trading

1. ✅ **Test extensively** with testnet/dry-run mode
2. ✅ **Start small** with minimal capital
3. ✅ **Monitor closely** for the first few hours
4. ✅ **Understand the risks** - only trade what you can afford to lose
5. ✅ **Check API permissions** - ensure trading is enabled
6. ✅ **Review exchange fees** - different VIP levels have different fees

## 🔧 Advanced Configuration

### Environment Variables

Create `.env` file:

```bash
# Binance API Credentials
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Optional: Telegram Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### Custom Triangle Paths

To add custom triangular paths, edit `config.py`:

```python
TRADING_TRIANGLES.append({
    'path': ['USDT', 'ADA', 'BNB', 'USDT'],
    'pairs': ['ADAUSDT', 'BNBADA', 'BNBUSDT']
})
```

**Important**: Ensure pairs exist on exchange and are formatted correctly!

## 📊 Database Schema

The bot stores data in SQLite (`data/trades.db`):

### Tables

**trades** - Executed trades
- `id`, `timestamp`, `triangle_path`, `pairs`
- `initial_amount`, `final_amount`, `profit`, `profit_percent`
- `executed`, `execution_time`, `error_message`, `steps_data`

**opportunities** - Detected opportunities
- `id`, `timestamp`, `triangle_path`
- `expected_profit`, `profit_percent`, `reason_not_executed`

**metrics** - Performance snapshots
- `id`, `timestamp`, `total_trades`, `successful_trades`
- `failed_trades`, `total_profit`, `avg_profit_per_trade`, `uptime_seconds`

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test connection
python main.py --test

# Check logs
cat logs/arbitrage.log
```

### No Opportunities Found

This is normal! Arbitrage opportunities are rare and short-lived. Factors:
- Market efficiency (most inefficiencies are quickly arbitraged away)
- High competition from other bots
- Fee structure (must overcome ~0.3% in fees)
- Your profit threshold might be too high

Try:
- Lowering `MIN_PROFIT_THRESHOLD` (but be careful!)
- Adding more triangular paths
- Using a VIP account for lower fees

### API Rate Limit Errors

```python
# In config.py, adjust:
MAX_API_CALLS_PER_MINUTE = 600  # Lower this value
UPDATE_INTERVAL = 2  # Increase scan interval
```

### Execution Errors

Check:
1. API permissions (trading enabled?)
2. Account balance (sufficient funds?)
3. Symbol precision (quantity formatted correctly?)
4. Market status (is the pair trading?)

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use testnet first** before any live trading
3. **Restrict API permissions** (only enable spot trading, no withdrawals)
4. **Use IP whitelist** on Binance API settings
5. **Keep dependencies updated** for security patches
6. **Monitor bot activity** regularly
7. **Set stop-loss limits** in config

## 📈 Performance Optimization

### Speed Improvements

1. **Use WebSocket** instead of REST API for prices (future enhancement)
2. **Colocate** bot near exchange servers (lower latency)
3. **Optimize code** in hot paths (calculator functions)
4. **Use asyncio** for parallel API calls (future enhancement)

### Profitability Improvements

1. **Get VIP status** for lower fees (0.075% vs 0.1%)
2. **Monitor more pairs** to find more opportunities
3. **Use limit orders** for better prices (but slower execution)
4. **Optimize triangle selection** based on liquidity

## 🧪 Testing

### Unit Tests (Coming Soon)

```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/
```

### Manual Testing Checklist

- [ ] Connection test passes
- [ ] Single scan shows prices
- [ ] Dry-run mode executes without errors
- [ ] Statistics display correctly
- [ ] Logs are being written
- [ ] Database is being populated

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- WebSocket support for real-time data
- More exchanges (Kraken, KuCoin, etc.)
- Advanced order types (limit orders)
- Machine learning for opportunity prediction
- Web dashboard for monitoring
- Telegram/Discord notifications
- Backtesting framework
- Multi-exchange arbitrage

## 📄 License

This project is for educational purposes. Use at your own risk.

**Disclaimer**: Cryptocurrency trading involves substantial risk. This bot is provided as-is with no guarantees of profit. Always test thoroughly and never trade more than you can afford to lose.

## 🆘 Support

For issues or questions:
1. Check this README thoroughly
2. Review logs in `logs/arbitrage.log`
3. Check Binance API documentation
4. Search for similar issues

## 📚 Additional Resources

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [Triangular Arbitrage Explained](https://www.investopedia.com/terms/t/triangulararbitrage.asp)
- [Cryptocurrency Trading Strategies](https://www.binance.com/en/blog)

---

**⚡ Remember**: Arbitrage opportunities are fleeting. Speed, accuracy, and risk management are crucial for success!

**💡 Pro Tip**: Start with testnet, run dry-run for several days, analyze results, then consider small live trades if profitable.
