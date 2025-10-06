"""
Trading execution module
Handles actual trade execution and order management
"""

import time
from typing import Dict, List, Optional
from config import Config
from logger import logger
from exchange import BinanceExchange

class TradeExecutor:
    """Execute arbitrage trades"""
    
    def __init__(self, exchange: BinanceExchange):
        self.exchange = exchange
        self.total_profit = 0
        self.total_trades = 0
        self.failed_trades = 0
    
    def execute_triangle(self, opportunity: Dict) -> Dict:
        """
        Execute a triangular arbitrage opportunity
        
        Returns dict with execution results
        """
        triangle = opportunity['triangle']
        steps = opportunity['steps']
        
        logger.info(f"🚀 Executing triangle: {' -> '.join(triangle['path'])}")
        
        execution_results = {
            'success': False,
            'triangle': triangle,
            'steps_executed': [],
            'total_profit': 0,
            'error': None
        }
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(steps):
                step_result = self._execute_step(step)
                
                if not step_result['success']:
                    execution_results['error'] = f"Step {i+1} failed: {step_result['error']}"
                    logger.error(execution_results['error'])
                    
                    # Attempt to reverse executed trades (if any)
                    if i > 0:
                        logger.warning("Attempting to reverse previous trades...")
                        self._reverse_trades(execution_results['steps_executed'])
                    
                    return execution_results
                
                execution_results['steps_executed'].append(step_result)
                
                # Small delay between trades to avoid issues
                time.sleep(0.1)
            
            # Calculate actual profit
            execution_results['success'] = True
            execution_results['total_profit'] = self._calculate_actual_profit(
                execution_results['steps_executed'],
                triangle,
                opportunity.get('initial_amount', 0.0)
            )
            
            self.total_profit += execution_results['total_profit']
            self.total_trades += 1
            
            logger.info(f"✅ Triangle executed successfully! Profit: {execution_results['total_profit']:.2f}")
            
        except Exception as e:
            execution_results['error'] = str(e)
            self.failed_trades += 1
            logger.error(f"Trade execution error: {e}")
        
        return execution_results
    
    def _execute_step(self, step: Dict) -> Dict:
        """
        Execute a single trading step
        """
        pair = step['pair']
        direction = step['direction']  # 'BUY' or 'SELL'
        amount = step['amount_before']
        
        result = {
            'success': False,
            'pair': pair,
            'direction': direction,
            'order_id': None,
            'executed_qty': 0,
            'executed_price': 0,
            'error': None
        }
        
        try:
            # Get symbol info for precision
            symbol_info = self.exchange.get_symbol_info(pair)
            if not symbol_info:
                result['error'] = f"Could not get symbol info for {pair}"
                return result
            
            # Format quantity according to symbol precision and notional
            quantity = self._format_quantity(amount, symbol_info, step.get('price', 0) or 0)
            if quantity <= 0:
                result['error'] = "Quantity below exchange limits"
                return result
            
            # Place market order
            order = self.exchange.place_market_order(pair, direction, quantity)
            
            if order and 'orderId' in order:
                result['success'] = True
                result['order_id'] = order['orderId']
                result['executed_qty'] = float(order.get('executedQty', quantity))
                result['executed_price'] = float(order.get('price', step['price']))
            else:
                result['error'] = "Order placement failed"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Step execution error: {e}")
        
        return result
    
    def _format_quantity(self, quantity: float, symbol_info: Dict, price: float) -> float:
        """Format quantity according to symbol's LOT_SIZE and MIN_NOTIONAL."""
        filters = symbol_info.get('filters', [])
        step_size = None
        min_qty = None
        min_notional = None
        for f in filters:
            if f.get('filterType') == 'LOT_SIZE':
                step_size = float(f.get('stepSize', 0) or 0)
                min_qty = float(f.get('minQty', 0) or 0)
            if f.get('filterType') == 'MIN_NOTIONAL':
                min_notional = float(f.get('minNotional', 0) or 0)
        # Apply min qty
        if min_qty:
            quantity = max(quantity, min_qty)
        # Apply step size (round down)
        if step_size and step_size > 0:
            # Use integer steps to avoid float errors
            steps = int(quantity / step_size)
            quantity = steps * step_size
        # Enforce min notional
        if price and min_notional:
            notional = quantity * price
            if notional < min_notional:
                return 0.0
        return quantity
    
    def _calculate_actual_profit(self, steps: List[Dict], triangle: Dict, initial_amount: float) -> float:
        """Calculate actual profit from executed trades using executed qty/price and taker fee.
        Assumes the 3 trades complete a closed loop back to triangle['path'][0]."""
        if not steps:
            return 0.0
        try:
            start_asset = triangle['path'][0]
            holdings = {start_asset: float(initial_amount)}
            for idx, step in enumerate(steps):
                pair = step['pair']
                direction = step['direction']
                executed_qty = float(step.get('executed_qty', 0) or 0)
                executed_price = float(step.get('executed_price', step.get('price', 0) or 0))
                info = self.exchange.get_symbol_info(pair)
                if not info:
                    continue
                base = info.get('baseAsset')
                quote = info.get('quoteAsset')
                fee_factor = (1 - Config.TAKER_FEE)
                if direction == 'BUY':
                    # Spent quote, received base
                    spent_quote = executed_qty * executed_price
                    received_base = executed_qty * fee_factor
                    holdings[quote] = holdings.get(quote, 0.0) - spent_quote
                    holdings[base] = holdings.get(base, 0.0) + received_base
                else:  # SELL
                    # Sold base, received quote
                    sold_base = executed_qty
                    received_quote = executed_qty * executed_price * fee_factor
                    holdings[base] = holdings.get(base, 0.0) - sold_base
                    holdings[quote] = holdings.get(quote, 0.0) + received_quote
            # After 3 steps, we should be back to start asset; profit is delta in start asset
            final_amount = holdings.get(start_asset, 0.0)
            return final_amount - float(initial_amount)
        except Exception as e:
            logger.error(f"PNL calculation error: {e}")
            return 0.0
    
    def _reverse_trades(self, executed_steps: List[Dict]):
        """
        Attempt to reverse executed trades (emergency recovery)
        This is a best-effort approach
        """
        logger.warning("⚠️ Attempting trade reversal (best effort)")
        
        for step in reversed(executed_steps):
            try:
                # Reverse the trade direction
                reverse_direction = 'SELL' if step['direction'] == 'BUY' else 'BUY'
                
                self.exchange.place_market_order(
                    step['pair'],
                    reverse_direction,
                    step['executed_qty']
                )
                
                logger.info(f"Reversed trade on {step['pair']}")
                
            except Exception as e:
                logger.error(f"Failed to reverse trade on {step['pair']}: {e}")
    
    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        success_rate = 0
        if self.total_trades > 0:
            success_rate = ((self.total_trades - self.failed_trades) / self.total_trades) * 100
        
        return {
            'total_trades': self.total_trades,
            'failed_trades': self.failed_trades,
            'success_rate': success_rate,
            'total_profit': self.total_profit,
            'avg_profit_per_trade': self.total_profit / max(self.total_trades, 1)
        }
    
    def dry_run_execute(self, opportunity: Dict) -> Dict:
        """
        Simulate trade execution without actually placing orders
        Useful for testing and paper trading
        """
        triangle = opportunity['triangle']
        
        logger.info(f"🧪 DRY RUN: Simulating triangle {' -> '.join(triangle['path'])}")
        logger.info(f"Expected profit: {opportunity['profit']:.2f} ({opportunity['profit_percent']:.2f}%)")
        
        return {
            'success': True,
            'triangle': triangle,
            'simulated_profit': opportunity['profit'],
            'note': 'This was a dry run - no actual trades executed'
        }
