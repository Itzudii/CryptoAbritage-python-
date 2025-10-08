"""
Main bot controller
Orchestrates all components and runs the arbitrage detection loop
"""

import time
import signal
import sys
import threading
from typing import Dict, List
from datetime import datetime

from config import Config
from logger import logger
from exchange import BinanceExchange
from calculator import ArbitrageCalculator
from trader import TradeExecutor
from database import TradeDatabase
from market_data import market_data
from risk import RiskManager

class ArbitrageBot:
    """Main arbitrage bot controller"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.running = False
        self.start_time = None
        
        # Initialize components
        logger.info("Initializing Arbitrage Bot...")
        
        self.exchange = BinanceExchange()
        self.calculator = ArbitrageCalculator()
        self.trader = TradeExecutor(self.exchange)
        self.database = TradeDatabase()
        self.risk = RiskManager(self.database)
        # Start WS market data if enabled
        if Config.USE_WEBSOCKET:
            market_data.start()
        
        # Statistics
        self.opportunities_found = 0
        self.trades_executed = 0
        self.iteration_count = 0
        
        # Signal handling for graceful shutdown
        # Only register OS signal handlers when running in the main thread.
        # When started from the FastAPI app, the bot runs in a background thread
        # and registering signal handlers raises: ValueError: signal only works in main thread
        try:
            if threading.current_thread() is threading.main_thread():
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            else:
                logger.debug("Skipping signal handlers since not in main thread")
        except Exception:
            # Best-effort: if signals can't be registered (e.g., on certain platforms), continue
            logger.debug("Signal handler registration skipped due to environment")
        
        logger.info("✅ Bot initialized successfully")
        logger.info(f"Mode: {'DRY RUN (Simulation)' if dry_run else 'LIVE TRADING'}")
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info("\n🛑 Shutdown signal received. Stopping bot...")
        self.stop()
    
    def start(self):
        """Start the arbitrage bot"""
        if self.running:
            logger.warning("Bot is already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("🚀 ARBITRAGE BOT STARTED")
        logger.info("=" * 60)
        logger.info(f"Monitoring {len(Config.TRADING_TRIANGLES)} triangular paths")
        logger.info(f"Min profit threshold: {Config.MIN_PROFIT_THRESHOLD}%")
        logger.info(f"Initial capital: {Config.INITIAL_CAPITAL} USDT")
        logger.info("=" * 60)
        
        try:
            self._run_main_loop()
        except Exception as e:
            logger.critical(f"Fatal error in main loop: {e}")
            self.stop()
    
    def _run_main_loop(self):
        """Main bot loop"""
        while self.running:
            try:
                self.iteration_count += 1
                loop_start = time.time()
                
                # Fetch all prices at once (prefer WS cache if available)
                prices = market_data.get_all_prices() if Config.USE_WEBSOCKET else {}
                if not prices:
                    prices = self.exchange.get_all_ticker_prices()
                
                if not prices:
                    logger.warning("Failed to fetch prices, retrying...")
                    time.sleep(Config.UPDATE_INTERVAL)
                    continue

                # API error-rate telemetry gate
                try:
                    err_rate = self.exchange.get_error_rate()
                    if self.risk.api_error_rate_trigger(err_rate):
                        logger.warning(f"Risk pause triggered by API error rate: {err_rate:.1%}")
                        # Skip execution when API is unhealthy
                        time.sleep(Config.UPDATE_INTERVAL)
                        continue
                except Exception:
                    pass
                
                # Find arbitrage opportunities
                opportunities = self.calculator.find_all_opportunities(
                    Config.TRADING_TRIANGLES,
                    prices,
                    Config.INITIAL_CAPITAL
                )
                
                if opportunities:
                    self.opportunities_found += len(opportunities)
                    
                    for opp in opportunities:
                        logger.log_opportunity(
                            opp['triangle'],
                            opp['profit'],
                            opp['profit_percent']
                        )
                        
                        # Save opportunity to database
                        self.database.save_opportunity(opp)
                        
                        # Execute the most profitable opportunity
                        if opp == opportunities[0]:  # Best opportunity
                            self._handle_opportunity(opp)
                
                # Print status every 100 iterations
                if self.iteration_count % 100 == 0:
                    self._print_status()
                
                # Rate limiting
                loop_time = time.time() - loop_start
                sleep_time = max(0, Config.UPDATE_INTERVAL - loop_time)
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(Config.UPDATE_INTERVAL)
    
    def _handle_opportunity(self, opportunity: Dict):
        """Handle a detected arbitrage opportunity"""
        
        # Profit threshold gate (static)
        if opportunity['profit_percent'] < Config.MIN_PROFIT_THRESHOLD:
            logger.debug(f"Profit below threshold: {opportunity['profit_percent']:.2f}%")
            # record skipped opportunity with reason
            try:
                self.database.save_opportunity(opportunity, reason="below_threshold")
            except Exception:
                pass
            return

        # Risk manager gate (daily stop, cooldowns, trade caps)
        ok, reason = self.risk.should_trade_now()
        if not ok:
            logger.warning(f"Skipping trade due to risk gate: {reason}")
            try:
                self.database.save_opportunity(opportunity, reason=reason)
            except Exception:
                pass
            return
        
        # Execute trade (or simulate in dry run mode)
        if self.dry_run:
            result = self.trader.dry_run_execute(opportunity)
        else:
            result = self.trader.execute_triangle(opportunity)
        
        # Save to database
        # Prefer actual execution PnL when available
        executed_profit = None
        if not self.dry_run:
            executed_profit = result.get('total_profit')
        # Fallbacks
        if executed_profit is None:
            executed_profit = opportunity.get('profit', 0.0)
        final_amount = float(opportunity.get('initial_amount', 0.0)) + float(executed_profit)

        trade_data = {
            'triangle': opportunity['triangle'],
            'initial_amount': opportunity.get('initial_amount', 0.0),
            'final_amount': final_amount,
            'profit': executed_profit,
            'profit_percent': (executed_profit / max(opportunity.get('initial_amount', 1.0), 1e-9)) * 100.0,
            'success': bool(result.get('success', False) and not self.dry_run),
            'execution_time': result.get('execution_time', 0),
            'error': result.get('error'),
            'steps_executed': result.get('steps_executed', [])
        }
        
        self.database.save_trade(trade_data)
        
        if result.get('success'):
            self.trades_executed += 1
            # Update risk state only for live trades
            if not self.dry_run:
                try:
                    self.risk.on_trade_result(float(executed_profit))
                except Exception:
                    pass
    
    def _print_status(self):
        """Print bot status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        stats = self.trader.get_statistics()
        
        logger.info("=" * 60)
        logger.info(f"📊 BOT STATUS - Iteration #{self.iteration_count}")
        logger.info(f"⏱️  Uptime: {uptime/60:.1f} minutes")
        logger.info(f"🔍 Opportunities found: {self.opportunities_found}")
        logger.info(f"💰 Trades executed: {self.trades_executed}")
        logger.info(f"📈 Total profit: {stats['total_profit']:.2f} USDT")
        logger.info(f"✅ Success rate: {stats['success_rate']:.1f}%")
        logger.info("=" * 60)
    
    def stop(self):
        """Stop the bot gracefully"""
        if not self.running:
            return
        
        self.running = False
        
        logger.info("=" * 60)
        logger.info("🛑 STOPPING BOT")
        logger.info("=" * 60)
        
        # Print final statistics
        self._print_final_stats()
        
        logger.info("Bot stopped successfully")
    
    def _print_final_stats(self):
        """Print final statistics before shutdown"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        stats = self.trader.get_statistics()
        db_stats = self.database.get_statistics()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total runtime: {uptime/3600:.2f} hours")
        logger.info(f"Total iterations: {self.iteration_count}")
        logger.info(f"Opportunities detected: {db_stats['total_opportunities']}")
        logger.info(f"Trades executed: {db_stats['total_trades']}")
        logger.info(f"Profitable trades: {db_stats['profitable_trades']}")
        logger.info(f"Success rate: {db_stats['success_rate']:.2f}%")
        logger.info(f"Total profit: {db_stats['total_profit']:.2f} USDT")
        logger.info(f"Average profit per trade: {db_stats['avg_profit']:.2f} USDT")
        logger.info(f"Best trade: {db_stats['best_trade']:.2f} USDT")
        logger.info(f"Worst trade: {db_stats['worst_trade']:.2f} USDT")
        logger.info("=" * 60)
        
        # Save final metrics to database
        metrics = {
            'total_trades': db_stats['total_trades'],
            'successful_trades': db_stats['profitable_trades'],
            'failed_trades': db_stats['total_trades'] - db_stats['profitable_trades'],
            'total_profit': db_stats['total_profit'],
            'avg_profit_per_trade': db_stats['avg_profit'],
            'uptime_seconds': uptime
        }
        self.database.save_metrics(metrics)
    
    def get_risk_state(self) -> dict:
        """Expose current risk state for APIs and dashboards."""
        try:
            return self.risk.get_state()
        except Exception:
            return {"paused": False}
    
    def test_connection(self) -> bool:
        """Test exchange connection"""
        logger.info("Testing exchange connection...")
        
        try:
            prices = market_data.get_all_prices() if Config.USE_WEBSOCKET else {}
            if not prices:
                prices = self.exchange.get_all_ticker_prices()
            if prices:
                logger.info(f"✅ Successfully fetched {len(prices)} ticker prices")
                return True
            else:
                logger.error("❌ Failed to fetch prices")
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False
    
    def run_single_scan(self):
        """Run a single scan for opportunities (useful for testing)"""
        logger.info("Running single opportunity scan...")
        
        prices = market_data.get_all_prices() if Config.USE_WEBSOCKET else {}
        if not prices:
            prices = self.exchange.get_all_ticker_prices()
        
        if not prices:
            logger.error("Failed to fetch prices")
            return
        
        opportunities = self.calculator.find_all_opportunities(
            Config.TRADING_TRIANGLES,
            prices,
            Config.INITIAL_CAPITAL
        )
        
        if opportunities:
            logger.info(f"Found {len(opportunities)} opportunities:")
            for i, opp in enumerate(opportunities, 1):
                path = ' -> '.join(opp['triangle']['path'])
                logger.info(f"{i}. {path}: {opp['profit']:.2f} USDT ({opp['profit_percent']:.2f}%)")
        else:
            logger.info("No profitable opportunities found")
