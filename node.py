from typing import Tuple,Dict,Any
class Node:
    def __init__(self,ex):
        self.platform = ex
        self.ask_p = None
        self.ask_q = None
        self.bid_p = None
        self.bid_q = None
        self.nano = None

    def get_ask(self) -> Tuple[int,int]:
        return self.ask_p, self.ask_q

    def set_ask(self, ask: Tuple[int,int]) -> None:
        self.ask_p, self.ask_q = ask

    def get_bid(self) -> Tuple[int,int]:
        return self.bid_p, self.bid_q

    def set_bid(self, bid: Tuple[int,int]) -> None:
        self.bid_p, self.bid_q = bid
    
    def setAll(self,ask_p,ask_q,bid_p,bid_q,nano) -> None:
        self.ask_p = ask_p
        self.ask_q = ask_q
        self.bid_p = bid_p
        self.bid_q = bid_q        
        self.nano = nano

    def to_dict(self) -> Dict[str,Any]:
        return {
                "exchange": self.platform,
                "bid": self.bid_p,
                "ask": self.ask_p,
                "bidQty": self.bid_q,
                "askQty": self.ask_q,
                "nano": self.nano
                    }