"""
Simple backtesting runner for the triangular arbitrage calculator.
- Loads price snapshots from a JSON file or fetches current prices once.
- Evaluates configured triangles and prints top opportunities per snapshot.

Usage:
  python backtest.py --prices-file data/prices.json
  # or
  python backtest.py --live-once

prices.json format (array of snapshots):
[
  {"timestamp": 1696523000, "prices": {"BTCUSDT": 68000.1, "ETHUSDT": 3150.2, "ETHBTC": 0.04635}},
  ...
]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

from calculator import ArbitrageCalculator
from config import Config
from exchange import BinanceExchange


def run_with_prices(prices: Dict[str, float]):
    calc = ArbitrageCalculator()
    opps = calc.find_all_opportunities(Config.TRADING_TRIANGLES, prices, Config.INITIAL_CAPITAL)
    print(f"Found {len(opps)} opportunities")
    for i, opp in enumerate(opps[:5], 1):
        path = ' -> '.join(opp['triangle']['path'])
        print(f"{i}. {path}: {opp['profit']:.2f} USDT ({opp['profit_percent']:.2f}%)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prices-file', type=str, help='Path to JSON file with snapshots')
    ap.add_argument('--live-once', action='store_true', help='Fetch current prices once and evaluate')
    args = ap.parse_args()

    if args.prices_file:
        p = Path(args.prices_file)
        if not p.exists():
            print(f"File not found: {p}")
            return
        snapshots = json.loads(p.read_text())
        for snap in snapshots:
            ts = snap.get('timestamp')
            prices = snap.get('prices', {})
            print(f"\nSnapshot @ {ts}:")
            run_with_prices(prices)
    else:
        # Default to live-once if requested or no file provided
        ex = BinanceExchange()
        prices = ex.get_all_ticker_prices() or {}
        if not prices:
            print("Failed to fetch prices")
            return
        run_with_prices(prices)


if __name__ == '__main__':
    main()
