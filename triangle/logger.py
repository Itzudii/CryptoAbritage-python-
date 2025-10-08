"""
Logging module for Triangular Arbitrage Bot
Provides structured logging with file and console output
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from config import Config

class Logger:
    """Custom logger class for arbitrage bot"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger('ArbitrageBot')
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # Create logs directory if it doesn't exist
        log_dir = Path(Config.LOG_FILE).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        if Config.LOG_TO_CONSOLE:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """Log critical message"""
        self.logger.critical(message)
    
    def log_opportunity(self, triangle: dict, profit: float, profit_percent: float):
        """Log arbitrage opportunity"""
        path = ' -> '.join(triangle['path'])
        self.info(f"💰 OPPORTUNITY | Path: {path} | Profit: {profit:.2f} USDT ({profit_percent:.2f}%)")
    
    def log_trade(self, triangle: dict, executed: bool, profit: float = None, reason: str = None):
        """Log trade execution"""
        path = ' -> '.join(triangle['path'])
        if executed:
            self.info(f"✅ TRADE EXECUTED | Path: {path} | Profit: {profit:.2f} USDT")
        else:
            self.warning(f"❌ TRADE SKIPPED | Path: {path} | Reason: {reason}")
    
    def log_error_trade(self, triangle: dict, error: str):
        """Log trade error"""
        path = ' -> '.join(triangle['path'])
        self.error(f"🚨 TRADE ERROR | Path: {path} | Error: {error}")

# Create singleton instance
logger = Logger()
