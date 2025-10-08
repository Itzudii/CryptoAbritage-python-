"""
Configuration module for Triangular Arbitrage Bot
Stores all configuration parameters and API credentials
"""

import os
import json
from typing import Dict, List
from pathlib import Path

# Load environment variables from a local .env file if present
try:
    from dotenv import load_dotenv
    # Search for a .env in project root
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        # Fallback to default discovery (will noop if none)
        load_dotenv()
except Exception:
    # Safe fallback if python-dotenv is not installed; os.getenv will still work
    pass

class Config:
    """Main configuration class"""
    
    # API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')
    
    # Exchange URLs
    BINANCE_BASE_URL = 'https://api.binance.com'
    BINANCE_TESTNET_URL = 'https://testnet.binance.vision'
    BINANCE_WS_MAINNET = 'wss://stream.binance.com:9443/ws'
    BINANCE_WS_TESTNET = 'wss://testnet.binance.vision/ws'
    
    # Trading Configuration
    USE_TESTNET = False  # Use mainnet public data (still dry-run unless live trading enabled)
    INITIAL_CAPITAL = 1000  # Starting capital in USDT
    MIN_PROFIT_THRESHOLD = 0.5  # Minimum profit % to execute trade
    MAX_TRADE_SIZE = 5000  # Maximum trade size in USDT
    
    # Fee Configuration
    MAKER_FEE = 0.001  # 0.1%
    TAKER_FEE = 0.001  # 0.1%
    
    # Risk Management
    MAX_SLIPPAGE = 0.002  # 0.2% max slippage tolerance
    STOP_LOSS_PERCENT = 2.0  # Stop if losses exceed this % (per-trade conceptual)
    # Daily and frequency limits
    DAILY_MAX_LOSS_PCT = 5.0  # Hard stop at -5% daily loss
    MAX_TRADES_PER_DAY = 50   # Cap daily trades to avoid overtrading
    MAX_CONSECUTIVE_LOSSES = 3  # Pause if this many consecutive losses occur
    # Cooldowns (in seconds)
    LOSS_COOLDOWN_SEC = 300  # 5 minutes after any loss
    COOLDOWN_AFTER_2_LOSSES_SEC = 900  # 15 minutes after 2 consecutive losses
    COOLDOWN_AFTER_3_LOSSES_SEC = 3600  # 1 hour after 3 consecutive losses
    DAILY_STOP_RESUME_DELAY_SEC = 3600  # After daily stop, minimum 1 hour pause
    # Execution safeguards
    MIN_FILL_RATIO = 0.95  # Require at least 95% fill or abort
    SINGLE_TRADE_TIMEOUT_SEC = 2.0
    FULL_TRIANGLE_TIMEOUT_SEC = 5.0
    # API health
    API_ERROR_RATE_PAUSE_THRESHOLD = 0.10  # 10% error rate triggers pause
    API_ERROR_PAUSE_SEC = 300  # 5 minutes
    API_ERROR_RATE_WINDOW_SEC = 60  # Compute error rate over this sliding window
    
    # Risk state persistence
    RISK_STATE_PATH = 'data/risk_state.json'
    
    # Performance Configuration
    UPDATE_INTERVAL = 1  # Seconds between price updates
    MAX_API_CALLS_PER_MINUTE = 1200
    USE_WEBSOCKET = True  # Enable real-time WS prices
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/arbitrage.log'
    LOG_TO_CONSOLE = True
    
    # Trading Pairs Configuration
    BASE_CURRENCIES = ['USDT', 'BTC', 'ETH', 'BNB']
    
    # Triangular paths to monitor
    TRADING_TRIANGLES: List[Dict[str, str]] = [
        {
            'path': ['USDT', 'BTC', 'ETH', 'USDT'],
            'pairs': ['BTCUSDT', 'ETHBTC', 'ETHUSDT']
        },
        {
            'path': ['USDT', 'BTC', 'BNB', 'USDT'],
            'pairs': ['BTCUSDT', 'BNBBTC', 'BNBUSDT']
        },
        {
            'path': ['USDT', 'ETH', 'BNB', 'USDT'],
            'pairs': ['ETHUSDT', 'BNBETH', 'BNBUSDT']
        },
        {
            'path': ['BTC', 'ETH', 'BNB', 'BTC'],
            'pairs': ['ETHBTC', 'BNBETH', 'BNBBTC']
        }
    ]
    
    # Database Configuration (for trade history)
    DB_PATH = 'data/trades.db'
    
    # Notification Configuration
    ENABLE_NOTIFICATIONS = False
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # API Security / CORS
    API_ALLOWED_ORIGINS = [o.strip() for o in os.getenv('API_ALLOWED_ORIGINS', '*').split(',') if o.strip()]
    DASHBOARD_API_KEY = os.getenv('DASHBOARD_API_KEY', '')
    # Runtime overrides persistence
    RUNTIME_CONFIG_PATH = 'data/runtime_config.json'
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get the appropriate API URL based on testnet setting"""
        return cls.BINANCE_TESTNET_URL if cls.USE_TESTNET else cls.BINANCE_BASE_URL
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration parameters"""
        if not cls.USE_TESTNET:
            if not cls.BINANCE_API_KEY or not cls.BINANCE_API_SECRET:
                raise ValueError("API credentials required for live trading")
        
        if cls.MIN_PROFIT_THRESHOLD < 0:
            raise ValueError("MIN_PROFIT_THRESHOLD must be positive")
        
        if cls.INITIAL_CAPITAL <= 0:
            raise ValueError("INITIAL_CAPITAL must be positive")
        
        return True

    # ---- Runtime overrides (persist settings toggled via API/UI) ----
    @classmethod
    def _load_runtime_overrides(cls) -> None:
        try:
            path = Path(cls.RUNTIME_CONFIG_PATH)
            if path.exists():
                data = json.loads(path.read_text())
                if isinstance(data, dict):
                    if 'use_testnet' in data:
                        cls.USE_TESTNET = bool(data['use_testnet'])
                    if 'use_websocket' in data:
                        cls.USE_WEBSOCKET = bool(data['use_websocket'])
        except Exception:
            # Ignore and use defaults
            pass

    @classmethod
    def save_runtime_overrides(cls, **kwargs) -> bool:
        """Persist selected config flags to disk (e.g., use_testnet, use_websocket)."""
        try:
            # Load existing
            data = {}
            path = Path(cls.RUNTIME_CONFIG_PATH)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                try:
                    data = json.loads(path.read_text()) or {}
                except Exception:
                    data = {}
            # Apply and write
            for k, v in kwargs.items():
                if k in ('use_testnet', 'use_websocket'):
                    data[k] = bool(v)
            path.write_text(json.dumps(data))
            return True
        except Exception:
            return False

# Load persisted overrides at import time
try:
    Config._load_runtime_overrides()
except Exception:
    pass
