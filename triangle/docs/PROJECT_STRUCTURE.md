# Project Structure & File Organization

## 📂 Complete Directory Structure

```
triangular-arbitrage-bot/
│
├── 📄 main.py                    # Entry point - Run this file
├── 📄 bot.py                     # Main bot controller & orchestrator
├── 📄 config.py                  # Configuration & settings
├── 📄 logger.py                  # Logging system
├── 📄 exchange.py                # Binance API wrapper
├── 📄 calculator.py              # Arbitrage calculations
├── 📄 trader.py                  # Trade execution engine
├── 📄 database.py                # SQLite database manager
│
├── 📄 requirements.txt           # Python dependencies
├── 📄 .env                       # Environment variables (DO NOT COMMIT)
├── 📄 .env.example               # Environment template
├── 📄 .gitignore                 # Git ignore rules
│
├── 📄 README.md                  # Main documentation
├── 📄 INSTALL.md                 # Installation guide
├── 📄 PROJECT_STRUCTURE.md       # This file
│
├── 📄 setup.sh                   # Automated setup script (Linux/Mac)
│
├── 📁 logs/                      # Log files (auto-created)
│   └── arbitrage.log             # Main log file
│
├── 📁 data/                      # Database files (auto-created)
│   └── trades.db                 # SQLite database
│
└── 📁 venv/                      # Virtual environment (auto-created)
    └── ...                       # Python packages
```

## 🔗 File Dependencies & Flow

```
main.py
  │
  ├─> bot.py
  │     │
  │     ├─> exchange.py ────> Binance API
  │     │
  │     ├─> calculator.py
  │     │
  │     ├─> trader.py ────> exchange.py
  │     │
  │     └─> database.py ────> data/trades.db
  │
  ├─> config.py ←──── (Used by all modules)
  │
  └─> logger.py ←──── (Used by all modules)
```

## 📄 Detailed File Descriptions

### Core Files

#### `main.py` - Entry Point
**Purpose**: Command-line interface and program entry point

**Functions**:
- Parse command-line arguments
- Initialize the bot
- Handle different run modes (dry-run, live, test, scan, stats)
- Display statistics

**Usage**:
```bash
python main.py --dry-run      # Simulation mode
python main.py --live         # Live trading
python main.py --test         # Test connection
python main.py --scan         # Single scan
python main.py --stats        # Show statistics
```

---

#### `bot.py` - Main Controller
**Purpose**: Orchestrates all components and runs the main loop

**Key Classes**:
- `ArbitrageBot`: Main bot controller

**Key Methods**:
- `start()`: Start the bot
- `stop()`: Stop gracefully
- `_run_main_loop()`: Main detection/execution loop
- `_handle_opportunity()`: Process detected opportunities
- `test_connection()`: Test exchange connectivity
- `run_single_scan()`: One-time opportunity scan

**Responsibilities**:
- Coordinate all modules
- Main event loop
- Signal handling (Ctrl+C)
- Statistics tracking
- Error recovery

---

#### `config.py` - Configuration
**Purpose**: Centralized configuration management

**Key Settings**:
```python
# API Configuration
BINANCE_API_KEY = ...
BINANCE_API_SECRET = ...
USE_TESTNET = True

# Trading Parameters
INITIAL_CAPITAL = 1000
MIN_PROFIT_THRESHOLD = 0.5
MAX_TRADE_SIZE = 5000

# Fees & Risk
MAKER_FEE = 0.001
TAKER_FEE = 0.001
MAX_SLIPPAGE = 0.002

# Trading Triangles
TRADING_TRIANGLES = [...]
```

**Key Methods**:
- `get_api_url()`: Returns correct API URL
- `validate_config()`: Validates settings

---

#### `logger.py` - Logging System
**Purpose**: Structured logging with file and console output

**Key Classes**:
- `Logger`: Singleton logger instance

**Key Methods**:
- `info()`, `debug()`, `warning()`, `error()`, `critical()`
- `log_opportunity()`: Log detected opportunities
- `log_trade()`: Log trade execution
- `log_error_trade()`: Log trade errors

**Log Format**:
```
2025-10-03 14:23:45 | INFO | Opportunity detected
2025-10-03 14:23:46 | ERROR | Trade failed: Insufficient balance
```

**Output**: 
- File: `logs/arbitrage.log`
- Console: Real-time output

---

#### `exchange.py` - Binance API Wrapper
**Purpose**: Handle all Binance API interactions

