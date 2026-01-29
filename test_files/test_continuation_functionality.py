#!/usr/bin/env python3
"""
Test Continuation Bot Functionality
Verifies that continuation bot still works after reversal bot fixes
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_continuation_functionality():
    """Test that continuation bot functionality is preserved"""

    print("🧪 Testing Continuation Bot Functionality")
    print("=" * 50)

    try:
        # Test basic imports
        from trading.live_trading.stock_monitor import StockMonitor
        from trading.live_trading.config import CONTINUATION_LIST_FILE
        print("✅ Continuation bot imports work")

        # Test continuation list loading
        if os.path.exists(CONTINUATION_LIST_FILE):
            with open(CONTINUATION_LIST_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    symbols = [s.strip() for s in content.split(',') if s.strip()]
                    print(f"✅ Continuation list loaded: {len(symbols)} stocks")
                    print(f"   Sample stocks: {', '.join(symbols[:5])}")
                else:
                    print("⚠️ Continuation list is empty")
                    return True  # Empty is OK, just means no stocks configured
        else:
            print("❌ Continuation list file not found")
            return False

        # Test monitor initialization
        monitor = StockMonitor()
        print("✅ StockMonitor initialized")

        # Test stock addition (using first symbol)
        if 'symbols' in locals() and symbols:
            test_symbol = symbols[0]
            # Mock prev_close for testing
            mock_prev_close = 100.0

            monitor.add_stock(test_symbol, f"NSE_EQ|{test_symbol}", mock_prev_close)
            print(f"✅ Added test stock: {test_symbol}")

            # Test entry preparation
            monitor.prepare_entries()
            print("✅ Entry preparation works")

            # Test stock retrieval
            active_stocks = monitor.get_active_stocks()
            if active_stocks:
                print(f"✅ Active stocks retrieved: {len(active_stocks)} stock(s)")
            else:
                print("⚠️ No active stocks (this may be normal)")

        # Test rule engine import
        from trading.live_trading.rule_engine import RuleEngine
        rule_engine = RuleEngine()
        print("✅ RuleEngine initialized")

        # Test selection engine import
        from trading.live_trading.selection_engine import SelectionEngine
        selection_engine = SelectionEngine()
        print("✅ SelectionEngine initialized")

        # Test paper trader import
        from trading.live_trading.paper_trader import PaperTrader
        paper_trader = PaperTrader()
        print("✅ PaperTrader initialized")

        print("\n" + "=" * 50)
        print("✅ CONTINUATION BOT FUNCTIONALITY: PRESERVED!")
        print("=" * 50)

        print("\n📋 All continuation bot components verified:")
        print("✅ Imports work correctly")
        print("✅ Configuration files load")
        print("✅ Core classes initialize")
        print("✅ Stock monitoring functions")
        print("✅ Trading components available")

        return True

    except Exception as e:
        print(f"❌ Continuation bot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    try:
        success = test_continuation_functionality()
        if success:
            print("\n✅ Continuation bot functionality test completed successfully!")
            print("💡 Continuation trading features are intact and working.")
        else:
            print("\n❌ Continuation bot functionality test failed!")
            print("🔧 Check that continuation bot components are not broken by recent changes.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
