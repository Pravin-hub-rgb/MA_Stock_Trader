#!/usr/bin/env python3
"""
Test script to verify the monitoring fix for reversal bot.

This script demonstrates that the logging now only shows actively monitored stocks,
not gap-rejected stocks that have been unsubscribed.
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'trading', 'live_trading'))

from reversal_stock_monitor import ReversalStockMonitor

def test_monitoring_fix():
    """Test that only actively monitored stocks are shown in qualification status"""
    
    print("🧪 TESTING MONITORING FIX")
    print("=" * 50)
    
    # Create monitor
    monitor = ReversalStockMonitor()
    
    # Add test stocks with different scenarios
    monitor.add_stock('SIGNATURE', 'NSE_EQ|16609', 823.0, 'reversal_s2')      # OOPS - qualified
    monitor.add_stock('POONAWALLA', 'NSE_EQ|16610', 406.3, 'reversal_s1')     # Strong Start - qualified  
    monitor.add_stock('ANANTRAJ', 'NSE_EQ|16611', 489.65, 'reversal_s2')      # OOPS - rejected (flat gap)
    monitor.add_stock('GODREJPROP', 'NSE_EQ|16612', 1520.0, 'reversal_s2')    # OOPS - rejected (flat gap)
    
    # Set open prices
    monitor.stocks['NSE_EQ|16609'].set_open_price(820.0)   # SIGNATURE - qualified (gap down)
    monitor.stocks['NSE_EQ|16610'].set_open_price(406.3)   # POONAWALLA - qualified (gap up)
    monitor.stocks['NSE_EQ|16611'].set_open_price(489.65)  # ANANTRAJ - rejected (flat gap)
    monitor.stocks['NSE_EQ|16612'].set_open_price(1521.5)  # GODREJPROP - rejected (flat gap)
    
    print("Stocks added:")
    print("  - SIGNATURE: OOPS candidate (qualified)")
    print("  - POONAWALLA: Strong Start candidate (qualified)")
    print("  - ANANTRAJ: OOPS candidate (rejected - flat gap)")
    print("  - GODREJPROP: OOPS candidate (rejected - flat gap)")
    print()
    
    # Validate gaps
    print("Validating gaps...")
    monitor.stocks['NSE_EQ|16609'].validate_gap()   # Should pass
    monitor.stocks['NSE_EQ|16610'].validate_gap()   # Should pass
    monitor.stocks['NSE_EQ|16611'].validate_gap()   # Should fail
    monitor.stocks['NSE_EQ|16612'].validate_gap()   # Should fail
    print()
    
    # Check violations
    monitor.check_violations()
    
    # Get qualified stocks - should only show active ones
    print("Getting qualified stocks (should only show actively monitored stocks):")
    qualified = monitor.get_qualified_stocks()
    
    print(f"\n✅ RESULTS:")
    print(f"   Total stocks added: 4")
    print(f"   Actively monitored: {len(monitor.get_active_stocks())}")
    print(f"   Qualified stocks: {len(qualified)}")
    
    print(f"\n📊 EXPECTED BEHAVIOR:")
    print(f"   - Only SIGNATURE and POONAWALLA should be shown in status")
    print(f"   - ANANTRAJ and GODREJPROP should NOT appear (they were rejected)")
    print(f"   - This prevents confusion about which stocks are actually being monitored")
    
    # Verify the fix
    active_symbols = [stock.symbol for stock in monitor.get_active_stocks()]
    qualified_symbols = [stock.symbol for stock in qualified]
    
    print(f"\n🔍 VERIFICATION:")
    print(f"   Active stocks: {active_symbols}")
    print(f"   Qualified stocks: {qualified_symbols}")
    
    # Check that rejected stocks are not in active list
    rejected_in_active = [symbol for symbol in ['ANANTRAJ', 'GODREJPROP'] if symbol in active_symbols]
    
    if not rejected_in_active:
        print(f"   ✅ SUCCESS: Rejected stocks not in active monitoring list")
        print(f"   ✅ SUCCESS: Only qualified stocks are being monitored")
        return True
    else:
        print(f"   ❌ FAILURE: Rejected stocks still in active list: {rejected_in_active}")
        return False

if __name__ == "__main__":
    success = test_monitoring_fix()
    if success:
        print(f"\n🎉 MONITORING FIX VERIFIED!")
        print(f"   The reversal bot now correctly shows only actively monitored stocks")
        print(f"   in the qualification status, eliminating confusion about which")
        print(f"   stocks are actually being tracked.")
    else:
        print(f"\n❌ MONITORING FIX FAILED!")
        sys.exit(1)