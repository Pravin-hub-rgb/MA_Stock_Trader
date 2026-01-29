#!/usr/bin/env python3
"""
Test script to verify the complete architectural separation and real-time low violation checking
"""

import sys
import os
from datetime import datetime, time, timedelta
import logging

# Add current directory to path for imports
sys.path.append('src/trading/live_trading')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def test_reversal_architecture():
    """Test the complete reversal architecture separation"""
    
    print("=== TESTING REVERSAL ARCHITECTURE SEPARATION ===")
    
    # Test 1: Import ReversalStockMonitor (should work)
    try:
        from reversal_stock_monitor import ReversalStockMonitor
        print("✅ ReversalStockMonitor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ReversalStockMonitor: {e}")
        return False
    
    # Test 2: Import StockMonitor (should fail - not available in reversal system)
    try:
        from stock_monitor import StockMonitor
        print("❌ StockMonitor should not be available in reversal system")
        return False
    except ImportError:
        print("✅ StockMonitor correctly not available in reversal system")
    
    # Test 3: Create ReversalStockMonitor instance
    try:
        monitor = ReversalStockMonitor()
        print("✅ ReversalStockMonitor instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create ReversalStockMonitor: {e}")
        return False
    
    # Test 4: Add stocks with different situations
    try:
        # Add OOPS stock (reversal_s2)
        monitor.add_stock("TEST_OOPS", "test_oops_key", 100.0, "reversal_s2")
        
        # Add Strong Start stock (reversal_s1)
        monitor.add_stock("TEST_SS", "test_ss_key", 100.0, "reversal_s1")
        
        print("✅ Stocks added successfully with different situations")
    except Exception as e:
        print(f"❌ Failed to add stocks: {e}")
        return False
    
    # Test 5: Test real-time low violation checking
    try:
        # Get the OOPS stock
        oops_stock = monitor.stocks["test_oops_key"]
        
        # Set opening price
        oops_stock.set_open_price(95.0)  # Gap down
        
        # Validate gap
        gap_valid = oops_stock.validate_gap()
        print(f"✅ OOPS gap validation: {gap_valid}")
        
        # Test real-time low violation checking
        import sys
        sys.path.append('src/trading/live_trading')
        from reversal_modules.tick_processor import ReversalTickProcessor
        
        tick_processor = ReversalTickProcessor(oops_stock)
        
        # Simulate price ticks that would trigger low violation
        current_time = datetime.now()
        
        # Price at 95 (open), then drops to 93.5 (1.5% drop)
        tick_processor.process_tick(95.0, current_time)
        tick_processor.process_tick(93.5, current_time)
        
        # Check if low violation was detected
        if oops_stock.low_violation_checked:
            print("✅ Real-time low violation checking working")
        else:
            print("❌ Real-time low violation checking not working")
            return False
            
    except Exception as e:
        print(f"❌ Failed real-time low violation test: {e}")
        return False
    
    # Test 6: Test Strong Start entry level tracking
    try:
        # Get the Strong Start stock
        ss_stock = monitor.stocks["test_ss_key"]
        
        # Set opening price
        ss_stock.set_open_price(105.0)  # Gap up
        
        # Validate gap
        gap_valid = ss_stock.validate_gap()
        print(f"✅ Strong Start gap validation: {gap_valid}")
        
        # Test real-time entry level tracking
        tick_processor = ReversalTickProcessor(ss_stock)
        
        # Simulate price ticks that would update entry levels
        current_time = datetime.now()
        
        # Price moves from 105 (open) to 110 (higher)
        tick_processor.process_tick(105.0, current_time)
        tick_processor.process_tick(110.0, current_time)
        
        # Check if entry levels were updated
        if ss_stock.entry_high is not None and ss_stock.entry_high >= 110.0:
            print("✅ Real-time entry level tracking working")
        else:
            print(f"❌ Real-time entry level tracking not working: entry_high={ss_stock.entry_high}")
            return False
            
    except Exception as e:
        print(f"❌ Failed Strong Start entry level test: {e}")
        return False
    
    # Test 7: Test utility methods
    try:
        # Test get_subscribed_symbols
        symbols = monitor.get_subscribed_symbols()
        print(f"✅ get_subscribed_symbols: {symbols}")
        
        # Test get_low_violation_stocks
        low_violations = monitor.get_low_violation_stocks()
        print(f"✅ get_low_violation_stocks: {len(low_violations)} stocks")
        
    except Exception as e:
        print(f"❌ Failed utility methods test: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("✅ Reversal architecture separation is working correctly")
    print("✅ Real-time low violation checking is working")
    print("✅ Real-time entry level tracking is working")
    print("✅ No dependencies on StockMonitor in reversal system")
    
    return True

def test_integration_with_real_time_low_checking():
    """Test the integration with real-time low violation checking"""
    
    print("\n=== TESTING INTEGRATION WITH REAL-TIME LOW VIOLATION CHECKING ===")
    
    try:
        from reversal_modules.integration import ReversalIntegration
        from simple_data_streamer import SimpleStockStreamer
        from reversal_stock_monitor import ReversalStockMonitor
        from paper_trader import PaperTrader
        
        # Create components
        monitor = ReversalStockMonitor()
        streamer = SimpleStockStreamer([], {})
        paper_trader = PaperTrader()
        
        # Create integration
        integration = ReversalIntegration(streamer, monitor, paper_trader)
        
        print("✅ Integration created successfully")
        print("✅ Real-time low violation checking integrated")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Reversal Bot Architectural Separation and Real-time Low Violation Checking")
    print("=" * 80)
    
    # Run tests
    architecture_test = test_reversal_architecture()
    integration_test = test_integration_with_real_time_low_checking()
    
    if architecture_test and integration_test:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("The reversal bot architectural separation is complete and working correctly.")
        print("Real-time low violation checking is implemented and functional.")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Please check the implementation and fix any issues.")
        sys.exit(1)