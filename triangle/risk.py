"""
Risk management module for Triangular Arbitrage Bot
Enforces operational, strategic and execution risk controls.
"""
from __future__ import annotations

from datetime import datetime, timezone
import time
import json
from pathlib import Path
from typing import Dict, Optional

from logger import logger
from config import Config
from database import TradeDatabase


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskManager:
    """Centralized risk controls and trading guards.

    Responsibilities:
    - Enforce daily/weekly/monthly loss limits and trade-count limits
    - Enforce cooldowns after losses and consecutive loss pauses
    - Provide go/no-go gate before executing a trade
    - Track runtime state (consecutive losses, last loss time, pauses)
    """

    def __init__(self, db: Optional[TradeDatabase] = None):
        self.db = db or TradeDatabase()
        self._paused_until_ts: float = 0.0
        self._consecutive_losses: int = 0
        self._last_trade_pnl: float = 0.0
        self._last_loss_ts: float = 0.0
        self._state_path = Path(Config.RISK_STATE_PATH)
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    # ---- State helpers ----
    def _today_bounds(self) -> tuple[str, str]:
        # Use UTC day bounds to be consistent
        now = _utc_now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=999000)
        return (day_start.isoformat(), day_end.isoformat())

    # ---- Public API ----
    def is_paused(self) -> bool:
        return time.time() < self._paused_until_ts

    def pause_for(self, seconds: float, reason: str):
        self._paused_until_ts = max(self._paused_until_ts, time.time() + max(0.0, seconds))
        logger.warning(f"⏸️ Trading paused for {seconds:.0f}s - {reason}")
        self._save_state()

    def should_trade_now(self) -> tuple[bool, str | None]:
        # Pause gate
        if self.is_paused():
            return False, "Paused by risk manager"

        # Daily loss limit gate
        daily_pnl = self.db.get_pnl_between(*self._today_bounds())
        equity = Config.INITIAL_CAPITAL + daily_pnl
        if Config.DAILY_MAX_LOSS_PCT > 0:
            max_loss = Config.INITIAL_CAPITAL * (Config.DAILY_MAX_LOSS_PCT / 100.0)
            if -daily_pnl >= max_loss:
                return False, f"Daily loss limit hit ({-daily_pnl:.2f} >= {max_loss:.2f})"

        # Trade frequency gate
        trades_today = self.db.get_trade_count_between(*self._today_bounds())
        if Config.MAX_TRADES_PER_DAY > 0 and trades_today >= Config.MAX_TRADES_PER_DAY:
            return False, "Max trades per day reached"

        # Cooldown after loss
        if self._last_loss_ts and Config.LOSS_COOLDOWN_SEC > 0:
            remaining = (self._last_loss_ts + Config.LOSS_COOLDOWN_SEC) - time.time()
            if remaining > 0:
                return False, f"Cooling down after loss ({remaining:.0f}s remaining)"

        # Consecutive loss limit
        if Config.MAX_CONSECUTIVE_LOSSES > 0 and self._consecutive_losses >= Config.MAX_CONSECUTIVE_LOSSES:
            return False, "Max consecutive losses reached"

        return True, None

    def on_trade_result(self, profit: float):
        """Update risk state after each executed trade."""
        self._last_trade_pnl = profit
        if profit < 0:
            self._consecutive_losses += 1
            self._last_loss_ts = time.time()
            # Auto-pause tiers based on losses
            if self._consecutive_losses == 1 and Config.LOSS_COOLDOWN_SEC > 0:
                self.pause_for(Config.LOSS_COOLDOWN_SEC, "single loss cooldown")
            elif self._consecutive_losses == 2 and Config.COOLDOWN_AFTER_2_LOSSES_SEC > 0:
                self.pause_for(Config.COOLDOWN_AFTER_2_LOSSES_SEC, "two consecutive losses")
            elif self._consecutive_losses >= 3 and Config.COOLDOWN_AFTER_3_LOSSES_SEC > 0:
                self.pause_for(Config.COOLDOWN_AFTER_3_LOSSES_SEC, "three consecutive losses")
        else:
            # Reset loss streak after a win
            self._consecutive_losses = 0

        # Daily stop check (in case external trades affected pnl)
        daily_pnl = self.db.get_pnl_between(*self._today_bounds())
        if Config.DAILY_MAX_LOSS_PCT > 0:
            max_loss = Config.INITIAL_CAPITAL * (Config.DAILY_MAX_LOSS_PCT / 100.0)
            if -daily_pnl >= max_loss:
                self.pause_for(Config.DAILY_STOP_RESUME_DELAY_SEC, "daily loss limit reached")
        self._save_state()

    # ---- Opportunity gating helpers ----
    def adjust_profit_threshold(self, base_threshold_pct: float) -> float:
        """Optionally adjust threshold based on simple conditions (placeholder)."""
        # Could integrate volatility regime here; keep simple for now
        return max(base_threshold_pct, Config.MIN_PROFIT_THRESHOLD)

    def min_fill_ratio_ok(self, fill_ratio: float) -> bool:
        return fill_ratio >= Config.MIN_FILL_RATIO

    def api_error_rate_trigger(self, error_rate: float) -> bool:
        if error_rate >= Config.API_ERROR_RATE_PAUSE_THRESHOLD:
            self.pause_for(Config.API_ERROR_PAUSE_SEC, f"API error rate {error_rate:.1%} >= threshold")
            return True
        return False

    # ---- Persistence and views ----
    def _load_state(self):
        try:
            if self._state_path.exists():
                data = json.load(self._state_path.open('r'))
                self._paused_until_ts = float(data.get('paused_until_ts', 0.0))
                self._consecutive_losses = int(data.get('consecutive_losses', 0))
                self._last_trade_pnl = float(data.get('last_trade_pnl', 0.0))
                self._last_loss_ts = float(data.get('last_loss_ts', 0.0))
        except Exception as e:
            logger.error(f"Failed to load risk state: {e}")

    def _save_state(self):
        try:
            tmp = {
                'paused_until_ts': self._paused_until_ts,
                'consecutive_losses': self._consecutive_losses,
                'last_trade_pnl': self._last_trade_pnl,
                'last_loss_ts': self._last_loss_ts,
                'saved_at': time.time(),
            }
            with self._state_path.open('w') as f:
                json.dump(tmp, f)
        except Exception as e:
            logger.error(f"Failed to save risk state: {e}")

    def get_state(self) -> Dict:
        """Return a snapshot of current risk state including daily stats."""
        day_start, day_end = self._today_bounds()
        daily_pnl = self.db.get_pnl_between(day_start, day_end)
        trades_today = self.db.get_trade_count_between(day_start, day_end)
        return {
            'paused': self.is_paused(),
            'paused_until_ts': self._paused_until_ts,
            'consecutive_losses': self._consecutive_losses,
            'last_trade_pnl': self._last_trade_pnl,
            'last_loss_ts': self._last_loss_ts,
            'daily_pnl': daily_pnl,
            'trades_today': trades_today,
            'config': {
                'daily_max_loss_pct': Config.DAILY_MAX_LOSS_PCT,
                'max_trades_per_day': Config.MAX_TRADES_PER_DAY,
                'max_consecutive_losses': Config.MAX_CONSECUTIVE_LOSSES,
            }
        }

