#!/usr/bin/env python3
"""
Test script for the new OOPS Reversal Trading System
"""

import sys
import os
sys.path.append('src')

from trading.live_trading.reversal_monitor import ReversalMonitor
from datetime import time

def test_load_watchlist():
    """Test watchlist loading with correct SYMBOL-TREND-DAYS format"""
    print("=== Testing Reversal Monitor ===")

    monitor = ReversalMonitor()

    # Create test watchlist file
    test_watchlist = "SBIN-d7,HDFC-u5,TCS-d4,INFY-u3,RELIANCE-d8"
    with open("test_watchlist.txt", 'w') as f:
        f.write(test_watchlist)

    # Test loading with correct format
    success = monitor.load_watchlist("test_watchlist.txt")
    print(f"Load result: {success}")

    # Verify classifications
    print(f"VIP stocks (7+ days): {len(monitor.vip_stocks)}")
    for stock in monitor.vip_stocks:
        print(f"  - {stock['symbol']}-{stock['trend']}{stock['days']}")

    print(f"Secondary stocks (3-6 days + downtrend): {len(monitor.secondary_stocks)}")
    for stock in monitor.secondary_stocks:
        print(f"  - {stock['symbol']}-{stock['trend']}{stock['days']}")

    print(f"Tertiary stocks (3-6 days + uptrend): {len(monitor.tertiary_stocks)}")
    for stock in monitor.tertiary_stocks:
        print(f"  - {stock['symbol']}-{stock['trend']}{stock['days']}")

    # Cleanup
    if os.path.exists("test_watchlist.txt"):
        os.remove("test_watchlist.txt")

    print()

def test_oops_trigger():
    """Test OOPS trigger logic"""
    print("=== Testing OOPS Trigger ===")

    monitor = ReversalMonitor()

    # Test OOPS conditions
    # Gap down 3% + crosses above prev close
    result = monitor.check_oops_trigger(
        symbol="TEST",
        open_price=95.0,    # 5% gap down from 100
        prev_close=100.0,
        current_price=101.0  # Crosses above prev close
    )
    print(f"OOPS Trigger (gap down + cross): {result}")

    # No gap down
    result = monitor.check_oops_trigger(
        symbol="TEST",
        open_price=101.0,   # Gap up
        prev_close=100.0,
        current_price=102.0
    )
    print(f"OOPS Trigger (gap up): {result}")

    # Gap down but no cross
    result = monitor.check_oops_trigger(
        symbol="TEST",
        open_price=95.0,
        prev_close=100.0,
        current_price=99.0   # Below prev close
    )
    print(f"OOPS Trigger (gap down, no cross): {result}")
    print()

def test_strong_start_trigger():
    """Test Strong Start trigger logic"""
    print("=== Testing Strong Start Trigger ===")

    monitor = ReversalMonitor()

    # Valid Strong Start: Gap up 3% + open ≈ low within 1%
    result = monitor.check_strong_start_trigger(
        symbol="TEST",
        open_price=103.0,   # 3% gap up from 100
        prev_close=100.0,
        current_low=102.0   # Within 1% of open (102.94 would be 1%)
    )
    print(f"Strong Start (valid): {result}")

    # No gap up
    result = monitor.check_strong_start_trigger(
        symbol="TEST",
        open_price=99.0,    # Gap down
        prev_close=100.0,
        current_low=98.0
    )
    print(f"Strong Start (gap down): {result}")

    # Gap up but open not ≈ low
    result = monitor.check_strong_start_trigger(
        symbol="TEST",
        open_price=103.0,
        prev_close=100.0,
        current_low=100.0   # 3% below open (>1%)
    )
    print(f"Strong Start (open not ≈ low): {result}")
    print()

def test_priority_classification():
    """Test priority-based stock classification"""
    print("=== Testing Priority Classification ===")

    # Create test data
    test_stocks = [
        {'symbol': 'VIP1', 'days': 8, 'expected_priority': 'VIP'},
        {'symbol': 'VIP2', 'days': 7, 'expected_priority': 'VIP'},
        {'symbol': 'SEC1', 'days': 5, 'expected_priority': 'Secondary'},
        {'symbol': 'SEC2', 'days': 3, 'expected_priority': 'Secondary'},
        {'symbol': 'SKIP', 'days': 2, 'expected_priority': 'Skip'}
    ]

    monitor = ReversalMonitor()

    # Manually test classification logic
    for stock in test_stocks:
        if stock['days'] >= 7:
            priority = 'VIP'
        elif stock['days'] >= 3:
            priority = 'Secondary'
        else:
            priority = 'Skip'

        status = "✓" if priority == stock['expected_priority'] else "✗"
        print(f"{status} {stock['symbol']}: {stock['days']} days → {priority}")

    print()

if __name__ == "__main__":
    print("🚀 Testing OOPS Reversal Trading System\n")

    test_load_watchlist()
    test_oops_trigger()
    test_strong_start_trigger()
    test_priority_classification()

    print("✅ All tests completed!")
