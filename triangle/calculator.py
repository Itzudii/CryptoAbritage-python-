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
        
        # Step 1: First conversion
        pair1 = pairs[0]
        price1 = prices[pair1]
        
        # Determine if buying or selling
        if pair1.endswith(path[0]):
            # Buying quote with base (e.g., BTCUSDT - buying BTC with USDT)
            amount1 = amount / price1
            direction1 = 'BUY'
        else:
            # Selling base for quote (e.g., USDTBTC - selling USDT for BTC)
            amount1 = amount * price1
            direction1 = 'SELL'
        
        amount1_after_fee = amount1 * (1 - self.taker_fee)
        steps.append({
            'pair': pair1,
            'direction': direction1,
            'price': price1,
            'amount_before': amount,
            'amount_after': amount1_after_fee,
            'fee': amount1 * self.taker_fee
        })
        
        # Step 2: Second conversion
        pair2 = pairs[1]
        price2 = prices[pair2]
        
        if pair2.endswith(path[1]):
            amount2 = amount1_after_fee / price2
            direction2 = 'BUY'
        else:
            amount2 = amount1_after_fee * price2
            direction2 = 'SELL'
        
        amount2_after_fee = amount2 * (1 - self.taker_fee)
        steps.append({
            'pair': pair2,
            'direction': direction2,
            'price': price2,
            'amount_before': amount1_after_fee,
            'amount_after': amount2_after_fee,
            'fee': amount2 * self.taker_fee
        })
        
        # Step 3: Third conversion (back to starting currency)
        pair3 = pairs[2]
        price3 = prices[pair3]
        
        if pair3.startswith(path[3]):
            amount3 = amount2_after_fee * price3
            direction3 = 'SELL'
        else:
            amount3 = amount2_after_fee / price3
            direction3 = 'BUY'
        
        amount3_after_fee = amount3 * (1 - self.taker_fee)
        steps.append({
            'pair': pair3,
            'direction': direction3,
            'price': price3,
            'amount_before': amount2_after_fee,
            'amount_after': amount3_after_fee,
            'fee': amount3 * self.taker_fee
        })
        
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
