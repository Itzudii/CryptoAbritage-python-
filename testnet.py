# BINANCE TESTNET
BINANCE_TESTNET_STREAM_BASE_URL = 'wss://stream.testnet.binance.vision'

BINANCE_TESTNET_API_BASE_URL = 'https://testnet.binance.vision'
# 'API time out limit 10 second'
# apis \/
BINANCE_PING_API = '/api/v3/ping'
BINANCE_SERVER_TIME_API = '/api/v3/time'
BINANCE_ALL_EX_INFO_API = '/api/v3/exchangeInfo'
BINANCE_EX_INFO_API = lambda pair: f'/api/v3/exchangeInfo?symbol={pair.upper()}'

# BYBIT TESTNET
BYBIT_TESTNET_STREAM_BASE_URL = 'wss://stream-testnet.bybit.com/v5/public/spot'

BYBIT_TESTNET_API_BASE_URL = 'https://api-testnet.bybit.com'

BYBIT_EX_INFO_API = '/v5/market/instruments-info'




'''# from decimal import Decimal, getcontext
# from dataclasses import dataclass
# from typing import Dict, Any, Optional, Tuple
# from exchangeinfo import ExchangeMeta
# from node import Node
# # High precision for money math
# getcontext().prec = 28

# # --- Tunables ---
# SLIPPAGE_CUSHION  = Decimal("0.0005")  # 5 bps (0.05%) cushion to account for micro-moves
# MIN_NET_EDGE_USD  = Decimal("0")       # Require at least $0 net profit before trading (adjust as needed)
# MAX_TRADE_USD     = Decimal("1.15")    # Hard cap on per-trade notional





# # ---------- example usage (remove in production) ----------
# if __name__ == "__main__":
#     # Example metas (mimic CCXT/filters)
#     binance = ExchangeMeta(
#         name="binance",
#         precision={"amount": 0.00001, "price": 0.01},
#         limits={"amount": {"min": 0.0001}, "cost": {"min": 5}},
#         filters={
#             "PRICE_FILTER": {"minPrice": "0.01", "maxPrice": "1000000", "tickSize": "0.01"},
#             "LOT_SIZE": {"minQty": "0.0001", "maxQty": "1000", "stepSize": "0.0001"},
#             "NOTIONAL": {"minNotional": "5", "maxNotional": "1000000"},
#         },
#         taker_fee=Decimal("0.0006"),
#     )

#     kraken = ExchangeMeta(
#         name="kraken",
#         precision={"amount": 0.00001, "price": 0.1},
#         limits={"amount": {"min": 0.0002}, "cost": {"min": 5}},
#         filters=None,
#         taker_fee=Decimal("0.0010"),
#     )

#     tob1 = TopOfBook(
#         ask_p=Decimal("60000.00"),
#         ask_q=Decimal("0.005"),
#         bid_p=Decimal("60001.00"),
#         bid_q=Decimal("0.010"),
#     )
#     tob2 = TopOfBook(
#         ask_p=Decimal("60000.00"),
#         ask_q=Decimal("0.005"),
#         bid_p=Decimal("60001.00"),
#         bid_q=Decimal("0.010"),
#     )

#     bals = Balances(
#         buy_quote_free=Decimal("100.00"),
#         sell_base_free=Decimal("0.010"),
#     )

#     decision1 = decide_cross_arb("BTC/USDT", binance, kraken, tob1, bals)
#     decision2 = decide_cross_arb("BTC/USDT", binance, kraken, tob2, bals)
#     print(decision1)
#     print(decision2)

'''