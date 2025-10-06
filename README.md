# Crypto Arbitrage (Low-Latency Refactor)

This repository has been refactored to a clean, modular, and low-latency architecture under the `arb/` package. It provides:

- A consistent configuration surface in `arb/config.py`.
- Ultra-light domain models in `arb/entities.py` and `arb/node.py`.
- Optimized decision logic in `arb/decision_engine.py`.
- Normalized metadata fetchers in `arb/meta.py`.
- Tuned testnet WebSocket clients in `arb/market_ws.py`.
- A new `run.py` entrypoint that pins processes to CPU cores and uses `uvloop` for lower latency.

## Structure

```
.
├── arb/
│   ├── __init__.py
│   ├── config.py
│   ├── decision_engine.py
│   ├── entities.py
│   ├── market_ws.py
│   ├── meta.py
│   └── node.py
├── requirements.txt
├── run.py
└── (legacy files kept intact: main.py, wsocket.py, decision.py, entities.py, node.py, binanceMeta.py, bybitMeta.py, constants.py, testnet.py)
```

## Quickstart

1. Create and activate a virtual environment (recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the system:

```bash
python run.py
```

This will:
- Fetch exchange metadata once for the configured symbol in `arb/config.py` (`PAIR`).
- Start Binance and Bybit WebSocket listeners as separate processes.
- Start the Decision Engine consumer in a third process.

All three processes are CPU-pinned (configurable) and use `uvloop` for async event loops.

## Configuration

Edit `arb/config.py` to adjust:

- `PAIR`: Trading pair (e.g., `btcusdt`). Used consistently across exchanges (Bybit uppercases automatically).
- Decision guards: `SLIPPAGE_CUSHION`, `MIN_NET_EDGE_USD`, `MAX_TRADE_USD`.
- WebSocket tuning: `WS_PING_INTERVAL`, `WS_PING_TIMEOUT`, `WS_MAX_QUEUE`, `WS_COMPRESSION`.
- CPU affinity: `CPU_BINANCE_WS`, `CPU_BYBIT_WS`, `CPU_DECISION`.

## Notes

- The refactor keeps legacy files intact for reference; `run.py` is the new entrypoint.
- The system currently prints `Decision` objects when an opportunity appears; order placement is not implemented.
- For production, implement:
  - Partial-fill handling and order state management.
  - Balance checks and rebalancing flows.
  - Freshness/latency thresholds and metrics.
  - Logging with minimal overhead (structured logging, ring buffers).