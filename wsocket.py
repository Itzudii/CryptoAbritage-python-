import websockets
import time
import json
from testnet import BINANCE_TESTNET_STREAM_BASE_URL , BYBIT_TESTNET_STREAM_BASE_URL
from constants import PAIR
from entities import Update

ORIGNAL_URL = 'wss://stream.binance.com:9443'

class BinanceWS:
    def __init__(self, queue):
        self.queue = queue
        self.url = f"{BINANCE_TESTNET_STREAM_BASE_URL}/stream?streams={PAIR}@bookTicker"

    async def listen(self) -> None:
        try:
            async with websockets.connect(self.url) as ws:
                print(f"{time.time()} Connected to Binance WS")

                async for msg in ws:
                    response = json.loads(msg)
                    data = response["data"]
                    symbol = data["s"].lower()
                    bid = float(data["b"])
                    ask = float(data["a"])
                    bidQty = float(data["B"])
                    askQty = float(data["A"])
                    update = Update('binance',ask,askQty,bid,bidQty,time.perf_counter_ns())
                    self.queue.put(update)

        except websockets.exceptions.ConnectionClosed as e:
            print("❌ Connection closed (on_close):", e.code, e.reason)

        except Exception as e:
            print("⚠️ Error (on_error):", e)


class BybitWS:
    def __init__(self, queue):
        self.queue = queue
        self.url = BYBIT_TESTNET_STREAM_BASE_URL

    async def listen(self) -> None:
        try:
            async with websockets.connect(self.url) as ws:
                print(f"{time.time()} Connected to Bybit WS")
            # Send subscription payload immediately after connection
                payload = {
                    "op": "subscribe",
                    "args": ["orderbook.1.BTCUSDT"]  # Best bid/ask for BTCUSDT
                }
                await ws.send(json.dumps(payload))
                print("BYbit Subscribed to BTCUSDT orderbook")

                # Continuously listen for messages
                while True:
                    message = await ws.recv()
                    data = json.loads(message)

                    if "data" in data:
                        bids = data["data"]["b"]
                        asks = data["data"]["a"]
                        if bids and asks:
                            best_bid = bids[0]
                            best_ask = asks[0]
                            ts = data['ts'] if data['ts'] else time.perf_counter_ns()

                            bid = float(best_bid[0])
                            ask = float(best_ask[0])
                            bidQty = float(best_bid[1])
                            askQty = float(best_ask[1])
                            update = Update('bybit',ask,askQty,bid,bidQty,ts)
                            self.queue.put(update)


        except websockets.exceptions.ConnectionClosed as e:
            print("❌ Connection closed (on_close):", e.code, e.reason)

        except Exception as e:
            print("⚠️ Error (on_error):", e)