# Frontend UI Guide (Dashboard)

This document explains every section on the dashboard UI, what it shows, why it’s useful, and how to use the data‑source toggles and PnL features.

The UI is served by `web/api.py` at `/ui` and powered by `web/static/index.html` and `web/static/app.js`.

## Header

- **[Data Source Badge]** (`#dataSource`)
  - Shows the current data source and transport, e.g. `Mainnet • WS` or `Testnet • REST`.
  - Hover to see the active REST and WebSocket URLs.
  - Reflects values returned by `GET /api/config`.

- **[Start (Dry Run)]** (`#startBtn`)
  - Starts the arbitrage bot in dry‑run mode via `POST /api/start?dry_run=true`.
  - No real orders are placed. Used for safe simulation.

- **[Stop]** (`#stopBtn`)
  - Stops the bot via `POST /api/stop`.

- **[On-demand Scan]** (`#scanBtn`)
  - Fetches current market prices and computes opportunities once via `GET /api/scan`, without starting the continuous bot loop.

- **[Toggle Net]** (`#toggleNetBtn`)
  - Switches `USE_TESTNET` on/off via `POST /api/config?use_testnet=...`.
  - Useful to move between Testnet and Mainnet public data. Dry‑run is still safe either way.
  - If `DASHBOARD_API_KEY` is set in `.env`, you must set `localStorage.setItem('dash_api_key', 'YOUR_KEY')` in the browser console once to authorize.

- **[Toggle WS]** (`#toggleWsBtn`)
  - Switches `USE_WEBSOCKET` on/off via `POST /api/config?use_websocket=...`.
  - Enables/disables the real‑time WebSocket price feed. REST fallback continues to work when WS is off.

## Status Card

- **[Mode]** (`#mode`)
  - `DRY_RUN` or `LIVE`. The UI starts in simulation; live trading should only be used with care.
- **[Running]** (`#running`)
  - Indicates if the bot loop is active.
- **[Iterations]** (`#iterations`)
  - Loop iterations since start; shows the system is scanning continuously.
- **[Opportunities Found]** (`#oppsFound`)
  - Total opportunities detected during the current session.
- **[Trades Executed]** (`#tradesExec`)
  - Executed trades count. In dry‑run this remains 0.

Backend source: `web/api.py` → `GET /api/status`.

## PnL Card

- **[Today’s PnL]** (`#dailyPNL`)
  - From `GET /api/risk` (`risk.RiskManager.get_state()`).
  - Green for positive, red for negative.
- **[Total Profit]** (`#totalProfit2`)
  - From `GET /api/stats` (aggregated bot statistics).
  - Green for positive, red for negative.

Why it’s useful: gives a quick “portfolio‑style” view of your profitability without drilling into tables.

## Wallet Card

- **[Total Portfolio (USDT)]** (`#totalUSDT`)
  - Aggregates balances valued in USDT.
- **[Balances Table]** (`#walletBody`)
  - Lists assets, free/locked amounts, and their USDT value.

Backend source: `web/api.py` → `GET /api/wallet`. Requires exchange API keys for signed endpoints; otherwise returns empty content gracefully.

## Live Opportunities

- **Table** (`#oppsBody`)
  - Shows recent/streamed opportunities.
  - Columns: Time, Path (triangle), Profit (USDT), Profit %.

Backend source:
- Continuous updates via the WebSocket endpoint `/ws/live`.
- When the bot isn’t running, the server performs a lightweight scan at most every 10 seconds to reduce flicker.

## Recent Trades

- **Table** (`#tradesBody`)
  - Displays recent trades from the SQLite database (`data/trades.db`).
  - Profit cells are colored: green for gains, red for losses.

Backend source: `web/api.py` → WebSocket feed `/ws/live` streams the latest from DB.

## Footer

- References the HTTP and WS endpoints for convenience.

## Data Source Toggles (Runtime Config)

Endpoints (`web/api.py`):
- **GET `/api/config`**
  - Returns `{ use_testnet, use_websocket, api_url, ws_url }`.
- **POST `/api/config?use_testnet=...&use_websocket=...`**
  - Updates flags at runtime.
  - If `DASHBOARD_API_KEY` is set in `.env`, this endpoint requires header `X-API-Key`.
  - Also starts/stops the WebSocket price feed immediately.

Persistence (`config.py`):
- Changes are saved to `data/runtime_config.json` so they survive process restarts.
- On import, `Config._load_runtime_overrides()` applies saved flags.

## How the WebSocket feed works

- Client connects to `/ws/live`.
- The server (`web/api.py`) sends:
  - Status (`/api/status` equivalent), recent trades and opportunities from DB.
  - If the bot isn’t running, a lightweight scan result at most every 10s.
- If WS is disabled (`USE_WEBSOCKET=False`), the app relies on REST price fetches.

## Styling and Colors

- Profit/loss styles are in `index.html`:
  - `.pos { color: #8fe1b7; }` (green)
  - `.neg { color: #f08a8a; }` (red)
- Pills reflect status:
  - `.ok` greenish, `.warn` amber, `.bad` red.

## Security Notes

- Add `DASHBOARD_API_KEY` in `.env` to protect admin endpoints (start/stop, config set).
- The UI will send `X-API-Key` if you store it locally:
  - `localStorage.setItem('dash_api_key', 'YOUR_KEY')`

## Troubleshooting

- **No wallet data**: Without API keys, signed endpoints return empty data — this is expected in dry‑run.
- **WS errors on testnet**: Testnet may reject certain WS paths; switch to mainnet public data or toggle WS off.
- **Flicker when bot idle**: The server scans at most every 10s now to reduce UI flicker.

## File Map

- UI HTML/CSS: `web/static/index.html`
- UI Logic: `web/static/app.js`
- API/WS Server: `web/api.py`
- Config and persistence: `config.py`
- Risk state & daily PnL: `risk.py`
- REST/WS data sources: `exchange.py`, `market_data.py`
- Stats and history DB: `database.py`, file `data/trades.db`
