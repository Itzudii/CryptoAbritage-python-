"""
Configuration module for Triangular Arbitrage Bot
Stores all configuration parameters and API credentials
"""

import os
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
    USE_TESTNET = True  # Set to False for live trading
    INITIAL_CAPITAL = 1000  # Starting capital in USDT
    MIN_PROFIT_THRESHOLD = 0.5  # Minimum profit % to execute trade
    MAX_TRADE_SIZE = 5000  # Maximum trade size in USDT
    
    # Fee Configuration
    MAKER_FEE = 0.001  # 0.1%
    TAKER_FEE = 0.001  # 0.1%
    
    # Risk Management
    MAX_SLIPPAGE = 0.002  # 0.2% max slippage tolerance
    STOP_LOSS_PERCENT = 2.0  # Stop if losses exceed this %
    
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
