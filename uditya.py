import time
import requests
from constants import PAIR
from entities import ExchangeMeta

class BYBITExchangeInfo:
    ' run one time a day'
    def __init__(self,queue):
        self.queue = queue
        self.taker_fees = '0.001000'
        self.url = "https://api-testnet.bybit.com/v5/market/instruments-info"
        self.params = {"category": "spot","symbol":PAIR.upper()}

    def formate_data(self,data):
        if data:
            response = data.get("retMsg")
            st = data.get("time")
            result = data.get("result")
            if result:
                lst = result.get("list")[0]
                print(lst)
                if lst:
                    symbol = lst.get("symbol")
                    baseAst = lst.get("baseCoin")
                    quoteAst = lst.get("quoteCoin")
                    status = lst.get("status")
                    MT = lst.get("marginTrading")
                    LOTF = lst.get("lotSizeFilter")
                    info = {}
                    if LOTF:
                        basePrecision = LOTF.get("basePrecision")
                        quotePrecision = LOTF.get("quotePrecision")
                        minOrderQty = LOTF.get("minOrderQty")
                        maxOrderQty = LOTF.get("maxOrderQty")
                        minOrderAmt = LOTF.get("minOrderAmt")
                        maxOrderAmt = LOTF.get("maxOrderAmt")
                    PF = lst.get("lotSizeFilter") #price filter
                    if PF:
                        tickSize = PF.get("tickSize")

                    return {
                        "servertime":st,
                        "symbol":symbol,
                        "status":status,
                        "baseAsset":baseAst,
                        "baseAssetPrecision":basePrecision,
                        "quoteAsset":quoteAst,
                        "quotePrecision":quotePrecision,
                        "filters":[{
                            "filterType":"PRICE_FILTER",
                            "minPrice":minOrderAmt,
                            "maxPrice":maxOrderAmt,
                            "tickSize":tickSize
                        },
                        {
                            "filterType":"LOT_SIZE",
                            "minQty":minOrderQty,
                            "maxQty":maxOrderQty,
                        }]
                    }
    

    def send_request(self) -> None:
        try:
            t0 = time.perf_counter_ns()
            response = requests.get(self.url, params=self.params)
            t1 = time.perf_counter_ns()
            if response.status_code == 200:
                data = response.json()
                info = self.formate_data(data)
                print(info)
                
                meta = ExchangeMeta('bybit',
                              info,
                              self.taker_fees,
                              (t1-t0)
                              )
                self.queue.put(meta)
                print(f'successfully put meta by Binace in Queue.')
            else:
                print(f'ExchangeInfoBinance:sendRequest:Error: statuscode=> {response.status_code}')
        except Exception as e:
            print(f'ExchangeInfoBinance:sendRequest:Error: {e}')


# if __name__ == '__main__':
#     b = ExchangeInfoBinance()
#     b.send_request()