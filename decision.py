from node import Node
from collections import defaultdict
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, Tuple
from entities import ExchangeMeta
from constants import SLIPPAGE_CUSHION, MIN_NET_EDGE_USD, MAX_TRADE_USD


@dataclass
class TopOfBook:
    ask_p: Decimal
    ask_q: Decimal
    bid_p: Decimal
    bid_q: Decimal


@dataclass
class Balances:
    buy_quote_free: Decimal
    sell_base_free: Decimal


@dataclass
class Decision:
    should_trade: bool
    reason: str
    side: Optional[str] = None              
    qty: Decimal = Decimal("0")
    expected_net_usd: Decimal = Decimal("0")
    constraints: Tuple[str, ...] = ()


# ---------- helpers ----------

def _as_decimal(x, default: Decimal = Decimal("0")) -> Decimal:
    if x is None:
        return default
    try:
        return Decimal(str(x))
    except Exception:
        return default


def floor_to_step(x: Decimal, step: Decimal) -> Decimal:
    step = _as_decimal(step, Decimal("0"))
    if step <= 0:
        return x
    return (x // step) * step


def quantize_price_to_tick(price: Decimal, meta: ExchangeMeta) -> Decimal:
    tick = _as_decimal(meta.tickSize)
    if tick and tick > 0:
        return floor_to_step(price, tick)
    return price


def amount_step(meta: ExchangeMeta) -> Decimal:
    return _as_decimal(meta.stepSize)


def min_cost(meta: ExchangeMeta) -> Decimal:
    return _as_decimal(meta.minNotional)


def max_cost(meta: ExchangeMeta) -> Decimal:
    return _as_decimal(meta.maxNotional)


def min_qty_step_clamped(qty: Decimal, metas: Tuple[ExchangeMeta, ExchangeMeta]) -> Decimal:
    # Use the stricter (max) step between the two exchanges, then floor
    steps = [amount_step(m) for m in metas]
    step = max(steps)
    return floor_to_step(qty, step)


def net_profit_after_fees(qty: Decimal, buy_px: Decimal, sell_px: Decimal,
                          fee_buy: Decimal, fee_sell: Decimal, cushion: Decimal) -> Decimal:
    notional_buy  = qty * buy_px
    notional_sell = qty * sell_px
    fees = notional_buy * fee_buy + notional_sell * fee_sell
    cushion_cost = (notional_buy + notional_sell) * cushion
    return notional_sell - notional_buy - fees - cushion_cost


def min_qty_for_instant_fill(tob: TopOfBook,
                             metas: Tuple[ExchangeMeta, ExchangeMeta]) -> Decimal:
    """Tradable qty at top-of-book, respecting precision, steps, and notional bounds.
       metas[0] is the BUY exchange, metas[1] is the SELL exchange.
    """
    qty = min(tob.ask_q, tob.bid_q)

    # Clamp by per-trade notional cap (using buy side price)
    max_qty_by_usd = (MAX_TRADE_USD / tob.ask_p) if tob.ask_p > 0 else Decimal("0")
    qty = min(qty, max_qty_by_usd)

    # Floor to stricter step
    qty = min_qty_step_clamped(qty, metas)

    # Enforce min notional across both venues (use the stricter max of mins)
    min_costs = [min_cost(m) for m in metas if m]
    min_cost_strict = max(min_costs) if min_costs else Decimal("0")

    if tob.ask_p * qty < min_cost_strict:
        return Decimal("0")

    # Also respect any max notional if provided on either side
    max_costs = [max_cost(m) for m in metas if m]
    if max_costs:
        # ensure qty * ask_p doesn't exceed the strictest max across venues and MAX_TRADE_USD
        strict_max = min(min(max_costs), MAX_TRADE_USD)
        qty = min(qty, floor_to_step(strict_max / tob.ask_p, amount_step(metas[0])))

    return max(qty, Decimal("0"))


# ---------- main decision ----------

def decide_cross_arb(symbol: str,
                      buy: ExchangeMeta,
                      sell: ExchangeMeta,
                      node: Node,
                      balances: Optional[Balances] = None,
                      min_edge_usd: Decimal = MIN_NET_EDGE_USD,
                      cushion: Decimal = SLIPPAGE_CUSHION) -> Decision:
    """
    Decide whether to arbitrage by buying on `buy` exchange at best ask and selling on `sell` exchange at best bid.

    Parameters
    ----------
    symbol: trading symbol (e.g., "BTC/USDT") for logs/telemetry
    buy: ExchangeMeta for the exchange where you would place the BUY
    sell: ExchangeMeta for the exchange where you would place the SELL
    tob: TopOfBook with best ask on buy venue and best bid on sell venue
    balances: optional Balances for basic sufficiency checks
    min_edge_usd: required net profit after fees and cushion to proceed
    cushion: slippage cushion applied to notional on both legs
    """
    tob=TopOfBook(Decimal(str(node.ask_p)),Decimal(str(node.ask_q)),Decimal(str(node.bid_p)),Decimal(str(node.bid_q)))

    constraints = []

    # Sanity price checks
    if tob.ask_p <= 0 or tob.bid_p <= 0:
        return Decision(False, "Invalid top-of-book prices", constraints=tuple(constraints))

    # Ensure there is an apparent edge before deeper checks
    gross_edge = tob.bid_p - tob.ask_p
    if gross_edge <= 0:
        return Decision(False, "No positive spread (bid <= ask)", constraints=tuple(constraints))

    # Compute tradable quantity respecting books & filters
    qty = min_qty_for_instant_fill(tob, (buy, sell))
    if qty <= 0:
        return Decision(False, "Qty after filters/limits is 0", constraints=tuple(constraints))

    # Balance checks (optional but recommended)
    if balances:
        # Buy leg requires quote (e.g., USDT)
        needed_quote = tob.ask_p * qty * (Decimal("1") + cushion + buy.taker_fee)
        if balances.buy_quote_free < needed_quote:
            constraints.append(f"Insufficient quote on {buy.platform}: need {needed_quote} have {balances.buy_quote_free}")

        # Sell leg requires base asset
        if balances.sell_base_free < qty:
            constraints.append(f"Insufficient base on {sell.platform}: need {qty} have {balances.sell_base_free}")

        if constraints:
            return Decision(False, "Balance constraint(s)", constraints=tuple(constraints))

    # Price quantization (for limit fallbacks)
    buy_px_q  = quantize_price_to_tick(tob.ask_p, buy)
    sell_px_q = quantize_price_to_tick(tob.bid_p, sell)

    # Re-guard after quantization
    if sell_px_q <= buy_px_q:
        return Decision(False, "No edge after price rounding", constraints=tuple(constraints))

    # Net edge after fees + cushion
    net_usd = net_profit_after_fees(
        qty=qty,
        buy_px=buy_px_q,
        sell_px=sell_px_q,
        fee_buy=buy.taker_fee,
        fee_sell=sell.taker_fee,
        cushion=cushion,
    )

    if net_usd < min_edge_usd:
        return Decision(False, f"Net edge {net_usd} < min {min_edge_usd}", constraints=tuple(constraints))

    side = f"buy_{buy.platform}_sell_{sell.platform}"
    return Decision(True, "Tradeable", side=side, qty=qty, expected_net_usd=net_usd, constraints=tuple(constraints))

class DecisionEngine:
    def __init__(self,queue):
        self.queue = queue
        self.status = defaultdict(bool)
        self.metaInfo = dict()
        self.tickerInfo = dict()

    def c_get_node(self,platform:str) -> Node: 
        ' return node if present if not present create and return '
        try:
            if platform not in self.tickerInfo:
                self.tickerInfo[platform] = Node(platform)
            return self.tickerInfo[platform]
        except Exception as e:
            print(f'Storage:getnode:Error:{e}')

    def error_handler(self,obj):
        pass

    def meta_handler(self,obj):
        platform  = obj.platform
        if not self.status[platform]:
            self.status[platform] = True
            self.metaInfo[platform] = obj
        else:
            print(f'error:repeate request {platform}')


    def update_handler(self,obj):
        platform  = obj.platform
        node = self.c_get_node(platform)
        node.setAll(obj.ask_p,obj.ask_q,obj.bid_p,obj.bid_q,obj.nano)   
        print(self.metaInfo)
        print(self.tickerInfo)
        # raise Exception('stop')
        if all([self.status.get('binance',False),self.status.get('bybit',False)]):
            binanceMeta = self.metaInfo.get('binance')
            bybitMeta = self.metaInfo.get('bybit')
            binanceNode = self.tickerInfo.get('binance')
            bybitNode = self.tickerInfo.get('bybit')
            if all([binanceMeta,bybitMeta,binanceNode,bybitNode]):
                node1 = Node('test1-binanace')
                node1.setAll(binanceNode.ask_p,binanceNode.ask_q,bybitNode.bid_p,bybitNode.bid_q,binanceNode.nano)

                node2 = Node('test2-bybit')
                node2.setAll(bybitNode.ask_p,bybitNode.ask_q,binanceNode.bid_p,binanceNode.bid_q,bybitNode.nano)

                decision1 = decide_cross_arb('btcusdt',binanceMeta,bybitMeta,node1)
                decision2 = decide_cross_arb('btcusdt',bybitMeta,binanceMeta,node2)
                print(decision1)
                print(decision2)
                # if decision1.should_trade:
                #     print(f"Decision: {decision1.side} qty:{decision1.qty} expected_net_usd:{decision1.expected_net_usd} constraints:{decision1.constraints}")
                # if decision2.should_trade:
                #     print(f"Decision: {decision2.side} qty:{decision2.qty} expected_net_usd:{decision2.expected_net_usd} constraints:{decision2.constraints}") 
        # print(obj.ask_p,obj.ask_q,obj.bid_p,obj.bid_q,obj.nano,platform)    

    def handler(self,obj):
        try:
           typ = obj._type()
           match(typ):
               case 'error': self.error_handler(obj)
               case 'update': self.update_handler(obj)
               case 'meta': self.meta_handler(obj)
        except Exception as e:
            print(f'Storage:handler:Error:{e}')


    def dicision(self):
        '''
        Think of it this way:
        Your Code: "There's a 1% profit opportunity to buy 1 BTC on Exchange A and sell it on Exchange B." (The core decision)

        A Complete System: 
        "There's a 1% profit opportunity, and I have enough capital on both exchanges. The data is fresh, so
        the opportunity is likely still there. I will place the order now, and if it only partially fills, I have a plan to 
        recover." (The complete, safe decision)'''
        # only run decision if both platform meta is store
        pass

    async def feed(self):
        try:
            while True:
                obj = self.queue.get()
                self.handler(obj)
    
        except Exception as e:
            print(f'Storage:listen:Error:{e}')

