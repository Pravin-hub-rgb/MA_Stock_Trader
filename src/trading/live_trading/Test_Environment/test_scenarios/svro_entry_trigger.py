#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVRO Entry Trigger Test
Tests SVRO entry trigger logic (price breaking entry high)
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.live_trading.continuation_stock_monitor import StockMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('SVROEntryTrigger')


def test_svro_entry_trigger():
    """Test SVRO entry trigger logic"""
    print("🧪 Testing SVRO Entry Trigger Logic")
    print("=" * 50)
    
    monitor = StockMonitor()
    
    # Add test stock
    monitor.add_stock(
        symbol='TEST_SVRO',
        instrument_key='TEST_SVRO_KEY',
        previous_close=100.0,
        situation='continuation'
    )
    
    stock = monitor.stocks['TEST_SVRO_KEY']
    
    # Set up stock state for SVRO entry
    stock.set_open_price(102.0)  # Gap up 2%
    stock.validate_gap()  # Should pass
    stock.check_low_violation()  # Should pass
    stock.volume_validated = True  # Simulate volume validation
    stock.early_volume = 100000.0  # Sufficient volume
    stock.volume_baseline = 1000000.0
    
    # Prepare entry (simulates 9:20 preparation)
    stock.entry_high = 103.0  # Entry high set to 103.0
    stock.entry_sl = 103.0 * 0.96  # 4% below entry high = 98.88
    stock.entry_ready = True
    
    print(f"Stock setup:")
    print(f"  Open Price: {stock.open_price}")
    print(f"  Entry High: {stock.entry_high}")
    print(f"  Entry SL: {stock.entry_sl:.2f}")
    print(f"  Entry Ready: {stock.entry_ready}")
    print(f"  Gap Validated: {stock.gap_validated}")
    print(f"  Low Violation Checked: {stock.low_violation_checked}")
    print(f"  Volume Validated: {stock.volume_validated}")
    
    # Test entry trigger scenarios
    test_scenarios = [
        {
            'price': 102.5,
            'expected_trigger': False,
            'reason': 'Price below entry high'
        },
        {
            'price': 103.0,
            'expected_trigger': True,
            'reason': 'Price equals entry high'
        },
        {
            'price': 103.5,
            'expected_trigger': True,
            'reason': 'Price above entry high'
        },
        {
            'price': 98.0,
            'expected_trigger': False,
            'reason': 'Price below entry high (and SL)'
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        # Update stock price
        stock.update_price(scenario['price'], datetime.now())
        
        # Check entry signal
        should_trigger = stock.check_entry_signal(scenario['price'])
        
        # Check result
        passed = should_trigger == scenario['expected_trigger']
        
        result = {
            'price': scenario['price'],
            'expected_trigger': scenario['expected_trigger'],
            'actual_trigger': should_trigger,
            'passed': passed,
            'reason': scenario['reason']
        }
        
        results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        
        print(f"{status} Price {scenario['price']:.2f} - {scenario['reason']}")
        print(f"     Expected: {scenario['expected_trigger']}, Got: {should_trigger}")
    
    # Test entry execution
    print(f"\n🎯 Testing Entry Execution")
    
    # Reset stock state
    stock.entered = False
    stock.entry_price = None
    stock.entry_time = None
    
    # Trigger entry at price 103.5
    trigger_price = 103.5
    stock.update_price(trigger_price, datetime.now())
    
    if stock.check_entry_signal(trigger_price):
        entry_time = datetime.now()
        stock.enter_position(trigger_price, entry_time)
        
        print(f"✅ Entry triggered successfully!")
        print(f"   Entry Price: {stock.entry_price}")
        print(f"   Entry Time: {stock.entry_time}")
        print(f"   Entered: {stock.entered}")
        print(f"   Entry High: {stock.entry_high}")
        print(f"   Entry SL: {stock.entry_sl:.2f}")
        
        entry_test_passed = True
    else:
        print(f"❌ Entry trigger failed!")
        entry_test_passed = False
    
    # Summary
    trigger_passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\n📊 Entry Trigger Results: {trigger_passed_count}/{total_count} passed")
    
    overall_success = (trigger_passed_count == total_count) and entry_test_passed
    
    if overall_success:
        print("🎉 All SVRO entry trigger tests PASSED!")
        return True
    else:
        print("❌ Some SVRO entry trigger tests FAILED!")
        return False


if __name__ == "__main__":
    success = test_svro_entry_trigger()
    sys.exit(0 if success else 1)