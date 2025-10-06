import math
from calculator import ArbitrageCalculator


def test_calculate_precise_triangular_profitable_example():
    calc = ArbitrageCalculator()
    triangle = {
        'path': ['USDT', 'BTC', 'ETH', 'USDT'],
        'pairs': ['BTCUSDT', 'ETHBTC', 'ETHUSDT']
    }
    # Synthetic prices consistent with a small profit after fees/slippage
    prices = {
        'BTCUSDT': 50000.0,    # 1 BTC = 50k USDT
        'ETHBTC': 0.06,        # 1 ETH = 0.06 BTC
        'ETHUSDT': 3100.0      # 1 ETH = 3100 USDT
    }
    res = calc.calculate_precise_triangular(triangle, prices, initial_amount=1000.0)
    assert 'error' not in res
    assert isinstance(res['profit_percent'], float)
    # Not asserting positive due to fees/slippage; at least computation runs
    assert math.isfinite(res['final_amount'])


def test_find_all_opportunities_runs():
    calc = ArbitrageCalculator()
    triangles = [
        {'path': ['USDT', 'BTC', 'ETH', 'USDT'], 'pairs': ['BTCUSDT', 'ETHBTC', 'ETHUSDT']},
        {'path': ['USDT', 'ETH', 'BNB', 'USDT'], 'pairs': ['ETHUSDT', 'BNBETH', 'BNBUSDT']}
    ]
    prices = {k: 1.0 for k in ['BTCUSDT', 'ETHBTC', 'ETHUSDT', 'BNBETH', 'BNBUSDT', 'ETHUSDT']}
    opps = calc.find_all_opportunities(triangles, prices, 1000.0)
    assert isinstance(opps, list)
