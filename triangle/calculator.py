"""
Arbitrage calculation module
Handles profit calculations and opportunity detection
"""

from typing import Dict, List, Optional, Tuple
from config import Config
from logger import logger

class ArbitrageCalculator:
    """Calculate arbitrage opportunities and profits"""
    
    def __init__(self):
        self.maker_fee = Config.MAKER_FEE
        self.taker_fee = Config.TAKER_FEE
        self.max_slippage = Config.MAX_SLIPPAGE
    
    def calculate_triangular_arbitrage(
        self, 
        triangle: Dict, 
        prices: Dict[str, float],
        initial_amount: float
    ) -> Tuple[float, float, bool]:
        """
        Calculate profit for a triangular arbitrage path
        
        Returns:
            (final_amount, profit_percent, is_profitable)
        """
        pairs = triangle['pairs']
        path = triangle['path']
        
        # Check if all prices are available
        for pair in pairs:
            if pair not in prices or prices[pair] is None:
                return 0, 0, False
        
        amount = initial_amount
        
        # Execute virtual trades through the triangle
        for i, pair in enumerate(pairs):
            price = prices[pair]
            
            # Determine trade direction
            base_curr = path[i]
            quote_curr = path[i + 1]
            
            # Check if we're buying or selling
            if pair.startswith(base_curr):
                # Selling base currency
                amount = amount / price
            elif pair.endswith(base_curr):
                # Buying base currency
                amount = amount * price
            else:
                # Need to determine direction from pair structure
                if pair.startswith(quote_curr):
                    amount = amount * price
                else:
                    amount = amount / price
            
            # Apply trading fee
            amount = amount * (1 - self.taker_fee)
        
        # Apply slippage
        amount = amount * (1 - self.max_slippage)
        
        profit = amount - initial_amount
        profit_percent = (profit / initial_amount) * 100
        
        is_profitable = profit_percent >= Config.MIN_PROFIT_THRESHOLD
        
        return amount, profit_percent, is_profitable
    
    def calculate_precise_triangular(
        self,
        triangle: Dict,
        prices: Dict[str, float],
        initial_amount: float
    ) -> Dict:
        """
        More precise calculation considering actual pair structure
        """
        pairs = triangle['pairs']
        path = triangle['path']
        
        if len(pairs) != 3 or len(path) != 4:
            return {'error': 'Invalid triangle structure'}
        
        # Validate all prices exist
        for pair in pairs:
            if pair not in prices:
                return {'error': f'Missing price for {pair}'}
        
        steps = []
        amount = initial_amount
        
        # Helper for a single step given current and next asset and a pair
        def _apply_step(curr_asset: str, next_asset: str, pair: str, price: float, amt_in: float):
            # Pair format is BASEQUOTE (e.g., ETHBTC means 1 ETH costs <price> BTC)
            base = pair[:-len(next_asset)] if pair.endswith(next_asset) else pair[:len(next_asset)]
            quote = pair[len(base):]
            # Validate mapping
            if base + quote != pair:
                return {'error': f'Invalid pair parsing for {pair}'}, None
            if {curr_asset, next_asset} != {base, quote}:
                return {'error': f'Pair {pair} does not match assets {curr_asset}->{next_asset}'}, None
            # If we hold BASE and want QUOTE, we SELL BASE for QUOTE: QUOTE = BASE * price
            if curr_asset == base and next_asset == quote:
                amt_out = amt_in * price
                direction = 'SELL'
            # If we hold QUOTE and want BASE, we BUY BASE with QUOTE: BASE = QUOTE / price
            elif curr_asset == quote and next_asset == base:
                # Guard divide by zero
                if not price:
                    return {'error': f'Zero price for {pair}'}, None
                amt_out = amt_in / price
                direction = 'BUY'
            else:
                return {'error': f'Unsupported direction for {pair} {curr_asset}->{next_asset}'}, None
            amt_after_fee = amt_out * (1 - self.taker_fee)
            step = {
                'pair': pair,
                'direction': direction,
                'price': price,
                'amount_before': amt_in,
                'amount_after': amt_after_fee,
                'fee': abs(amt_out - amt_after_fee),
            }
            return None, step

        # Step 1
        pair1 = pairs[0]
        price1 = prices[pair1]
        err, s1 = _apply_step(path[0], path[1], pair1, price1, amount)
        if err:
            return err
        steps.append(s1)
        amount1_after_fee = s1['amount_after']

        # Step 2
        pair2 = pairs[1]
        price2 = prices[pair2]
        err, s2 = _apply_step(path[1], path[2], pair2, price2, amount1_after_fee)
        if err:
            return err
        steps.append(s2)
        amount2_after_fee = s2['amount_after']

        # Step 3 (back to starting currency)
        pair3 = pairs[2]
        price3 = prices[pair3]
        err, s3 = _apply_step(path[2], path[3], pair3, price3, amount2_after_fee)
        if err:
            return err
        steps.append(s3)
        amount3_after_fee = s3['amount_after']

        # Apply slippage to final amount
        final_amount = amount3_after_fee * (1 - self.max_slippage)
        profit = final_amount - initial_amount
        profit_percent = (profit / initial_amount) * 100
        
        return {
            'triangle': triangle,
            'initial_amount': initial_amount,
            'final_amount': final_amount,
            'profit': profit,
            'profit_percent': profit_percent,
            'is_profitable': profit_percent >= Config.MIN_PROFIT_THRESHOLD,
            'steps': steps
        }
    
    def find_all_opportunities(
        self,
        triangles: List[Dict],
        prices: Dict[str, float],
        initial_amount: float
    ) -> List[Dict]:
        """
        Scan all triangles for opportunities
        """
        opportunities = []
        
        for triangle in triangles:
            result = self.calculate_precise_triangular(triangle, prices, initial_amount)
            
            if 'error' not in result and result['is_profitable']:
                opportunities.append(result)
        
        # Sort by profit percentage (descending)
        opportunities.sort(key=lambda x: x['profit_percent'], reverse=True)
        
        return opportunities
    
    def calculate_optimal_trade_size(
        self,
        triangle: Dict,
        prices: Dict[str, float],
        max_amount: float
    ) -> float:
        """
        Calculate optimal trade size considering liquidity
        """
        # Start with max allowed trade size
        optimal_size = min(Config.INITIAL_CAPITAL, max_amount, Config.MAX_TRADE_SIZE)
        
        # Could add more sophisticated logic here based on order book depth
        
        return optimal_size
