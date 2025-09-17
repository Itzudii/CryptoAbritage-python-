from dataclasses import dataclass
from decimal import Decimal
from typing import  Any, Optional

@dataclass
class Update:
    platform:str
    ask_p:int
    ask_q:int
    bid_p:int
    bid_q:int
    nano: Any
    
    def _type(self) -> str:
        return 'update'

@dataclass
class Error:
    platform:str
    message:str
    _type:Optional[str] = 'empty'

    def _type(self) -> str:
        return 'error'


class ExchangeMeta:
    def __init__(self,platform,info,taker_fee,latency_ns):
        self.platform = platform
        self.servertime = info.get('servertime',0)
        self.taker_fee = Decimal(str(taker_fee))
        self.latency_ns = latency_ns

        self.symbol = info.get('symbol','').lower()
        self.status = info.get('status')

        self.baseAsset = info.get('baseAsset')
        self.baseAssetPrecision = Decimal(str(info.get('baseAssetPrecision',0)))
        self.quoteAsset = info.get('quoteAsset')
        self.quotePrecision = Decimal(str(info.get('quotePrecision',0)))

        #  List of OrderTypes
        self.orderTypes = info.get('orderTypes',[])

        #  isSpotTradingAllowed && isMarginTradingAllowed => bool
        self.isSpotTradingAllowed = info.get('isSpotTradingAllowed') 
        self.isMarginTradingAllowed = info.get('isMarginTradingAllowed')

        #  Dict of all Filters
        self.filter = dict([[filt.get('filterType'),filt] for filt in info.get('filters',[])])

        #  PRICE_FILTER
        self.priceFilter = self.filter.get('PRICE_FILTER',{})
        self.minPrice = Decimal(self.priceFilter.get('minPrice','0'))
        self.maxPrice = Decimal(self.priceFilter.get('maxPrice','999999999'))
        self.tickSize = Decimal(self.priceFilter.get('tickSize','0.00000001'))

        #  LOT_SIZE
        self.lotSizeFilter = self.filter.get('LOT_SIZE',{})
        self.minQty = Decimal(self.lotSizeFilter.get("minQty", "0.00000001"))
        self.maxQty = Decimal(self.lotSizeFilter.get("maxQty", "999999999"))
        self.stepSize = Decimal(self.lotSizeFilter.get("stepSize", "0.00000001"))

        # #  NOTIONAL
        self.notionalFilter = self.filter.get('NOTIONAL',{})
        self.minNotional = Decimal(self.notionalFilter.get("minNotional", "0"))
        self.maxNotional = Decimal(self.notionalFilter.get("maxNotional", "999999999"))
        
        #  ICEBERG_PARTS
        self.icebergPartsFilter = self.filter.get('ICEBERG_PARTS',{})

        #  TRAILING_DELTA
        self.trailingDeltaFilter = self.filter.get('TRAILING_DELTA',{})

        #  PERCENT_PRICE_BY_SIDE
        self.percentPriceBySideFilter = self.filter.get('PERCENT_PRICE_BY_SIDE',{})


        #  MAX_NUM_ORDERS
        self.maxNumOrdersFilter = self.filter.get('MAX_NUM_ORDERS',{})

        #  MAX_NUM_ALGO_ORDERS
        self.maxNumAlgoOrdersFilter = self.filter.get('MAX_NUM_ALGO_ORDERS',{})

    def _type(self) -> str:
        return 'meta'
