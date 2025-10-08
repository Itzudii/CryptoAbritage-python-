"""
Trading execution module
Handles actual trade execution and order management
"""

import time
from exchange import BinanceExchange
from config import Config
from logger import logger
import time
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, getcontext
from liquidity import LiquidityChecker, LiquidityCheckResult
from notifications import send_risk_alert, AlertLevel

class TradeExecutor:
    """Execute arbitrage trades"""
    
    def __init__(self, exchange: BinanceExchange):
        self.exchange = exchange
        self.total_profit = 0
        self.total_trades = 0
        self.failed_trades = 0
        self.liquidity_checker = LiquidityChecker(exchange)
        self._last_liquidity_check = {}
        self._liquidity_cache_ttl = 5.0  # Cache liquidity checks for 5 seconds
    
    def _check_liquidity(self, opportunity: Dict) -> Tuple[bool, Optional[str], List[LiquidityCheckResult]]:
        """Check if there's sufficient liquidity for the entire triangle."""
        triangle_key = '->'.join(opportunity['triangle']['path'])
        current_time = time.time()
        
        # Check cache first
        if triangle_key in self._last_liquidity_check:
            last_check_time, last_result = self._last_liquidity_check[triangle_key]
            if current_time - last_check_time < self._liquidity_cache_ttl:
                return last_result
        
        # Perform liquidity check
        is_viable, results = self.liquidity_checker.validate_triangle_liquidity(
            opportunity, 
            opportunity.get('initial_amount', 0)
        )
        
        # Cache the result
        self._last_liquidity_check[triangle_key] = (current_time, (is_viable, None if is_viable else "Insufficient liquidity", results))
        
        if not is_viable:
            # Log the specific reasons for rejection
            for i, result in enumerate(results):
                if not result.is_sufficient:
                    logger.warning(f"Liquidity check failed on step {i+1}: {result.message}")
                    
                    # Send alert for critical liquidity issues
                    if result.estimated_slippage > Config.MAX_SLIPPAGE * 100:  # Convert to percentage
                        send_risk_alert(
                            "High Slippage Detected",
                            {
                                "symbol": opportunity['steps'][i]['pair'],
                                "estimated_slippage": f"{result.estimated_slippage:.4f}%",
                                "max_allowed": f"{Config.MAX_SLIPPAGE * 100:.2f}%",
                                "required_volume": f"{result.required_volume:.2f} USDT",
                                "available_volume": f"{result.available_volume:.2f} USDT"
                            },
                            AlertLevel.WARNING,
                            {"triangle": opportunity['triangle'].get('path', [])}
                        )
        
        return is_viable, None if is_viable else "Insufficient liquidity", results

    def execute_triangle(self, opportunity: Dict) -> Dict:
        """
        Execute a triangular arbitrage opportunity
        
        Returns dict with execution results
        """
        triangle = opportunity['triangle']
        steps = opportunity['steps']
        
        logger.info(f"🚀 Executing triangle: {' -> '.join(triangle['path'])}")
        
        # Check liquidity before proceeding
        is_viable, reason, liquidity_results = self._check_liquidity(opportunity)
        if not is_viable:
            return {
                'success': False,
                'triangle': triangle,
                'steps_executed': [],
                'total_profit': 0,
                'error': reason,
                'liquidity_checks': [r.to_dict() for r in liquidity_results] if liquidity_results else []
            }
        
        start_ts = time.time()
        execution_results = {
            'success': False,
            'triangle': triangle,
            'steps_executed': [],
            'total_profit': 0,
            'error': None,
            'liquidity_checks': [r.to_dict() for r in liquidity_results] if liquidity_results else [],
            'execution_time': 0.0,
        }
        
        try:
            # Execute each step in sequence with timeouts
            for i, step in enumerate(steps):
                # Enforce full-triangle timeout budget
                if (time.time() - start_ts) > Config.FULL_TRIANGLE_TIMEOUT_SEC:
                    execution_results['error'] = f"Full triangle timeout > {Config.FULL_TRIANGLE_TIMEOUT_SEC}s"
                    logger.error(execution_results['error'])
                    # Attempt to reverse any executed trades
                    if execution_results['steps_executed']:
                        logger.warning("Attempting to reverse previous trades due to timeout...")
                        self._reverse_trades(execution_results['steps_executed'])
                    return execution_results

                step_result = self._execute_step(step)
                
                if not step_result['success']:
                    execution_results['error'] = f"Step {i+1} failed: {step_result['error']}"
                    logger.error(execution_results['error'])
                    
                    # Attempt to reverse executed trades (if any)
                    if i > 0:
                        logger.warning("Attempting to reverse previous trades...")
                        self._reverse_trades(execution_results['steps_executed'])
                    
                    return execution_results

                # Enforce minimum fill ratio
                req_qty = float(step_result.get('requested_qty', 0) or 0)
                exec_qty = float(step_result.get('executed_qty', 0) or 0)
                fill_ratio = (exec_qty / req_qty) if req_qty > 0 else 1.0
                if fill_ratio < Config.MIN_FILL_RATIO:
                    execution_results['error'] = (
                        f"Fill ratio {fill_ratio:.3f} < min {Config.MIN_FILL_RATIO:.3f} on {step_result.get('pair')}"
                    )
                    logger.error(execution_results['error'])
                    # Reverse prior trades (including this partial one best-effort)
                    self._reverse_trades(execution_results['steps_executed'] + [step_result])
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
            execution_results['execution_time'] = time.time() - start_ts
            
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
        Execute a single trading step with enhanced error handling and monitoring
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
            'requested_qty': 0,
            'error': None,
            'timestamp': time.time(),
            'latency_ms': 0
        }
        
        start_time = time.time()
        
        try:
            # Enforce single trade timeout
            if time.time() - start_time > Config.SINGLE_TRADE_TIMEOUT_SEC:
                result['error'] = f"Single trade timeout after {Config.SINGLE_TRADE_TIMEOUT_SEC}s"
                logger.error(f"{pair} {direction} {amount} - {result['error']}")
                return result
                
            # Get symbol info for precision
            symbol_info = self.exchange.get_symbol_info(pair)
            if not symbol_info:
                result['error'] = f"Could not get symbol info for {pair}"
                logger.error(result['error'])
                return result
            
            # Format quantity according to symbol precision and notional
            quantity = self._format_quantity(amount, symbol_info, step.get('price', 0) or 0)
            if quantity <= 0:
                result['error'] = "Quantity below exchange limits"
                return result
            result['requested_qty'] = float(quantity)
            
            # Record requested quantity for fill ratio calculation
            result['requested_qty'] = float(quantity)
            
            # Place market order with timeout
            order_start = time.time()
            try:
                order = self.exchange.place_market_order(pair, direction, quantity)
                result['latency_ms'] = (time.time() - order_start) * 1000
                if not order:
                    result['error'] = "Order placement returned no data"
                    return result
                # Populate result fields from exchange response
                result['order_id'] = order.get('orderId')
                executed_qty = float(order.get('executedQty', 0) or 0)
                result['executed_qty'] = executed_qty
                # Determine executed price
                cum_quote = float(order.get('cummulativeQuoteQty', 0) or 0)
                if executed_qty > 0 and cum_quote > 0:
                    result['executed_price'] = cum_quote / executed_qty
                else:
                    fills = order.get('fills', [])
                    if fills:
                        total_cost = sum(float(f.get('price', 0)) * float(f.get('qty', 0)) for f in fills)
                        total_qty = sum(float(f.get('qty', 0)) for f in fills)
                        if total_qty > 0:
                            result['executed_price'] = total_cost / total_qty
                # Mark success if we executed any quantity
                result['success'] = executed_qty > 0
            except Exception as oe:
                result['error'] = str(oe)
                result['latency_ms'] = (time.time() - order_start) * 1000
                logger.error(f"Order placement failed for {pair} {direction} {quantity}: {oe}")
                return result
                
        except Exception as e:
            result['error'] = str(e)
            result['latency_ms'] = (time.time() - start_time) * 1000
            logger.error(f"{pair} {direction} {amount} - Step execution error: {e}")
            
            # Send alert for execution error
            send_risk_alert(
                "Trade Execution Error",
                {
                    "symbol": pair,
                    "side": direction,
                    "amount": amount,
                    "error": str(e)
                },
                AlertLevel.CRITICAL
            )
        
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
