#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for unsubscription logging with both gap and VAH validation scenarios
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_comprehensive_unsubscription():
    """Test comprehensive unsubscription logging scenarios"""
    
    print("🧪 COMPREHENSIVE UNSUBSCRIPTION LOGGING TEST")
    print("=" * 60)
    print("Testing both Gap validation failures and VAH validation failures")
    print()
    
    # Import the modules
    try:
        from src.trading.live_trading.continuation_modules.subscription_manager import ContinuationSubscriptionManager
        from src.trading.live_trading.continuation_stock_monitor import StockState
        print("✅ Successfully imported modules")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return
    
    # Create mock data streamer
    class MockDataStreamer:
        def __init__(self):
            self.subscribed_keys = set()
        
        def unsubscribe(self, keys):
            print(f"   📡 UNSUBSCRIBED {len(keys)} keys: {keys}")
            self.subscribed_keys.difference_update(keys)
    
    # Create test stocks with different scenarios
    test_stocks = {
        # Gap-failed stocks (gap validation failed)
        'ADANIPOWER': StockState('ADANIPOWER', 'ADANIPOWER', 100.0, 'continuation'),
        'ANGELONE': StockState('ANGELONE', 'ANGELONE', 100.0, 'continuation'),
        
        # VAH-failed stocks (gap validated but VAH failed)
        'ELECON': StockState('ELECON', 'ELECON', 100.0, 'continuation'),
        'GRSE': StockState('GRSE', 'GRSE', 100.0, 'continuation'),
        
        # Both gap and VAH validated (should remain subscribed)
        'ROSSTECH': StockState('ROSSTECH', 'ROSSTECH', 100.0, 'continuation'),
        'SHANTIGOLD': StockState('SHANTIGOLD', 'SHANTIGOLD', 100.0, 'continuation'),
    }
    
    # Set up test scenarios
    
    # Gap-failed stocks (gap validation failed)
    test_stocks['ADANIPOWER'].gap_validated = False
    test_stocks['ADANIPOWER'].is_active = False
    test_stocks['ADANIPOWER'].open_price = 142.60
    test_stocks['ADANIPOWER'].vah_price = 149.93
    
    test_stocks['ANGELONE'].gap_validated = False
    test_stocks['ANGELONE'].is_active = False
    test_stocks['ANGELONE'].open_price = 2675.00
    test_stocks['ANGELONE'].vah_price = 2745.08
    
    # VAH-failed stocks (gap validated but VAH failed)
    test_stocks['ELECON'].gap_validated = True
    test_stocks['ELECON'].is_active = False  # Will be set to False by VAH validation
    test_stocks['ELECON'].open_price = 434.15
    test_stocks['ELECON'].vah_price = 452.63
    
    test_stocks['GRSE'].gap_validated = True
    test_stocks['GRSE'].is_active = False  # Will be set to False by VAH validation
    test_stocks['GRSE'].open_price = 2445.40
    test_stocks['GRSE'].vah_price = 2499.93
    
    # Both gap and VAH validated (should remain subscribed)
    test_stocks['ROSSTECH'].gap_validated = True
    test_stocks['ROSSTECH'].is_active = True
    test_stocks['ROSSTECH'].open_price = 727.00
    test_stocks['ROSSTECH'].vah_price = 707.77
    
    test_stocks['SHANTIGOLD'].gap_validated = True
    test_stocks['SHANTIGOLD'].is_active = True
    test_stocks['SHANTIGOLD'].open_price = 220.37
    test_stocks['SHANTIGOLD'].vah_price = 219.44
    
    # Create mock monitor
    class MockMonitor:
        def __init__(self, stocks):
            self.stocks = stocks
    
    mock_monitor = MockMonitor(test_stocks)
    mock_data_streamer = MockDataStreamer()
    
    # Create subscription manager
    subscription_manager = ContinuationSubscriptionManager(mock_data_streamer, mock_monitor)
    
    # Initialize all stocks as subscribed
    for stock in test_stocks.values():
        subscription_manager.subscribed_keys.add(stock.instrument_key)
    
    print(f"📊 INITIAL STATUS:")
    print(f"   Total stocks: {len(test_stocks)}")
    print(f"   Subscribed: {len(subscription_manager.subscribed_keys)}")
    print(f"   Gap-validated: {sum(1 for s in test_stocks.values() if s.gap_validated)}")
    print(f"   Gap-failed: {sum(1 for s in test_stocks.values() if not s.gap_validated)}")
    print(f"   VAH-validated: {sum(1 for s in test_stocks.values() if s.open_price >= s.vah_price)}")
    print(f"   VAH-failed: {sum(1 for s in test_stocks.values() if s.open_price < s.vah_price)}")
    print()
    
    # Run Phase 1 unsubscription
    print("🚀 RUNNING PHASE 1: UNSUBSCRIBE GAP+VAH REJECTED STOCKS")
    subscription_manager.unsubscribe_gap_and_vah_rejected()
    print()
    
    # Check results
    print("📊 POST-PHASE 1 STATUS:")
    print(f"   Subscribed: {len(subscription_manager.subscribed_keys)}")
    print(f"   Unsubscribed: {len(test_stocks) - len(subscription_manager.subscribed_keys)}")
    
    subscribed_symbols = [s.symbol for s in test_stocks.values() if s.instrument_key in subscription_manager.subscribed_keys]
    unsubscribed_symbols = [s.symbol for s in test_stocks.values() if s.instrument_key not in subscription_manager.subscribed_keys]
    
    print(f"   Still subscribed: {subscribed_symbols}")
    print(f"   Unsubscribed: {unsubscribed_symbols}")
    print()
    
    # Verify expected results
    expected_subscribed = ['ROSSTECH', 'SHANTIGOLD']  # Only stocks that passed both gap and VAH
    expected_unsubscribed = [s for s in test_stocks.keys() if s not in expected_subscribed]
    
    print("✅ VERIFICATION:")
    if set(subscribed_symbols) == set(expected_subscribed):
        print(f"   ✅ Correctly subscribed: {subscribed_symbols}")
    else:
        print(f"   ❌ Expected subscribed: {expected_subscribed}")
        print(f"   ❌ Actually subscribed: {subscribed_symbols}")
    
    if set(unsubscribed_symbols) == set(expected_unsubscribed):
        print(f"   ✅ Correctly unsubscribed: {unsubscribed_symbols}")
    else:
        print(f"   ❌ Expected unsubscribed: {expected_unsubscribed}")
        print(f"   ❌ Actually unsubscribed: {unsubscribed_symbols}")
    
    print()
    print("🎯 EXPECTED LOG OUTPUT:")
    print("When you run the continuation bot, you should see:")
    print("   === PHASE 1: UNSUBSCRIBING GAP+VAH REJECTED STOCKS ===")
    print("   Unsubscribing 4 stocks: ['ADANIPOWER', 'ANGELONE', 'ELECON', 'GRSE']")
    print("   UNSUBSCRIBING ADANIPOWER - Reason: Gap validation failed")
    print("   UNSUBSCRIBING ANGELONE - Reason: Gap validation failed")
    print("   UNSUBSCRIBING ELECON - Reason: VAH validation failed (Opening price 434.15 < VAH 452.63)")
    print("   UNSUBSCRIBING GRSE - Reason: VAH validation failed (Opening price 2445.40 < VAH 2499.93)")
    print("   GAP VALIDATION FAILED (2 stocks):")
    print("      - ADANIPOWER")
    print("      - ANGELONE")
    print("   VAH VALIDATION FAILED (2 stocks):")
    print("      - ELECON (Open: 434.15, VAH: 452.63)")
    print("      - GRSE (Open: 2445.40, VAH: 2499.93)")
    print("   STOCKS REMAINING SUBSCRIBED (2 stocks):")
    print("      - ROSSTECH")
    print("      - SHANTIGOLD")
    
    if set(subscribed_symbols) == set(expected_subscribed) and set(unsubscribed_symbols) == set(expected_unsubscribed):
        print("\n🎉 COMPREHENSIVE UNSUBSCRIPTION LOGGING TEST PASSED!")
        return True
    else:
        print("\n❌ COMPREHENSIVE UNSUBSCRIPTION LOGGING TEST FAILED!")
        return False

if __name__ == "__main__":
    success = test_comprehensive_unsubscription()
    if success:
        print("\n✅ Ready to test with live bot!")
    else:
        print("\n❌ Fix needed before live testing!")