**Key Classes**:
- `BinanceExchange`: API wrapper

**Key Methods**:
- `get_ticker_price()`: Get single ticker price
- `get_all_ticker_prices()`: Get all prices at once
- `get_orderbook()`: Get order book depth
- `get_book_ticker()`: Get best bid/ask
- `place_market_order()`: Execute market order
- `get_account_info()`: Get account balance
- `get_balance()`: Get specific asset balance

**Features**:
- Rate limiting
- Request signing for authenticated endpoints
- Error handling
- Session management

---

#### `calculator.py` - Arbitrage Calculator
**Purpose**: Detect and calculate arbitrage opportunities

**Key Classes**:
- `ArbitrageCalculator`: Profit calculator

**Key Methods**:
- `calculate_triangular_arbitrage()`: Basic calculation
- `calculate_precise_triangular()`: Detailed calculation with steps
- `find_all_opportunities()`: Scan all triangles
- `calculate_optimal_trade_size()`: Determine trade size

**Calculation Logic**:
```
For each triangle (A → B → C → A):
  1. Convert A to B using pair1
  2. Convert B to C using pair2
  3. Convert C to A using pair3
  4. Apply fees to each step
  5. Apply slippage
  6. Calculate profit
```

---

#### `trader.py` - Trade Executor
**Purpose**: Execute trades on the exchange

**Key Classes**:
- `TradeExecutor`: Trade execution engine

**Key Methods**:
- `execute_triangle()`: Execute full triangle
- `_execute_step()`: Execute single trade
- `_reverse_trades()`: Emergency trade reversal
- `get_statistics()`: Trading stats
- `dry_run_execute()`: Simulate execution

**Execution Flow**:
```
1. Execute Step 1 (A → B)
2. Execute Step 2 (B → C)
3. Execute Step 3 (C → A)
4. If any step fails → attempt reversal
5. Record results
```

---

#### `database.py` - Database Manager
**Purpose**: Store and retrieve trade history

**Key Classes**:
- `TradeDatabase`: SQLite database manager

**Tables**:
- `trades`: Executed trades
- `opportunities`: Detected opportunities
- `metrics`: Performance snapshots

**Key Methods**:
- `save_trade()`: Store executed trade
- `save_opportunity()`: Store detected opportunity
- `save_metrics()`: Store performance metrics
- `get_all_trades()`: Retrieve trade history
- `get_statistics()`: Get aggregated stats
- `clear_old_data()`: Clean up old records

---

### Configuration Files

#### `requirements.txt`
Lists all Python dependencies:
```
requests==2.31.0
pytest==7.4.3
...
```

#### `.env` (You create this)
Stores sensitive credentials:
```bash
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
```

#### `.env.example`
Template for `.env` file with placeholder values

#### `.gitignore`
Tells git which files to ignore:
- `.env` (sensitive!)
- `logs/`
- `data/`
- `__pycache__/`
- `venv/`

---

### Documentation Files

#### `README.md`
Main documentation covering:
- What the bot does
- How to use it
- Configuration options
- Safety warnings
- Examples

#### `INSTALL.md`
Step-by-step installation guide with troubleshooting

#### `PROJECT_STRUCTURE.md` (This file)
Explains project organization and file relationships

---

### Setup Files

#### `setup.sh`
Automated setup script for Linux/Mac:
- Creates virtual environment
- Installs dependencies
- Creates directories
- Copies .env template

---

## 🔄 Execution Flow

### 1. Startup Sequence

```
main.py
  ↓
Parse arguments
  ↓
Validate config
  ↓
Initialize bot components:
  - Exchange API client
  - Calculator
  - Trader
  - Database
  ↓
Start main loop or run command
```

### 2. Main Loop Flow

```
while running:
  ↓
Fetch all prices from exchange
  ↓
For each triangle:
  - Calculate potential profit
  - Check if above threshold
  ↓
If profitable opportunity found:
  - Log opportunity
  - Execute trade (or simulate)
  - Save to database
  ↓
Sleep (rate limiting)
  ↓
Repeat
```

### 3. Trade Execution Flow

