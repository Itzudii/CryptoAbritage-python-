# Managed Risk Factors – Coverage and Implementation Map

This document summarizes the major risk factors from `RISKMANAGEMENT.md`, the specific controls implemented in this codebase, and where they live. It is intended for audits, reviews, and operational handoffs.

## Sources
- Primary design source: `RISKMANAGEMENT.md` (Multi-Layer Defense Architecture; Daily Operating Limits; Operational Safeguards; Incident Response)
- Exchange API: Binance REST (depth, orders)

---

## Tier 1 – Existential Risks (Critical)

- **Execution Timing Risk**
  - Control: Triangle- and leg-level execution timeouts.
  - Where:
    - `trader.py`: enforces `Config.SINGLE_TRADE_TIMEOUT_SEC` per step and `Config.FULL_TRIANGLE_TIMEOUT_SEC` per triangle; attempts best-effort reversal on failure.
    - `config.py`: timeout parameters.
  - Source: RISKMANAGEMENT.md – “Execution Speed Failure”, “Failure Levels”, “Operational Safeguards”.

- **Liquidity Evaporation Risk**
  - Control: Pre-trade order book depth + slippage estimation; minimum fill-ratio enforcement; early abort.
  - Where:
    - `liquidity.py`: `LiquidityChecker` uses `exchange.get_order_book()` to compute depth, VWAP, and estimated slippage vs `Config.MAX_SLIPPAGE`.
    - `exchange.py`: `get_order_book()` implementation for Binance.
    - `trader.py`: enforces `Config.MIN_FILL_RATIO` and aborts/reverses if violated.
  - Source: RISKMANAGEMENT.md – “Order Book Analysis”, “10x Liquidity Rule”, “Flash Crash Detection”.

- **Technical Infrastructure Risk**
  - Control: Fail-fast, pause-on-error hooks; API-rate limiting and timeouts; alerts for critical execution failures.
  - Where:
    - `exchange.py`: internal request limiter and error checks.
    - `notifications.py`: Telegram alerts for critical trade/infra errors.
    - `risk.py`: pause interface for systemic issues (extendable via API error-rate triggers).
  - Source: RISKMANAGEMENT.md – “Technical Failure”, “Degraded Mode Operations”, “Incident Response Procedures”.

---

## Tier 2 – Operational Risks (High)

- **Slippage Accumulation**
  - Control: Pre-trade VWAP slippage estimate; step fill-ratio guard; global max slippage config.
  - Where:
    - `liquidity.py`: estimated slippage calculation.
    - `trader.py`: `MIN_FILL_RATIO` enforcement; logs and alert on partial fills.
    - `config.py`: `MAX_SLIPPAGE`, `MIN_FILL_RATIO`.
  - Source: RISKMANAGEMENT.md – “Slippage Accumulation”, “Operational Safeguards”.

- **Fee Overhead**
  - Control: Fees accounted in profit calcs; thresholds include fee margin.
  - Where:
    - `config.py`: `MAKER_FEE`, `TAKER_FEE` already used by calculator.
    - `calculator.py`: incorporates fees in profitability.
  - Source: RISKMANAGEMENT.md – “Fee Accumulation”, “Maker Preference”.

- **Market Volatility**
  - Control: Execution timeouts, liquidity checks (VWAP), and profit threshold gating.
  - Where:
    - `bot.py`: static `MIN_PROFIT_THRESHOLD` gate before attempting execution.
    - `trader.py` + `liquidity.py`: reduce exposure by fast-failing on speed/market changes.
  - Source: RISKMANAGEMENT.md – “Market Volatility”, “Pre-Trade Filters”.

---

## Tier 3 – Strategic/Process Risks (Medium)

- **Capital Loss Controls (Daily/Consecutive)**
  - Control: Daily loss limit, consecutive-loss pause, daily trade cap, loss cooldowns.
  - Where:
    - `risk.py`: `RiskManager.should_trade_now()` and `on_trade_result()` manage gates and pauses.
    - `database.py`: helpers `get_pnl_between()`, `get_trade_count_between()` support daily checks.
    - `config.py`: `DAILY_MAX_LOSS_PCT`, `MAX_TRADES_PER_DAY`, `MAX_CONSECUTIVE_LOSSES`, `LOSS_COOLDOWN_SEC`, `COOLDOWN_AFTER_2_LOSSES_SEC`, `COOLDOWN_AFTER_3_LOSSES_SEC`, `DAILY_STOP_RESUME_DELAY_SEC`.
    - `bot.py`: consults `RiskManager` before trades, records skip reasons to opportunities.
  - Source: RISKMANAGEMENT.md – “Daily Operating Limits”, “Governance & Oversight”.

