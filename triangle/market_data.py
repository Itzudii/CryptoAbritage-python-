"""
Real-time market data via Binance WebSocket.
Maintains a price cache for all symbols using the !bookTicker stream.
Falls back gracefully if connection drops.
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Dict, Optional

import websockets

from config import Config
from logger import logger


class MarketData:
    _instance: "MarketData" | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._prices: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._ws_thread: threading.Thread | None = None
        self._running = False
        self._last_msg_ts: float = 0.0
        self._reconnects: int = 0

    def start(self):
        if self._running or not Config.USE_WEBSOCKET:
            return
        self._running = True
        self._ws_thread = threading.Thread(target=self._run_ws_loop, daemon=True)
        self._ws_thread.start()
        logger.info("📡 MarketData WebSocket started")

    def stop(self):
        self._running = False

    def get_all_prices(self) -> Dict[str, float]:
        with self._lock:
            return dict(self._prices)

    def get_health(self) -> Dict[str, float | int | bool]:
        from time import time as _now
        return {
            "running": self._running,
            "last_message_age_sec": max(0.0, _now() - self._last_msg_ts) if self._last_msg_ts else None,
            "reconnects": self._reconnects,
            "cached_symbols": len(self._prices),
        }

    def _run_ws_loop(self):
        asyncio.run(self._ws_loop())

    async def _ws_loop(self):
        # Build endpoint for all book tickers: stream name is !bookTicker
        ws_base = Config.BINANCE_WS_TESTNET if Config.USE_TESTNET else Config.BINANCE_WS_MAINNET
        # Use combined stream path when available
        # Binance supports endpoint: wss://stream.binance.com:9443/ws/!bookTicker
        # Testnet follows the same pattern
        if ws_base.endswith("/ws"):
            url = f"{ws_base}/!bookTicker"
        else:
            url = f"{ws_base}/ws/!bookTicker"

        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                    logger.info(f"Connected to Binance WS: {url}")
                    while self._running:
                        msg = await ws.recv()
                        try:
                            data = json.loads(msg)
                        except Exception:
                            continue
                        # Book ticker payload fields: s (symbol), b (best bid), a (best ask)
                        symbol = data.get("s")
                        if not symbol:
                            # Some servers wrap payload in {stream,data}
                            data = data.get("data", {})
                            symbol = data.get("s")
                        if not symbol:
                            continue
                        bid = float(data.get("b", 0) or 0)
                        ask = float(data.get("a", 0) or 0)
                        price = 0.0
                        if bid and ask:
                            price = (bid + ask) / 2.0
                        elif bid:
                            price = bid
                        elif ask:
                            price = ask
                        if price > 0:
                            with self._lock:
                                self._prices[symbol] = price
                                # health heartbeat
                                import time as _t
                                self._last_msg_ts = _t.time()
            except Exception as e:
                logger.warning(f"WebSocket error: {e}. Reconnecting in 2s...")
                self._reconnects += 1
                await asyncio.sleep(2)


market_data = MarketData()
