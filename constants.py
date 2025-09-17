from decimal import Decimal, getcontext
getcontext().prec = 28

LIMIT = 90
DRY_RUN = True   # Set to False to allow live orders (BE CAREFUL)

SLIPPAGE_CUSHION  = Decimal("0.0005")  # 5 bps (0.05%) cushion to account for micro-moves
MIN_NET_EDGE_USD  = Decimal("0")       # Require at least $0 net profit before trading (adjust as needed)
MAX_TRADE_USD     = Decimal("1.15")    # Hard cap on per-trade notional

PAIR = 'btcusdt'