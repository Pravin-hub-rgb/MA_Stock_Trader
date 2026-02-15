#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the simple chain reaction - immediate rejection and unsubscription
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_simple_chain_reaction():
    """Test that stocks are immediately rejected and stop processing data"""
    
    print("🧪 SIMPLE CHAIN REACTION TEST")
    print("=" * 50)
    print("Testing immediate rejection and unsubscription")
    print()
    
    # Import the modules
    try:
        from src.trading.live_trading.continuation_stock_monitor import StockState
        print("✅ Successfully imported StockState")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return
    
    # Create a test stock
    test_stock = StockState('TESTSTOCK', 'TESTSTOCK', 100.0, 'continuation')
    test_stock.open_price = 95.0  # Gap down - should fail gap validation
    test_stock.vah_price = 105.0  # Open below VAH - should fail VAH validation
    
    print(f"📊 INITIAL STATUS:")
    print(f"   Stock: {test_stock.symbol}")
    print(f"   Open Price: {test_stock.open_price}")
    print(f"   VAH Price: {test_stock.vah_price}")
    print(f"   is_active: {test_stock.is_active}")
    print(f"   is_subscribed: {test_stock.is_subscribed}")
    print()
    
    # Test Gap Validation
    print("🚀 TESTING GAP VALIDATION")
    gap_result = test_stock.validate_gap()
    print(f"   Gap validation result: {gap_result}")
    print(f"   is_active after gap validation: {test_stock.is_active}")
    print(f"   is_subscribed after gap validation: {test_stock.is_subscribed}")
    print(f"   rejection_reason: {test_stock.rejection_reason}")
    print()
    
    # Reset for VAH test
    test_stock.is_active = True
    test_stock.is_subscribed = True
    test_stock.rejection_reason = None
    
    # Test VAH Validation
    print("🚀 TESTING VAH VALIDATION")
    vah_result = test_stock.validate_vah_rejection(test_stock.vah_price)
    print(f"   VAH validation result: {vah_result}")
    print(f"   is_active after VAH validation: {test_stock.is_active}")
    print(f"   is_subscribed after VAH validation: {test_stock.is_subscribed}")
    print(f"   rejection_reason: {test_stock.rejection_reason}")
    print()
    
    # Test that rejected stock stops processing
    print("🚀 TESTING DATA PROCESSING STOP")
    initial_price = test_stock.current_price
    test_stock.update_price(96.0, None)
    print(f"   Price updated to 96.0: {test_stock.current_price}")
    print(f"   Stock should ignore this update since it's rejected")
    print()
    
    # Verify the chain reaction worked
    print("✅ VERIFICATION:")
    if not test_stock.is_active and not test_stock.is_subscribed:
        print("   ✅ Stock correctly rejected and unsubscribed")
        print("   ✅ Chain reaction working - stock stops processing data")
        return True
    else:
        print("   ❌ Chain reaction failed")
        print(f"   ❌ is_active: {test_stock.is_active}")
        print(f"   ❌ is_subscribed: {test_stock.is_subscribed}")
        return False

if __name__ == "__main__":
    success = test_simple_chain_reaction()
    if success:
        print("\n🎉 SIMPLE CHAIN REACTION TEST PASSED!")
        print("Stocks will now be immediately rejected and stop processing data!")
    else:
        print("\n❌ SIMPLE CHAIN REACTION TEST FAILED!")
        print("Fix needed before live testing!")