- **Bot Competition (Opportunity Quality)**
  - Control: Profit threshold; liquidity screen reduces chasing thin edges.
  - Where:
    - `config.py`: `MIN_PROFIT_THRESHOLD`.
    - `bot.py`: skips below-threshold opportunities and persists reasons via `save_opportunity()`.
  - Source: RISKMANAGEMENT.md – “Competitive Pressure”.

---

## Monitoring & Alerts

- **Level 3/4 Alerts (Critical)**
  - Control: Telegram alerts for critical events (order placement failure, liquidity insufficiency, high slippage, execution errors).
  - Where:
    - `notifications.py`: `NotificationService`, `send_risk_alert()` with `AlertLevel`.
    - `trader.py`: alerts on placement failures, execution errors, partial fills.
    - `liquidity.py`: alerts on insufficient liquidity and check failures.
  - Configuration:
    - `.env`: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
  - Source: RISKMANAGEMENT.md – “Monitoring & Alert Systems”.

---

## Data & Persistence

- **Trade/Opportunity/Metric Storage**
  - Where:
    - `database.py`: `trades`, `opportunities`, `metrics` tables.
    - `bot.py`: persists trade results; logs skip reasons; risk uses P&L queries for daily checks.

- **Auditability**
  - Control: Reasons for skipping opportunities and execution outcomes are recorded.
  - Where:
    - `database.py.save_opportunity()` and `save_trade()` fields.
  - Source: RISKMANAGEMENT.md – “Governance & Oversight”, “Audit Trails”.

---

## Gaps and Planned Enhancements

- **Volatility Regime Filter**
  - Not yet implemented. `RiskManager.adjust_profit_threshold()` is a hook to integrate volatility-based thresholding.

- **API Error-Rate Circuit Breaker**
  - Config present (`API_ERROR_RATE_PAUSE_THRESHOLD`, `API_ERROR_PAUSE_SEC`), basic hook exists in `risk.py` but needs wiring to real error-rate telemetry.

- **Dashboard Risk Endpoint**
  - Planned: `/api/risk` to expose paused state, consecutive losses, daily P&L, trades today.

- **Persistence of Risk State**
  - In-memory streaks/pauses; could be persisted across restarts for stronger guarantees.

- **Comprehensive Reversal/Position Recovery**
  - Best-effort reversal exists; a full recovery playbook (and status reconciliation) can be layered in.

---

## Quick Configuration Reference

- `config.py`
  - Risk gates: `DAILY_MAX_LOSS_PCT`, `MAX_TRADES_PER_DAY`, `MAX_CONSECUTIVE_LOSSES`.
  - Cooldowns: `LOSS_COOLDOWN_SEC`, `COOLDOWN_AFTER_2_LOSSES_SEC`, `COOLDOWN_AFTER_3_LOSSES_SEC`, `DAILY_STOP_RESUME_DELAY_SEC`.
  - Execution: `SINGLE_TRADE_TIMEOUT_SEC`, `FULL_TRIANGLE_TIMEOUT_SEC`, `MIN_FILL_RATIO`, `MAX_SLIPPAGE`.
  - API Health: `API_ERROR_RATE_PAUSE_THRESHOLD`, `API_ERROR_PAUSE_SEC`.
  - Profit gating: `MIN_PROFIT_THRESHOLD`.

- `.env`
  - Alerts: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
  - Exchange: `BINANCE_API_KEY`, `BINANCE_API_SECRET` (testnet/live).

---

## Validation Checklist

- Bot skips below-threshold opportunities and records reasons in `opportunities`.
- Liquidity checks run before execution; high slippage or thin books abort with alerts.
- Triangle and single-leg timeouts enforced; partial fill guard via `MIN_FILL_RATIO`.
- Risk gates stop trading on daily drawdown, max trades/day, and consecutive losses with cooldowns.
- Critical failures emit Telegram alerts when configured.
