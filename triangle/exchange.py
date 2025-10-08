"""
Exchange API module for Triangular Arbitrage Bot
Handles all interactions with Binance exchange
"""

import requests
import time
import hmac
import hashlib
from typing import Dict, List, Optional
from collections import deque
from urllib.parse import urlencode
from config import Config
from logger import logger

class BinanceExchange:
    """Binance exchange API wrapper"""
    
    def __init__(self):
        self.base_url = Config.get_api_url()
        self.api_key = Config.BINANCE_API_KEY
        self.api_secret = Config.BINANCE_API_SECRET
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key
        })
        self._last_request_time = 0
        self._request_count = 0
        # Telemetry: track request and error timestamps (epoch seconds)
        self._req_events = deque(maxlen=5000)
        self._err_events = deque(maxlen=5000)
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        if current_time - self._last_request_time < 60:
            self._request_count += 1
            if self._request_count >= Config.MAX_API_CALLS_PER_MINUTE:
                sleep_time = 60 - (current_time - self._last_request_time)
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        else:
            self._request_count = 1
            self._last_request_time = current_time
    
    def _sign_request(self, params: Dict) -> str:
        """Generate signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, signed: bool = False, params: Dict = None) -> Dict:
        """Make API request with error handling, retries, and backoff."""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        retries = 4
        backoff = 0.5
        for attempt in range(1, retries + 1):
            self._rate_limit()
            req_params = dict(params)
            if signed:
                req_params['timestamp'] = int(time.time() * 1000)
                req_params['signature'] = self._sign_request(req_params)
            try:
                if method == 'GET':
                    response = self.session.get(url, params=req_params, timeout=10)
                elif method == 'POST':
                    response = self.session.post(url, params=req_params, timeout=10)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                # Handle HTTP status
                if response.status_code == 429 or response.status_code == 418:
                    # Rate limited or banned temporarily
                    wait = min(60, backoff * (2 ** (attempt - 1)))
                    logger.warning(f"Rate limited ({response.status_code}). Backing off {wait:.1f}s (attempt {attempt}/{retries})")
                    time.sleep(wait)
                    continue
                response.raise_for_status()
                data = response.json()
                # Check Binance-specific error codes
                if isinstance(data, dict) and data.get('code'):
                    code = data.get('code')
                    msg = data.get('msg', '')
                    if code in (-1003, -1015):  # Too many requests / rate-limit
                        wait = min(60, backoff * (2 ** (attempt - 1)))
                        logger.warning(f"Binance error {code}: {msg}. Backing off {wait:.1f}s")
                    now = time.time()
                    self._req_events.append(now)
                    self._prune_events(now, Config.API_ERROR_RATE_WINDOW_SEC)
                    if isinstance(data, dict) and 'code' in data and data['code'] != 200:
                        code = data.get('code')
                        msg = data.get('msg')
                        logger.error(f"Binance error {code}: {msg}")
                        # Count this as an error event
                        self._err_events.append(now)
                        self._prune_events(now, Config.API_ERROR_RATE_WINDOW_SEC)
                        return None
                return data
            except requests.exceptions.RequestException as e:
                now = time.time()
                self._req_events.append(now)
                self._err_events.append(now)
                self._prune_events(now, Config.API_ERROR_RATE_WINDOW_SEC)
                wait = min(10, backoff * (2 ** (attempt - 1)))
                logger.warning(f"API request error: {e}. Retry in {wait:.1f}s (attempt {attempt}/{retries})")
                time.sleep(wait)
            except Exception as e:
                now = time.time()
                self._req_events.append(now)
                self._err_events.append(now)
                self._prune_events(now, Config.API_ERROR_RATE_WINDOW_SEC)
                logger.error(f"Unexpected request error: {e}")
                return None
        logger.error("API request failed after retries")
        return None

    def _prune_events(self, now_ts: float, window_sec: int):
        cutoff = now_ts - window_sec
        while self._req_events and self._req_events[0] < cutoff:
            self._req_events.popleft()
        while self._err_events and self._err_events[0] < cutoff:
            self._err_events.popleft()

    def get_error_rate(self, window_sec: Optional[int] = None) -> float:
        """Return API error rate over a sliding window [0.0 - 1.0]."""
        now = time.time()
        win = window_sec or Config.API_ERROR_RATE_WINDOW_SEC
        self._prune_events(now, win)
        req = len(self._req_events)
        if req == 0:
            return 0.0
        err = len(self._err_events)
        return min(1.0, max(0.0, err / req))
    
    def get_ticker_price(self, symbol: str) -> Optional[float]:
        """Get current ticker price for a symbol"""
        endpoint = '/api/v3/ticker/price'
        params = {'symbol': symbol}
        
        data = self._make_request('GET', endpoint, params=params)
        if data and 'price' in data:
            return float(data['price'])
        return None
    
    def get_all_ticker_prices(self) -> Dict[str, float]:
        """Get all ticker prices at once"""
        endpoint = '/api/v3/ticker/price'
        
        data = self._make_request('GET', endpoint)
        if data:
            return {item['symbol']: float(item['price']) for item in data}
        return {}
    
    def get_orderbook(self, symbol: str, limit: int = 5) -> Optional[Dict]:
        """Get order book for a symbol"""
        endpoint = '/api/v3/depth'
        params = {'symbol': symbol, 'limit': limit}
        
        return self._make_request('GET', endpoint, params=params)
    
    def get_book_ticker(self, symbol: str) -> Optional[Dict]:
        """Get best bid/ask prices"""
        endpoint = '/api/v3/ticker/bookTicker'
        params = {'symbol': symbol}
        
        return self._make_request('GET', endpoint, params=params)
    
    def get_all_book_tickers(self) -> List[Dict]:
        """Get all book tickers at once"""
        endpoint = '/api/v3/ticker/bookTicker'
        
        data = self._make_request('GET', endpoint)
        return data if data else []
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information"""
        # If keys are not provided, skip calling the signed endpoint to avoid 401 spam
        if not self.api_key or not self.api_secret:
            logger.debug("Skipping account info request: no API keys provided")
            return {}
        endpoint = '/api/v3/account'
        return self._make_request('GET', endpoint, signed=True)
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Place market order"""
        endpoint = '/api/v3/order'
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
            'newOrderRespType': 'FULL'
        }
        
        logger.info(f"Placing {side} order: {quantity} {symbol}")
        return self._make_request('POST', endpoint, signed=True, params=params)
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get symbol information and trading rules"""
        return self._make_request('GET', '/api/v3/exchangeInfo', params={'symbol': symbol})
        
    def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """
        Get order book for a symbol
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            limit: Number of price levels to return (default 100, max 5000)
            
        Returns:
            {
                'lastUpdateId': int,  # Last update ID
                'bids': [             # List of bid orders [price, quantity]
                    ['price', 'quantity'],
                    ...
                ],
                'asks': [             # List of ask orders [price, quantity]
                    ['price', 'quantity'],
                    ...
                ]
            }
        """
        try:
            params = {'symbol': symbol, 'limit': min(limit, 5000)}
            data = self._make_request('GET', '/api/v3/depth', params=params)
            
            if not data or 'bids' not in data or 'asks' not in data:
                logger.error(f"Invalid order book data received: {data}")
                return None
                
            # Convert string values to floats for easier calculations
            orderbook = {
                'lastUpdateId': data.get('lastUpdateId', 0),
                'bids': [[float(price), float(qty)] for price, qty in data['bids']],
                'asks': [[float(price), float(qty)] for price, qty in data['asks']],
            }
            
            return orderbook
            
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            return None
        
    def get_order(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Get order status/details"""
        endpoint = '/api/v3/order'
        params = {'symbol': symbol, 'orderId': order_id}
        return self._make_request('GET', endpoint, signed=True, params=params)

    def get_my_trades(self, symbol: str, start_time: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get account trades for a symbol (recent fills)."""
        endpoint = '/api/v3/myTrades'
        params: Dict = {'symbol': symbol, 'limit': limit}
        if start_time:
            params['startTime'] = start_time
        data = self._make_request('GET', endpoint, signed=True, params=params)
        return data if isinstance(data, list) else []
    
    def get_balance(self, asset: str) -> float:
        """Get balance for specific asset"""
        account = self.get_account_info()
        if account and 'balances' in account:
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
        return 0.0
