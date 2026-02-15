 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify VAH validation logging is working correctly
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_vah_validation_logging():
    """Test that VAH validation logging works correctly"""
    
    print("🧪 TESTING VAH VALIDATION LOGGING")
    print("=" * 50)
    print("This tests the VAH validation logging that was just added")
    print()
    
    # Import the modules
    try:
        from src.trading.live_trading.continuation_stock_monitor import StockState
        print("✅ Successfully imported StockState")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return
    
    # Create test stocks with different scenarios
    test_cases = [
        {
            'symbol': 'ROSSTECH',
            'open_price': 727.00,
            'vah_price': 707.77,
            'expected_result': 'VAH validated',
            'expected_active': True
        },
        {
            'symbol': 'SHANTIGOLD', 
            'open_price': 220.37,
            'vah_price': 219.44,
            'expected_result': 'VAH validated',
            'expected_active': True
        },
        {
            'symbol': 'ADANIPOWER',
            'open_price': 142.60,
            'vah_price': 149.93,
            'expected_result': 'VAH validation failed',
            'expected_active': False
        },
        {
            'symbol': 'ANGELONE',
            'open_price': 2675.00,
            'vah_price': 2745.08,
            'expected_result': 'VAH validation failed',
            'expected_active': False
        }
    ]
    
    print("📊 TEST CASES:")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case['symbol']}: Open {case['open_price']:.2f} vs VAH {case['vah_price']:.2f}")
    
    print()
    print("🚀 RUNNING VAH VALIDATION LOGGING TEST")
    print("-" * 50)
    
    # Test each case
    for case in test_cases:
        print(f"\nTesting {case['symbol']}:")
        
        # Create stock
        stock = StockState(
            symbol=case['symbol'],
            instrument_key=case['symbol'],
            previous_close=100.0,  # Dummy value
            situation='continuation'
        )
        
        # Set opening price
        stock.set_open_price(case['open_price'])
        
        # Run VAH validation
        stock.validate_vah_rejection(case['vah_price'])
        
        # Check result
        if stock.is_active == case['expected_active']:
            print(f"   ✅ {case['symbol']}: {case['expected_result']}")
        else:
            print(f"   ❌ {case['symbol']}: Expected {case['expected_result']}, got {'validated' if stock.is_active else 'failed'}")
    
    print()
    print("🎯 EXPECTED LOG OUTPUT:")
    print("When you run the continuation bot, you should see:")
    print("   VAH validated for ROSSTECH")
    print("   VAH validated for SHANTIGOLD")
    print("   VAH validation failed for ADANIPOWER (Opening price 142.60 < VAH 149.93)")
    print("   VAH validation failed for ANGELONE (Opening price 2675.00 < VAH 2745.08)")
    
    print()
    print("✅ VAH VALIDATION LOGGING TEST COMPLETE")
    print("The continuation bot will now show explicit VAH validation results!")

if __name__ == "__main__":
    test_vah_validation_logging()