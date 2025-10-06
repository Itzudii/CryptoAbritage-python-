import threading
import time
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from bot import ArbitrageBot
from database import TradeDatabase
from config import Config
from exchange import BinanceExchange
from calculator import ArbitrageCalculator

app = FastAPI(title="Triangular Arbitrage Bot API", version="1.0.0")

# Allow local dev UIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.API_ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend at /ui
app.mount("/ui", StaticFiles(directory="web/static", html=True), name="static")

@app.get("/")
def root_redirect():
    return RedirectResponse(url="/ui/")


def _safe_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return dict(d)
    except Exception:
        return {}


from fastapi import Header, HTTPException


def require_dashboard_api_key(x_api_key: str | None = Header(default=None)):
    if Config.DASHBOARD_API_KEY:
        if not x_api_key or x_api_key != Config.DASHBOARD_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


class BotManager:
    def __init__(self):
        self._bot: ArbitrageBot | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._running = False

    def status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "mode": "DRY_RUN" if (self._bot and self._bot.dry_run) else ("LIVE" if self._bot else None),
                "iteration_count": getattr(self._bot, "iteration_count", 0) if self._bot else 0,
                "opportunities_found": getattr(self._bot, "opportunities_found", 0) if self._bot else 0,
                "trades_executed": getattr(self._bot, "trades_executed", 0) if self._bot else 0,
            }

    def start(self, dry_run: bool = True) -> bool:
        with self._lock:
            if self._running:
                return False
            self._bot = ArbitrageBot(dry_run=dry_run)
            self._thread = threading.Thread(target=self._bot.start, daemon=True)
            self._thread.start()
            self._running = True
            return True

    def stop(self) -> bool:
        with self._lock:
            if not self._running or not self._bot:
                return False
            self._bot.stop()
            self._running = False
            return True


bot_manager = BotManager()
db = TradeDatabase()


@app.get("/api/status")
def get_status():
    return bot_manager.status()


@app.post("/api/start")
def start_bot(dry_run: bool = True, _=require_dashboard_api_key()):
    started = bot_manager.start(dry_run=dry_run)
    return {"started": started, **bot_manager.status()}


@app.post("/api/stop")
def stop_bot(_=require_dashboard_api_key()):
    stopped = bot_manager.stop()
    return {"stopped": stopped, **bot_manager.status()}


@app.get("/api/stats")
def get_stats():
    stats = db.get_statistics()
    return _safe_dict(stats)


@app.get("/api/trades")
def get_trades(limit: int = 50):
    return db.get_all_trades(limit=limit)


@app.get("/api/opportunities")
def get_opportunities(limit: int = 50):
    return db.get_recent_opportunities(limit=limit)


@app.get("/api/scan")
def on_demand_scan():
    # Run a single scan and return current opportunities without starting the bot
    exchange = BinanceExchange()
    calc = ArbitrageCalculator()
    prices = exchange.get_all_ticker_prices()
    if not prices:
        return {"ok": False, "error": "Failed to fetch prices"}
    opportunities = calc.find_all_opportunities(Config.TRADING_TRIANGLES, prices, Config.INITIAL_CAPITAL)
    return {"ok": True, "count": len(opportunities), "opportunities": opportunities[:10]}


@app.get("/api/wallet")
def get_wallet():
    """Return account balances and total portfolio value in USDT."""
    exchange = BinanceExchange()
    account = exchange.get_account_info() or {}
    balances = account.get("balances", [])
    # Fetch prices for conversion
    prices = exchange.get_all_ticker_prices() or {}
    total_usdt = 0.0
    items: list[dict[str, Any]] = []
    for b in balances:
        asset = b.get("asset")
        free = float(b.get("free", 0))
        locked = float(b.get("locked", 0))
        amount = free + locked
        if amount <= 0:
            continue
        value_usdt = 0.0
        if asset == "USDT":
            value_usdt = amount
        else:
            sym1 = f"{asset}USDT"
            sym2 = f"USDT{asset}"
            price = None
            if sym1 in prices:
                price = prices.get(sym1)
                value_usdt = amount * float(price)
            elif sym2 in prices and prices.get(sym2):
                price = prices.get(sym2)
                # sym2 is USDT per asset inverted; to get asset->USDT we divide
                try:
                    value_usdt = amount / float(price)
                except Exception:
                    value_usdt = 0.0
        total_usdt += value_usdt
        items.append({
            "asset": asset,
            "free": free,
            "locked": locked,
            "value_usdt": value_usdt,
        })
    # Sort by value desc
    items.sort(key=lambda x: x["value_usdt"], reverse=True)
    return {"total_value_usdt": total_usdt, "balances": items}


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    await ws.accept()
    try:
        # If bot not running, provide continuous data via periodic scans
        exchange = BinanceExchange()
        calc = ArbitrageCalculator()
        while True:
            status = bot_manager.status()
            payload: Dict[str, Any] = {"type": "status", "data": status}
            await ws.send_json(payload)

            # Send recent DB updates
            recent_trades = db.get_all_trades(limit=10)
            recent_opps = db.get_recent_opportunities(limit=10)
            await ws.send_json({"type": "trades", "data": recent_trades})
            await ws.send_json({"type": "opportunities", "data": recent_opps})

            # If bot is not running, do a lightweight scan to provide fresh data
            if not status.get("running"):
                prices = exchange.get_all_ticker_prices() or {}
                if prices:
                    opps = calc.find_all_opportunities(Config.TRADING_TRIANGLES, prices, Config.INITIAL_CAPITAL)
                    await ws.send_json({
                        "type": "scan",
                        "data": {
                            "timestamp": time.time(),
                            "count": len(opps),
                            "opportunities": opps[:10],
                        },
                    })
            # Throttle updates
            await ws.receive_text(timeout=0.0) if False else None  # no-op for starlette compatibility
            await asyncio_sleep(1.0)
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# Simple asyncio sleep helper without importing asyncio at top-level if not needed
import asyncio


async def asyncio_sleep(sec: float):
    await asyncio.sleep(sec)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.api:app", host="0.0.0.0", port=8000, reload=False)
