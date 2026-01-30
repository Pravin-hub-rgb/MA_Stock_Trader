#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVRO Volume Validation Test
Tests SVRO volume validation requirements (7.5% of mean volume baseline)
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
logger = logging.getLogger('SVROVolumeValidation')


def test_svro_volume_validation():
    """Test SVRO volume validation requirements (7.5% threshold)"""
    print("🧪 Testing SVRO Volume Validation Requirements")
    print("=" * 50)
    
    monitor = StockMonitor()
    
    # Test cases for SVRO volume validation
    test_cases = [
        {
            'symbol': 'TEST_LOW_VOL',
            'volume_baseline': 1000000.0,
            'early_volume': 50000.0,  # 5% - should be rejected (< 7.5%)
            'expected_valid': False,
            'reason': 'Volume too low (< 7.5%)'
        },
        {
            'symbol': 'TEST_MIN_VOL',
            'volume_baseline': 1000000.0,
            'early_volume': 75000.0,  # 7.5% - should pass (minimum SVRO)
            'expected_valid': True,
            'reason': 'Minimum SVRO volume (7.5%)'
        },
        {
            'symbol': 'TEST_NORMAL_VOL',
            'volume_baseline': 1000000.0,
            'early_volume': 150000.0,  # 15% - should pass (normal SVRO)
            'expected_valid': True,
            'reason': 'Normal SVRO volume (15%)'
        },
        {
            'symbol': 'TEST_HIGH_VOL',
            'volume_baseline': 1000000.0,
            'early_volume': 300000.0,  # 30% - should pass (high SVRO)
            'expected_valid': True,
            'reason': 'High SVRO volume (30%)'
        },
        {
            'symbol': 'TEST_LOW_BASELINE',
            'volume_baseline': 500000.0,  # Lower baseline
            'early_volume': 37500.0,  # 7.5% of 500K
            'expected_valid': True,
            'reason': '7.5% of lower baseline'
        },
        {
            'symbol': 'TEST_ZERO_BASELINE',
            'volume_baseline': 0.0,  # Zero baseline
            'early_volume': 100000.0,
            'expected_valid': False,
            'reason': 'Zero volume baseline'
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        # Add stock to monitor
        monitor.add_stock(
            symbol=test_case['symbol'],
            instrument_key=f"{test_case['symbol']}_KEY",
            previous_close=100.0,  # Dummy value
            situation='continuation'
        )
        
        # Get the stock
        stock = monitor.stocks[f"{test_case['symbol']}_KEY"]
        
        # Set volume baseline and early volume
        stock.volume_baseline = test_case['volume_baseline']
        stock.early_volume = test_case['early_volume']
        
        # Validate volume
        is_valid = stock.validate_volume(test_case['volume_baseline'])
        
        # Check result
        passed = is_valid == test_case['expected_valid']
        
        result = {
            'symbol': test_case['symbol'],
            'volume_baseline': test_case['volume_baseline'],
            'early_volume': test_case['early_volume'],
            'volume_pct': (test_case['early_volume'] / test_case['volume_baseline'] * 100) if test_case['volume_baseline'] > 0 else 0,
            'expected_valid': test_case['expected_valid'],
            'actual_valid': is_valid,
            'passed': passed,
            'reason': test_case['reason']
        }
        
        results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        volume_pct = result['volume_pct']
        
        print(f"{status} {test_case['symbol']}: {volume_pct:.1f}% - {test_case['reason']}")
        if not passed:
            print(f"     Expected: {test_case['expected_valid']}, Got: {is_valid}")
            print(f"     Volume: {test_case['early_volume']:,.0f}, Baseline: {test_case['volume_baseline']:,.0f}")
    
    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\n📊 Volume Validation Results: {passed_count}/{total_count} passed")
    
    if passed_count == total_count:
        print("🎉 All SVRO volume validation tests PASSED!")
        return True
    else:
        print("❌ Some SVRO volume validation tests FAILED!")
        return False


if __name__ == "__main__":
    success = test_svro_volume_validation()
    sys.exit(0 if success else 1)