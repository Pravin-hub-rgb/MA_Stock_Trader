#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVRO Gap Validation Test
Tests SVRO gap validation requirements (0.3% to 5% gap up)
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
logger = logging.getLogger('SVROGapValidation')


def test_svro_gap_validation():
    """Test SVRO gap validation requirements"""
    print("🧪 Testing SVRO Gap Validation Requirements")
    print("=" * 50)
    
    monitor = StockMonitor()
    
    # Test cases for SVRO gap validation
    test_cases = [
        {
            'symbol': 'TEST_FLAT',
            'prev_close': 100.0,
            'open_price': 100.2,  # 0.2% - should be rejected (too flat)
            'expected_valid': False,
            'reason': 'Gap too flat (< 0.3%)'
        },
        {
            'symbol': 'TEST_SVRO_MIN',
            'prev_close': 100.0,
            'open_price': 100.4,  # 0.4% - should pass (minimum SVRO)
            'expected_valid': True,
            'reason': 'Minimum SVRO gap (0.4%)'
        },
        {
            'symbol': 'TEST_SVRO_NORMAL',
            'prev_close': 100.0,
            'open_price': 102.0,  # 2.0% - should pass (normal SVRO)
            'expected_valid': True,
            'reason': 'Normal SVRO gap (2.0%)'
        },
        {
            'symbol': 'TEST_SVRO_MAX',
            'prev_close': 100.0,
            'open_price': 105.0,  # 5.0% - should pass (maximum SVRO)
            'expected_valid': True,
            'reason': 'Maximum SVRO gap (5.0%)'
        },
        {
            'symbol': 'TEST_SVRO_TOO_HIGH',
            'prev_close': 100.0,
            'open_price': 105.1,  # 5.1% - should be rejected (too high)
            'expected_valid': False,
            'reason': 'Gap too high (> 5%)'
        },
        {
            'symbol': 'TEST_GAP_DOWN',
            'prev_close': 100.0,
            'open_price': 99.0,  # -1.0% - should be rejected (gap down)
            'expected_valid': False,
            'reason': 'Gap down (not SVRO)'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        # Add stock to monitor
        monitor.add_stock(
            symbol=test_case['symbol'],
            instrument_key=f"{test_case['symbol']}_KEY",
            previous_close=test_case['prev_close'],
            situation='continuation'
        )
        
        # Get the stock
        stock = monitor.stocks[f"{test_case['symbol']}_KEY"]
        
        # Set opening price
        stock.set_open_price(test_case['open_price'])
        
        # Validate gap
        is_valid = stock.validate_gap()
        
        # Check result
        passed = is_valid == test_case['expected_valid']
        
        result = {
            'symbol': test_case['symbol'],
            'prev_close': test_case['prev_close'],
            'open_price': test_case['open_price'],
            'gap_pct': ((test_case['open_price'] - test_case['prev_close']) / test_case['prev_close']) * 100,
            'expected_valid': test_case['expected_valid'],
            'actual_valid': is_valid,
            'passed': passed,
            'reason': test_case['reason']
        }
        
        results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        gap_type = "up" if result['gap_pct'] >= 0 else "down"
        
        print(f"{status} {test_case['symbol']}: {gap_type} {result['gap_pct']:+.1f}% - {test_case['reason']}")
        if not passed:
            print(f"     Expected: {test_case['expected_valid']}, Got: {is_valid}")
    
    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\n📊 Gap Validation Results: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("🎉 All SVRO gap validation tests PASSED!")
        return True
    else:
        print("❌ Some SVRO gap validation tests FAILED!")
        return False


if __name__ == "__main__":
    success = test_svro_gap_validation()
    sys.exit(0 if success else 1)