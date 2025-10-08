# Triangular Arbitrage Bot — Documentation Overview

This README consolidates the purpose and main contents of all documentation files in `docs/` and provides quick links and commands to get started.

## Index of Docs (with summaries)

- **docs/QUICKSTART.md**
  - Purpose: 5‑minute setup to get the bot running.
  - Contents:
    - Prerequisites and environment setup.
    - One‑command setup (Linux/Mac) and manual steps (Windows).
    - Testnet API keys and `.env` config.
    - Commands to test (`--test`), scan (`--scan`), and run dry‑run (`--dry-run`).
    - Basic troubleshooting.

- **docs/GUIDE.md**
  - Purpose: End‑to‑end connection and usage guide (detailed).
  - Contents:
    - Creating project structure and files.
    - Installing Python/dependencies; virtualenv setup.
    - API keys (Testnet/Live) and safety practices.
    - Verifying `config.py` and connectivity.
    - Running scans, dry‑run, reading logs/stats/DB.
    - Daily workflow, cloud/OS notes, troubleshooting.

- **docs/PROJECT_STRUCTURE.md**
  - Purpose: Architecture, modules, and data flow reference.
  - Contents:
    - Full directory layout and file responsibilities.
    - Dependency graph among core modules.
    - Startup, main loop, and trade execution flows.
    - Database schema and reference commands.
    - Configuration hierarchy and security notes.

- **docs/PROJECT_SUMMERY.md**
  - Purpose: High‑level project summary.
  - Contents:
    - What’s included (modules, docs, setup).
    - Features, safety/risk management, analytics.
    - Usage modes; configuration and default triangles.
    - Performance expectations and warnings.

- **docs/FILELIST.md**
  - Purpose: File inventory and distribution guidance.
  - Contents:
    - Core modules, configs, docs, scripts.
    - What to include/exclude in packages.
    - File sizes, dependencies, version info, checksums.

- **docs/RISKMANAGEMENT.md**
  - Purpose: Comprehensive risk framework.
  - Contents:
    - Risk taxonomy and severity matrix.
    - Multi‑layer defense (infrastructure → execution → operational → strategic → governance).
    - Mitigations for slippage, liquidity, latency, outages.
    - Monitoring, incident response, compliance, KPIs.

- **docs/managedrisk.md**
  - Purpose: Implementation map of risk controls in code.
  - Contents:
    - Tier‑1/2/3 risks mapped to specific modules/settings.
    - Where to find controls: `trader.py`, `liquidity.py`, `exchange.py`, `risk.py`, `database.py`.
    - Gaps and planned enhancements; quick config reference.

- **docs/frontexp.md**
  - Purpose: Dashboard (frontend) guide.
  - Contents:
    - Header controls (Start/Stop/Scan), Data Source badge.
    - Toggles via `POST /api/config` (Testnet/Mainnet, WS/REST).
    - Status card, PnL card (Today’s PnL & Total Profit), Wallet, Opportunities, Trades.
    - WS feed behavior, REST fallback, reduced idle flicker, PnL coloring.

## Where things live (primary code references)

- Backend API & WS: `web/api.py` (endpoints and `/ws/live`)
- Frontend UI: `web/static/index.html`, `web/static/app.js`
- Config & runtime persistence: `config.py` (persists toggles to `data/runtime_config.json`)
- Exchange access: `exchange.py` (REST), `market_data.py` (WebSocket)
- Core bot: `bot.py` (loop), `calculator.py` (opportunities/profit), `trader.py` (exec/dry‑run), `database.py` (SQLite)
- Risk: `risk.py` (daily PnL, gates, cooldowns)

## Quick start (API dashboard)

```bash
python -m uvicorn web.api:app --host 0.0.0.0 --port 8000
# open http://localhost:8000/ui
```

Start in dry‑run (safe):
```bash
curl -X POST 'http://localhost:8000/api/start?dry_run=true'
```

Switch data source/transport at runtime (requires `X-API-Key` if `DASHBOARD_API_KEY` is set):
```bash
# Example: mainnet public data with WS enabled
curl -X POST 'http://localhost:8000/api/config?use_testnet=false&use_websocket=true'
```

## Notes

- Dry‑run never places orders; Testnet/Mainnet toggles affect data sources (and signed endpoints if keys provided).
- If Testnet WS rejects `!bookTicker`, toggle WS off (REST‑only) or switch to Mainnet WS.
- `/api/wallet` requires API keys; without keys, the app returns `{}` without retry noise.
