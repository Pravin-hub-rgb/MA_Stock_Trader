#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Phase 1 unsubscription is working correctly
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

def test_phase_1_unsubscription():
    """Test that Phase 1 unsubscription works correctly"""
    
    print("🧪 TESTING PHASE 1 UNSUBSCRIPTION")
    print("=" * 50)
    print("This tests the exact same logic used in the live continuation bot")
    print()
    
    # Import the integration module
    try:
        from src.trading.live_trading.continuation_modules.integration import ContinuationIntegration
        from src.trading.live_trading.continuation_stock_monitor import StockMonitor
        print("✅ Successfully imported continuation modules")
    except ImportError as e:
        print(f"❌ Failed to import modules: {e}")
        return
    
    # Create mock data streamer and monitor
    class MockDataStreamer:
        def __init__(self):
            self.subscribed_keys = set()
        
        def unsubscribe(self, keys):
            print(f"   📡 UNSUBSCRIBED {len(keys)} keys: {keys}")
            self.subscribed_keys.difference_update(keys)
    
    class MockStock:
        def __init__(self, symbol, gap_validated, is_active):
            self.symbol = symbol
            self.instrument_key = symbol
            self.gap_validated = gap_validated
            self.is_active = is_active
            self.situation = 'continuation'
            self.rejection_reason = ""
    
    # Create test stocks
    test_stocks = {
        'ADANIPOWER': MockStock('ADANIPOWER', False, False),  # Gap failed
        'ANGELONE': MockStock('ANGELONE', False, False),      # Gap failed  
        'ELECON': MockStock('ELECON', False, False),          # Gap failed
        'GRSE': MockStock('GRSE', False, False),              # Gap failed
        'HINDCOPPER': MockStock('HINDCOPPER', False, False),  # Gap failed
        'MIDHANI': MockStock('MIDHANI', False, False),        # Gap failed
        'MOSCHIP': MockStock('MOSCHIP', False, False),        # Gap failed
        'NAVNETEDUL': MockStock('NAVNETEDUL', False, False),  # Gap failed
        'PATELRMART': MockStock('PATELRMART', False, False),  # Gap failed
        'PICCADIL': MockStock('PICCADIL', False, False),      # Gap failed
        'ROSSTECH': MockStock('ROSSTECH', True, True),        # Gap validated
        'SHANTIGOLD': MockStock('SHANTIGOLD', True, True),    # Gap validated
        'SHRINGARMS': MockStock('SHRINGARMS', False, False),  # Gap failed
        'UNIONBANK': MockStock('UNIONBANK', False, False),    # Gap failed
        'WALCHANNAG': MockStock('WALCHANNAG', False, False),  # Gap failed
    }
    
    # Create mock monitor
    mock_monitor = MockDataStreamer()
    mock_monitor.stocks = test_stocks
    
    # Create integration
    mock_data_streamer = MockDataStreamer()
    integration = ContinuationIntegration(mock_data_streamer, mock_monitor)
    
    # Initialize subscription manager with all stocks
    for stock in test_stocks.values():
        integration.subscription_manager.subscribed_keys.add(stock.instrument_key)
    
    print(f"📊 INITIAL STATUS:")
    print(f"   Total stocks: {len(test_stocks)}")
    print(f"   Subscribed: {len(integration.subscription_manager.subscribed_keys)}")
    print(f"   Gap-validated: {sum(1 for s in test_stocks.values() if s.gap_validated)}")
    print(f"   Gap-failed: {sum(1 for s in test_stocks.values() if not s.gap_validated)}")
    print()
    
    # Run Phase 1 unsubscription
    print("🚀 RUNNING PHASE 1: UNSUBSCRIBE GAP+VAH REJECTED STOCKS")
    integration.phase_1_unsubscribe_after_gap_and_vah()
    print()
    
    # Check results
    print("📊 POST-PHASE 1 STATUS:")
    print(f"   Subscribed: {len(integration.subscription_manager.subscribed_keys)}")
    print(f"   Unsubscribed: {len(test_stocks) - len(integration.subscription_manager.subscribed_keys)}")
    
    subscribed_symbols = [s.symbol for s in test_stocks.values() if s.instrument_key in integration.subscription_manager.subscribed_keys]
    unsubscribed_symbols = [s.symbol for s in test_stocks.values() if s.instrument_key not in integration.subscription_manager.subscribed_keys]
    
    print(f"   Still subscribed: {subscribed_symbols}")
    print(f"   Unsubscribed: {unsubscribed_symbols}")
    print()
    
    # Verify expected results
    expected_subscribed = ['ROSSTECH', 'SHANTIGOLD']  # Only gap-validated stocks
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
    print("🎯 EXPECTED BEHAVIOR IN LIVE BOT:")
    print("1. Gap-failed stocks should be unsubscribed immediately")
    print("2. Gap-validated stocks should remain subscribed")
    print("3. Unsubscribed stocks should NOT appear in logs")
    print("4. Tick handler should filter out unsubscribed stocks")
    
    if set(subscribed_symbols) == set(expected_subscribed) and set(unsubscribed_symbols) == set(expected_unsubscribed):
        print("\n🎉 PHASE 1 UNSUBSCRIPTION TEST PASSED!")
        return True
    else:
        print("\n❌ PHASE 1 UNSUBSCRIPTION TEST FAILED!")
        return False

if __name__ == "__main__":
    success = test_phase_1_unsubscription()
    if success:
        print("\n✅ Ready to test with live bot!")
    else:
        print("\n❌ Fix needed before live testing!")