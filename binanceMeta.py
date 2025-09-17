import time
import requests
from testnet import BINANCE_TESTNET_API_BASE_URL , BINANCE_EX_INFO_API
from constants import PAIR
from entities import ExchangeMeta

class BINANCEExchangeInfo:
    ' run one time a day'
    def __init__(self,queue):
        self.queue = queue
        self.taker_fees = '0.001000'

    def formate_data(self,data):
        return data
    

    def send_request(self) -> None:
        try:
            t0 = time.perf_counter_ns()
            response = requests.get(f'{BINANCE_TESTNET_API_BASE_URL}{BINANCE_EX_INFO_API(PAIR)}')
            t1 = time.perf_counter_ns()
            if response.status_code == 200:
                data = response.json()
                self.formate_data(data)
                info = data.get('symbols',[[]])[0]
                info['servertime'] = data.get('serverTime',0)
                meta = ExchangeMeta('binance',
                              info,
                              self.taker_fees,
                              (t1-t0)
                              )
                self.queue.put(meta)
                print(f'successfully put meta by Binace in Queue.')
            else:
                print(f'BINANCEExchangeInfo:sendRequest:Error: statuscode=> {response.status_code}')
        except Exception as e:
            print(f'BINANCEExchangeInfo:sendRequest:Error: {e}')
