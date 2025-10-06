"""
Main entry point for Triangular Arbitrage Bot
Run this file to start the bot
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from logger import logger
from bot import ArbitrageBot

def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Triangular Arbitrage Trading Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in dry-run mode (simulation, no real trades)
  python main.py --dry-run

  # Run live trading (DANGER: uses real money!)
  python main.py --live

  # Test connection only
  python main.py --test

  # Run single scan
  python main.py --scan

  # Show statistics
  python main.py --stats
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in simulation mode (no real trades)'
    )
    
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in live trading mode (USES REAL MONEY!)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test exchange connection and exit'
    )
    
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Run single opportunity scan and exit'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show trading statistics and exit'
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Determine run mode
    if args.live and args.dry_run:
        logger.error("Cannot specify both --live and --dry-run")
        sys.exit(1)
    
    # Default to dry-run if neither specified
    if not args.live and not args.dry_run and not args.test and not args.scan and not args.stats:
        args.dry_run = True
        logger.info("No mode specified, defaulting to --dry-run")
    
    # Initialize bot
    bot = ArbitrageBot(dry_run=args.dry_run or not args.live)
    
    # Handle different modes
    if args.test:
        logger.info("Running connection test...")
        if bot.test_connection():
            logger.info("✅ Connection test passed!")
            sys.exit(0)
        else:
            logger.error("❌ Connection test failed!")
            sys.exit(1)
    
    elif args.scan:
        bot.run_single_scan()
        sys.exit(0)
    
    elif args.stats:
        show_statistics(bot)
        sys.exit(0)
    
    else:
        # Warn if live trading
        if args.live:
            logger.warning("=" * 60)
            logger.warning("⚠️  LIVE TRADING MODE ENABLED")
            logger.warning("⚠️  THIS WILL USE REAL MONEY!")
            logger.warning("=" * 60)
            
            response = input("Are you absolutely sure? Type 'YES' to continue: ")
            if response != 'YES':
                logger.info("Live trading cancelled")
                sys.exit(0)
        
        # Start the bot
        try:
            bot.start()
        except KeyboardInterrupt:
            logger.info("\nKeyboard interrupt received")
            bot.stop()
        except Exception as e:
            logger.critical(f"Unhandled exception: {e}")
            bot.stop()
            sys.exit(1)

def show_statistics(bot: ArbitrageBot):
    """Show trading statistics"""
    from database import TradeDatabase
    
    db = TradeDatabase()
    stats = db.get_statistics()
    
    print("\n" + "=" * 60)
    print("📊 TRADING STATISTICS")
    print("=" * 60)
    print(f"Total trades executed: {stats['total_trades']}")
    print(f"Profitable trades: {stats['profitable_trades']}")
    print(f"Success rate: {stats['success_rate']:.2f}%")
    print(f"Total profit: {stats['total_profit']:.2f} USDT")
    print(f"Average profit per trade: {stats['avg_profit']:.2f} USDT")
    print(f"Best trade: {stats['best_trade']:.2f} USDT")
    print(f"Worst trade: {stats['worst_trade']:.2f} USDT")
    print(f"Total opportunities detected: {stats['total_opportunities']}")
    print("=" * 60)
    
    # Show recent trades
    trades = db.get_all_trades(limit=10)
    if trades:
        print("\n📜 RECENT TRADES (Last 10):")
        print("-" * 60)
        for trade in trades:
            status = "✅" if trade['executed'] and trade['profit'] > 0 else "❌"
            print(f"{status} {trade['timestamp']} | {trade['triangle_path']}")
            print(f"   Profit: {trade['profit']:.2f} USDT ({trade['profit_percent']:.2f}%)")
        print("-" * 60)

if __name__ == '__main__':
    main()