```
Opportunity detected
  ↓
Execute Step 1: A → B
  - Place market order
  - Wait for fill
  ↓
Execute Step 2: B → C
  - Place market order
  - Wait for fill
  ↓
Execute Step 3: C → A
  - Place market order
  - Wait for fill
  ↓
Calculate actual profit
  ↓
Save to database
  ↓
Update statistics
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                              │
│                    (Entry Point)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                         bot.py                               │
│                  (Main Controller)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Start Loop  │→ │ Fetch Prices │→ │Find Opps     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└───────┬──────────────────┬──────────────────┬───────────────┘
        │                  │                  │
        ↓                  ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ exchange.py  │  │calculator.py │  │  trader.py   │
│ (Binance API)│  │(Calculate $) │  │(Execute)     │
└──────┬───────┘  └──────────────┘  └──────┬───────┘
       │                                     │
       ↓                                     ↓
┌─────────────────────────────────────────────────┐
│              Binance Exchange                    │
│         (REST API / WebSocket)                   │
└─────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────┐
│              database.py                         │
│         (SQLite - trades.db)                     │
└─────────────────────────────────────────────────┘
       ↓
┌─────────────────────────────────────────────────┐
│              logger.py                           │
│         (logs/arbitrage.log)                     │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Module Interaction Matrix

| Module | Uses | Used By |
|--------|------|---------|
| **main.py** | bot.py, config.py, logger.py | None (entry point) |
| **bot.py** | All modules | main.py |
| **config.py** | os (environment vars) | All modules |
| **logger.py** | logging, config.py | All modules |
| **exchange.py** | requests, config.py, logger.py | bot.py, trader.py |
| **calculator.py** | config.py, logger.py | bot.py |
| **trader.py** | exchange.py, config.py, logger.py | bot.py |
| **database.py** | sqlite3, config.py | bot.py, main.py |

---

## 🗂️ Database Structure

### Table: `trades`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | DATETIME | Trade execution time |
| triangle_path | TEXT | Path (e.g., "USDT → BTC → ETH → USDT") |
| pairs | TEXT | Trading pairs |
| initial_amount | REAL | Starting amount |
| final_amount | REAL | Ending amount |
| profit | REAL | Actual profit |
| profit_percent | REAL | Profit percentage |
| executed | BOOLEAN | Successfully executed? |
| execution_time | REAL | Time taken to execute |
| error_message | TEXT | Error if failed |
| steps_data | TEXT | JSON of execution steps |

### Table: `opportunities`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | DATETIME | When detected |
| triangle_path | TEXT | Triangle path |
| expected_profit | REAL | Expected profit |
| profit_percent | REAL | Expected profit % |
| reason_not_executed | TEXT | Why not executed |

### Table: `metrics`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PRIMARY KEY | Auto-increment ID |
| timestamp | DATETIME | Snapshot time |
| total_trades | INTEGER | Total trades |
| successful_trades | INTEGER | Successful trades |
| failed_trades | INTEGER | Failed trades |
| total_profit | REAL | Cumulative profit |
| avg_profit_per_trade | REAL | Average profit |
| uptime_seconds | REAL | Bot uptime |

---

## 📋 Configuration Hierarchy

```
Environment Variables (.env)
  ↓
config.py (overrides with code defaults)
  ↓
