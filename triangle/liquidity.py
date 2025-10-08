"""
Liquidity assessment and validation for trading operations.
"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
from decimal import Decimal, getcontext

from exchange import BinanceExchange
from config import Config
from notifications import send_risk_alert, AlertLevel

# Set decimal precision for calculations
getcontext().prec = 8

@dataclass
class LiquidityCheckResult:
    """Result of a liquidity check."""
    is_sufficient: bool
    estimated_slippage: float  # as a percentage (e.g., 0.1 for 0.1%)
    available_volume: float     # in quote currency (e.g., USDT)
    required_volume: float      # in quote currency (e.g., USDT)
    message: str
    
    def to_dict(self) -> dict:
        return {
            'is_sufficient': self.is_sufficient,
            'estimated_slippage': self.estimated_slippage,
            'available_volume': self.available_volume,
            'required_volume': self.required_volume,
            'message': self.message
        }

class LiquidityChecker:
    """Validates if sufficient liquidity exists before trading."""
    
    def __init__(self, exchange: BinanceExchange):
        self.exchange = exchange
        self.min_liquidity_multiplier = 10.0  # Require 10x the trade size in order book
        self.max_allowed_slippage = Config.MAX_SLIPPAGE * 100  # Convert to percentage
        
    def check_market_depth(
        self, 
        symbol: str, 
        side: str, 
        quantity: float,
        price: float
    ) -> LiquidityCheckResult:
        """
        Check if sufficient liquidity exists in the order book.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'buy' or 'sell'
            quantity: Base currency amount to trade
            price: Expected price (for calculating quote value)
            
        Returns:
            LiquidityCheckResult with details on liquidity sufficiency
        """
        try:
            # Get order book
            orderbook = self.exchange.get_order_book(symbol, limit=50)
            if not orderbook or 'bids' not in orderbook or 'asks' not in orderbook:
                return LiquidityCheckResult(
                    is_sufficient=False,
                    estimated_slippage=0,
                    available_volume=0,
                    required_volume=quantity * price,
                    message=f"Failed to fetch order book for {symbol}"
                )
            
            # Calculate available volume and slippage
            levels = orderbook['asks'] if side.lower() == 'buy' else orderbook['bids']
            
            required_volume = Decimal(str(quantity)) * Decimal(str(price))
            available_volume = Decimal('0')
            cumulative_volume = Decimal('0')
            slippage = Decimal('0')
            
            # Calculate volume-weighted average price (VWAP) for the required quantity
            remaining_qty = Decimal(str(quantity))
            
            for level in levels:
                level_price = Decimal(str(level[0]))
                level_qty = Decimal(str(level[1]))
                
                # Calculate how much we can take from this level
                qty_to_take = min(remaining_qty, level_qty)
                
                # Update cumulative values
                level_volume = qty_to_take * level_price
                cumulative_volume += level_volume
                slippage += (level_price - Decimal(str(price))) * qty_to_take if side == 'buy' \
                          else (Decimal(str(price)) - level_price) * qty_to_take
                
                # Update remaining quantity
                remaining_qty -= qty_to_take
                
                # If we've matched the required quantity, stop
                if remaining_qty <= 0:
                    break
            
            # Calculate average slippage as a percentage of price
            avg_slippage_pct = float((slippage / Decimal(str(quantity)) / Decimal(str(price))) * 100) \
                if quantity > 0 and price > 0 else 0.0
            
            # Check if we have enough liquidity
            is_sufficient = (remaining_qty <= 0 and 
                           avg_slippage_pct <= self.max_allowed_slippage and
                           cumulative_volume >= required_volume * Decimal(str(self.min_liquidity_multiplier)))
            
            message = (f"{'✅' if is_sufficient else '❌'} {symbol} {side.upper()} "
                     f"(Qty: {quantity:.8f} @ ~{price:.8f})\n"
                     f"• Estimated slippage: {avg_slippage_pct:.4f}% "
                     f"(max: {self.max_allowed_slippage:.2f}%)\n"
                     f"• Available volume: {float(cumulative_volume):.2f} USDT "
                     f"(required: {float(required_volume):.2f} USDT)")
            
            if not is_sufficient:
                if remaining_qty > 0:
                    message += f"\n• Insufficient depth for full quantity (missing {float(remaining_qty):.8f} {symbol.split('USDT')[0]})"
                if avg_slippage_pct > self.max_allowed_slippage:
                    message += f"\n• Slippage exceeds maximum allowed ({avg_slippage_pct:.2f}% > {self.max_allowed_slippage:.2f}%)"
            
            return LiquidityCheckResult(
                is_sufficient=is_sufficient,
                estimated_slippage=float(avg_slippage_pct),
                available_volume=float(cumulative_volume),
                required_volume=float(required_volume),
                message=message
            )
            
        except Exception as e:
            error_msg = f"Liquidity check failed for {symbol}: {str(e)}"
            send_risk_alert(
                "Liquidity Check Error",
                {"error": str(e), "symbol": symbol, "side": side, "quantity": quantity},
                AlertLevel.WARNING
            )
            return LiquidityCheckResult(
                is_sufficient=False,
                estimated_slippage=0,
                available_volume=0,
                required_volume=quantity * price,
                message=error_msg
            )
    
    def validate_triangle_liquidity(
        self, 
        triangle: Dict[str, any],
        amount: float
    ) -> Tuple[bool, List[LiquidityCheckResult]]:
        """
        Validate liquidity for all legs of a triangular arbitrage opportunity.
        
        Args:
            triangle: The triangle opportunity details
            amount: Starting amount in quote currency (e.g., USDT)
            
        Returns:
            Tuple of (all_checks_passed, list_of_check_results)
        """
        steps = triangle.get('steps', [])
        if not steps:
            return False, []
        
        all_passed = True
        results = []
        current_amount = amount
        
        for step in steps:
            symbol = step.get('pair', '')
            side = step.get('direction', '').lower()
            price = step.get('price', 0)
            
            if not all([symbol, side, price > 0]):
                results.append(LiquidityCheckResult(
                    is_sufficient=False,
                    estimated_slippage=0,
                    available_volume=0,
                    required_volume=current_amount,
                    message=f"Invalid step in triangle: {step}"
                ))
                all_passed = False
                break
            
            # Calculate quantity based on current amount and price
            quantity = current_amount / price if side == 'buy' else current_amount
            
            # Check liquidity for this step
            result = self.check_market_depth(symbol, side, quantity, price)
            results.append(result)
            
            if not result.is_sufficient:
                all_passed = False
                
                # Send alert for insufficient liquidity
                send_risk_alert(
                    "Insufficient Liquidity",
                    {
                        "symbol": symbol,
                        "side": side.upper(),
                        "quantity": quantity,
                        "price": price,
                        "required_volume": result.required_volume,
                        "available_volume": result.available_volume,
                        "estimated_slippage": f"{result.estimated_slippage:.4f}%"
                    },
                    AlertLevel.WARNING,
                    {"triangle": triangle.get('path', [])}
                )
                
                # No need to check further steps if one fails
                break
            
            # Update current amount for next step
            if side == 'buy':
                current_amount = quantity  # Now we have the base currency
            else:
                current_amount = quantity * price  # Now we have the quote currency
        
        return all_passed, results
