"""
Database module for storing trade history and analytics
Uses SQLite for lightweight, embedded storage
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from config import Config

class TradeDatabase:
    """Manage trade history database"""
    
    def __init__(self):
        self.db_path = Config.DB_PATH
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Create database directory if it doesn't exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Create tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                triangle_path TEXT NOT NULL,
                pairs TEXT NOT NULL,
                initial_amount REAL NOT NULL,
                final_amount REAL NOT NULL,
                profit REAL NOT NULL,
                profit_percent REAL NOT NULL,
                executed BOOLEAN NOT NULL,
                execution_time REAL,
                error_message TEXT,
                steps_data TEXT
            )
        ''')
        
        # Opportunities table (for tracking detected but not executed)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                triangle_path TEXT NOT NULL,
                expected_profit REAL NOT NULL,
                profit_percent REAL NOT NULL,
                reason_not_executed TEXT
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_trades INTEGER,
                successful_trades INTEGER,
                failed_trades INTEGER,
                total_profit REAL,
                avg_profit_per_trade REAL,
                uptime_seconds REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def save_trade(self, trade_data: Dict) -> int:
        """Save executed trade to database"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        triangle = trade_data.get('triangle', {})
        path = ' -> '.join(triangle.get('path', []))
        pairs = ', '.join(triangle.get('pairs', []))
        
        cursor.execute('''
            INSERT INTO trades (
                triangle_path, pairs, initial_amount, final_amount,
                profit, profit_percent, executed, execution_time,
                error_message, steps_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            path,
            pairs,
            trade_data.get('initial_amount', 0),
            trade_data.get('final_amount', 0),
            trade_data.get('profit', 0),
            trade_data.get('profit_percent', 0),
            trade_data.get('success', False),
            trade_data.get('execution_time', 0),
            trade_data.get('error', None),
            json.dumps(trade_data.get('steps_executed', []))
        ))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return trade_id
    
    def save_opportunity(self, opportunity: Dict, reason: str = None):
        """Save detected opportunity"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        triangle = opportunity.get('triangle', {})
        path = ' -> '.join(triangle.get('path', []))
        
        cursor.execute('''
            INSERT INTO opportunities (
                triangle_path, expected_profit, profit_percent,
                reason_not_executed
            ) VALUES (?, ?, ?, ?)
        ''', (
            path,
            opportunity.get('profit', 0),
            opportunity.get('profit_percent', 0),
            reason
        ))
        
        conn.commit()
        conn.close()
    
    def save_metrics(self, metrics: Dict):
        """Save performance metrics snapshot"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO metrics (
                total_trades, successful_trades, failed_trades,
                total_profit, avg_profit_per_trade, uptime_seconds
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            metrics.get('total_trades', 0),
            metrics.get('successful_trades', 0),
            metrics.get('failed_trades', 0),
            metrics.get('total_profit', 0),
            metrics.get('avg_profit_per_trade', 0),
            metrics.get('uptime_seconds', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def get_all_trades(self, limit: int = 100) -> List[Dict]:
        """Retrieve trade history"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return trades
    
    def get_recent_opportunities(self, limit: int = 100) -> List[Dict]:
        """Retrieve recent detected opportunities"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM opportunities
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        opportunities = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return opportunities
    
    def get_profitable_trades(self) -> List[Dict]:
        """Get only profitable trades"""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trades
            WHERE executed = 1 AND profit > 0
            ORDER BY profit DESC
        ''')
        
        trades = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return trades
    
    def get_statistics(self) -> Dict:
        """Get overall trading statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Total trades
        cursor.execute('SELECT COUNT(*) FROM trades WHERE executed = 1')
        total_trades = cursor.fetchone()[0]
        
        # Successful trades
        cursor.execute('SELECT COUNT(*) FROM trades WHERE executed = 1 AND profit > 0')
        profitable_trades = cursor.fetchone()[0]
        
        # Total profit
        cursor.execute('SELECT SUM(profit) FROM trades WHERE executed = 1')
        total_profit = cursor.fetchone()[0] or 0
        
        # Average profit
        cursor.execute('SELECT AVG(profit) FROM trades WHERE executed = 1')
        avg_profit = cursor.fetchone()[0] or 0
        
        # Best trade
        cursor.execute('SELECT MAX(profit) FROM trades WHERE executed = 1')
        best_trade = cursor.fetchone()[0] or 0
        
        # Worst trade
        cursor.execute('SELECT MIN(profit) FROM trades WHERE executed = 1')
        worst_trade = cursor.fetchone()[0] or 0
        
        # Total opportunities detected
        cursor.execute('SELECT COUNT(*) FROM opportunities')
        total_opportunities = cursor.fetchone()[0]
        
        conn.close()
        
        success_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'success_rate': success_rate,
            'total_profit': total_profit,
            'avg_profit': avg_profit,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'total_opportunities': total_opportunities
        }
    
    # ---- Risk analytics helpers ----
    def get_pnl_between(self, start_iso: str, end_iso: str) -> float:
        """Return realized P&L between start and end timestamps (ISO8601 UTC strings)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COALESCE(SUM(profit), 0) FROM trades
            WHERE executed = 1 AND timestamp BETWEEN ? AND ?
            ''',
            (start_iso, end_iso),
        )
        total = cursor.fetchone()[0] or 0.0
        conn.close()
        return float(total)

    def get_trade_count_between(self, start_iso: str, end_iso: str) -> int:
        """Return count of executed trades between start and end timestamps."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT COUNT(*) FROM trades
            WHERE executed = 1 AND timestamp BETWEEN ? AND ?
            ''',
            (start_iso, end_iso),
        )
        count = int(cursor.fetchone()[0] or 0)
        conn.close()
        return count
    
    def clear_old_data(self, days: int = 30):
        """Clear data older than specified days"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM trades
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        cursor.execute('''
            DELETE FROM opportunities
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted_trades = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_trades