Runtime (can be modified while running)
```

**Priority Order:**
1. Environment variables (highest)
2. config.py defaults
3. Hardcoded fallbacks (lowest)

---

## 🔐 Security & Sensitive Files

### ⚠️ NEVER COMMIT TO GIT:
- ✅ `.env` - Contains API keys
- ✅ `logs/*.log` - May contain sensitive data
- ✅ `data/*.db` - Contains trade history
- ✅ `venv/` - Virtual environment

### ✅ SAFE TO COMMIT:
- `.env.example` - Template only
- `.gitignore` - Protects sensitive files
- All `.py` files - Code only, no secrets
- Documentation files

---

## 📦 Distribution Package Structure

When sharing the project, include:

```
triangular-arbitrage-bot.zip
│
├── *.py (all Python files)
├── requirements.txt
├── .env.example
├── .gitignore
├── setup.sh
├── README.md
├── INSTALL.md
└── PROJECT_STRUCTURE.md
```

**Exclude:**
- `.env` (user must create)
- `logs/` (will be auto-created)
- `data/` (will be auto-created)
- `venv/` (user must create)
- `__pycache__/` (auto-generated)

---

## 🚀 Quick Reference Commands

### Installation
```bash
./setup.sh                    # Automated setup
python -m venv venv           # Manual: create venv
source venv/bin/activate      # Manual: activate
pip install -r requirements.txt  # Manual: install deps
```

### Running
```bash
python main.py --test         # Test connection
python main.py --scan         # Single scan
python main.py --dry-run      # Simulation mode
python main.py --live         # Live trading (careful!)
python main.py --stats        # Show statistics
```

### Maintenance
```bash
tail -f logs/arbitrage.log    # Watch logs
sqlite3 data/trades.db        # Access database
git status                    # Check git status
pip list                      # Check installed packages
```

---

## 🔧 Customization Points

### Easy Customizations:

**1. Change trading pairs** (`config.py`):
```python
TRADING_TRIANGLES.append({
    'path': ['USDT', 'XRP', 'BNB', 'USDT'],
    'pairs': ['XRPUSDT', 'BNBXRP', 'BNBUSDT']
})
```

**2. Adjust profit threshold** (`config.py`):
```python
MIN_PROFIT_THRESHOLD = 0.3  # Lower = more opportunities
```

**3. Change scan interval** (`config.py`):
```python
UPDATE_INTERVAL = 5  # Scan every 5 seconds
```

### Advanced Customizations:

**1. Add new exchange** (requires new file):
- Create `exchanges/kraken.py`
- Implement same interface as `exchange.py`
- Update `bot.py` to use new exchange

**2. Add machine learning**:
- Create `ml_predictor.py`
- Train on historical opportunity data
- Predict best times to trade

**3. Add web dashboard**:
- Create `web/` directory
- Use Flask/FastAPI
- Display real-time stats

---

## 🐛 Debugging Guide

### Check Each Component:

**1. Configuration**
```python
python -c "from config import Config; Config.validate_config()"
```

**2. Exchange Connection**
```bash
python main.py --test
```

**3. Price Fetching**
```python
from exchange import BinanceExchange
ex = BinanceExchange()
print(ex.get_ticker_price('BTCUSDT'))
```

**4. Calculator**
```python
from calculator import ArbitrageCalculator
calc = ArbitrageCalculator()
# Test calculation logic
```

**5. Database**
```python
from database import TradeDatabase
db = TradeDatabase()
print(db.get_statistics())
```

**6. Logs**
```bash
# View recent activity
tail -n 100 logs/arbitrage.log

# Search for errors
grep ERROR logs/arbitrage.log

# Search for opportunities
grep OPPORTUNITY logs/arbitrage.log
```

---

## 📈 Performance Optimization Tips

### File Level:
- `exchange.py`: Implement WebSocket for faster price updates
- `calculator.py`: Use numpy for faster calculations
- `trader.py`: Implement asyncio for parallel execution
- `database.py`: Add indexes for faster queries

### System Level:
- Use SSD for database
- Run on server near exchange (low latency)
- Use connection pooling
- Cache frequently accessed data

---

## 🎓 Learning Path

### Beginner:
1. Read `README.md`
2. Follow `INSTALL.md`
3. Run `--test` and `--scan`
4. Understand `config.py`
5. Read logs

### Intermediate:
1. Understand `calculator.py` logic
2. Study `exchange.py` API calls
3. Modify `TRADING_TRIANGLES`
4. Analyze database with SQL
5. Run dry-run for extended periods

### Advanced:
1. Study `trader.py` execution flow
2. Implement error handling improvements
3. Add new exchanges
4. Optimize calculations
5. Build web dashboard
6. Implement ML predictions

---

## 🤝 Contributing Guide

### File Naming Conventions:
- Module files: `lowercase.py`
- Constants: `UPPER_CASE`
- Classes: `PascalCase`
- Functions: `snake_case`

### Code Style:
- Follow PEP 8
- Use type hints
- Write docstrings
- Comment complex logic

### Testing:
- Add tests in `tests/`
- Test each module independently
- Use pytest framework

---

## 📚 Additional Resources

### Project Files Documentation:
- **README.md**: User guide
- **INSTALL.md**: Installation steps
- **This file**: Architecture overview

### External Resources:
- [Binance API Docs](https://binance-docs.github.io/apidocs/spot/en/)
- [Python Style Guide](https://pep8.org/)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)

---

## ✅ Checklist for New Users

Before starting:
- [ ] Read README.md completely
- [ ] Follow INSTALL.md step-by-step
- [ ] Understand this PROJECT_STRUCTURE.md
- [ ] Set up .env with testnet keys
- [ ] Run connection test
- [ ] Run single scan
- [ ] Review config.py settings
- [ ] Start dry-run mode
- [ ] Monitor logs for issues
- [ ] Check database after runs
- [ ] Understand the risks
- [ ] Only then consider live trading

---

**Remember**: This is a complex system. Take time to understand each component before using real money!
