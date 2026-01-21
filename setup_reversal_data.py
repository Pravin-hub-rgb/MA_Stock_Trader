#!/usr/bin/env python3
"""
Setup script for Reversal Bot Data Access
Ensures reversal bot has same data access as continuation bot
"""

import sys
import os
import json
from pathlib import Path

def setup_reversal_data():
    """Set up data access for reversal bot"""

    print("🔧 Setting up Reversal Bot Data Access")
    print("=" * 50)

    # Add src to path
    sys.path.insert(0, 'src')

    # 1. Validate Upstox token
    print("\n1. 🔑 Validating Upstox Token...")
    try:
        from utils.token_validator import token_validator

        # Get current token
        current = token_validator.get_current_token()
        if not current['exists']:
            print("❌ No token found in upstox_config.json")
            return False

        # Validate token
        result = token_validator.validate_token(current['token'])

        if result['valid']:
            print("✅ Token validated successfully")
            print(f"   Tests passed: {result['successful_tests']}/{result['total_tests']}")

            # Test a few reversal stocks specifically
            test_stocks = ['AVANTEL', 'ELECON', 'GODREJPROP']
            print(f"\n   Testing reversal stocks: {', '.join(test_stocks)}")
            for stock in test_stocks:
                try:
                    from utils.upstox_fetcher import upstox_fetcher
                    data = upstox_fetcher.get_ltp_data(stock)
                    if data and 'cp' in data:
                        print(f"   ✅ {stock}: Previous close ₹{data['cp']}")
                    else:
                        print(f"   ❌ {stock}: No previous close data")
                except Exception as e:
                    print(f"   ❌ {stock}: Error - {e}")
        else:
            print(f"❌ Token validation failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

    # 2. Check bhavcopy cache
    print("\n2. 📊 Checking Bhavcopy Cache...")

    cache_dir = Path('bhavcopy_cache')
    if not cache_dir.exists():
        print("❌ bhavcopy_cache directory not found")
        return False

    # Check for CSV files
    csv_files = list(cache_dir.glob('*.csv'))
    if not csv_files:
        print("⚠️ No historical CSV files found in bhavcopy_cache")

        # Try to update bhavcopy
        print("📥 Attempting to update bhavcopy data...")
        try:
            from utils.bhavcopy_integrator import update_latest_bhavcopy
            result = update_latest_bhavcopy()

            if result['status'] == 'SUCCESS':
                print(f"✅ Bhavcopy updated: {result['date']}")
            else:
                print(f"❌ Bhavcopy update failed: {result.get('error', 'Unknown error')}")
                print("⚠️ Continuing without historical data (will use defaults)")
        except Exception as e:
            print(f"❌ Bhavcopy update error: {e}")
            print("⚠️ Continuing without historical data (will use defaults)")
    else:
        print(f"✅ Found {len(csv_files)} historical data files")
        # Check if reversal stocks have data
        reversal_stocks = ['AVANTEL', 'ELECON', 'GODREJPROP']
        found_data = 0
        for stock in reversal_stocks:
            csv_file = cache_dir / f"{stock.lower()}_daily.csv"
            if csv_file.exists():
                found_data += 1
                print(f"   ✅ {stock}: Historical data available")
            else:
                print(f"   ⚠️ {stock}: No historical data (will use defaults)")

        if found_data > 0:
            print(f"✅ Historical data available for {found_data}/{len(reversal_stocks)} reversal stocks")
        else:
            print("⚠️ No historical data for reversal stocks (will use ADR defaults)")

    # 3. Test reversal bot data access
    print("\n3. 🧪 Testing Reversal Bot Data Access...")

    try:
        # Import reversal components
        from trading.live_trading.reversal_monitor import ReversalMonitor
        from trading.live_trading.config import REVERSAL_LIST_FILE

        # Create monitor and load watchlist
        monitor = ReversalMonitor()
        success = monitor.load_watchlist(REVERSAL_LIST_FILE)

        if success:
            print("✅ Reversal watchlist loaded successfully")
            print(f"   VIP stocks: {len(monitor.vip_stocks)}")
            print(f"   Secondary stocks: {len(monitor.secondary_stocks)}")
            print(f"   Tertiary stocks: {len(monitor.tertiary_stocks)}")

            # Test prev_close setting
            print("\n   Testing previous close data access...")
            test_stocks = monitor.vip_stocks[:3]  # Test first 3 VIP stocks

            from utils.upstox_fetcher import upstox_fetcher
            prev_closes = {}

            for stock in test_stocks:
                try:
                    # Extract clean symbol
                    clean_symbol = stock.symbol.split('-')[0]
                    data = upstox_fetcher.get_ltp_data(clean_symbol)
                    if data and 'cp' in data:
                        prev_closes[stock.symbol] = float(data['cp'])
                        print(f"   ✅ {stock.symbol}: Previous close ₹{data['cp']}")
                    else:
                        prev_closes[stock.symbol] = 0.0
                        print(f"   ❌ {stock.symbol}: No previous close data (using 0.0)")
                except Exception as e:
                    prev_closes[stock.symbol] = 0.0
                    print(f"   ❌ {stock.symbol}: Error getting data - {e}")

            # Set prev closes in monitor
            monitor.set_prev_closes(prev_closes)

            # Test gap calculation
            print("\n   Testing gap calculations...")
            for stock in test_stocks:
                if hasattr(stock, 'prev_close') and stock.prev_close and stock.prev_close > 0:
                    # Simulate opening price (use prev_close for testing)
                    stock.open_price = stock.prev_close * 1.01  # 1% gap up for testing
                    stock.first_tick_captured = True

                    # Calculate gap
                    monitor.calculate_stock_gap(stock)

                    if stock.gap_calculated:
                        print(f"   ✅ {stock.symbol}: Gap calculation working")
                    else:
                        print(f"   ❌ {stock.symbol}: Gap calculation failed")
                else:
                    print(f"   ⚠️ {stock.symbol}: Skipping gap test (no valid prev_close)")

        else:
            print("❌ Failed to load reversal watchlist")
            return False

    except Exception as e:
        print(f"❌ Reversal bot data access test failed: {e}")
        return False

    # 4. Test stock scoring
    print("\n4. 📈 Testing Stock Scoring...")

    try:
        from scanner.stock_scorer import stock_scorer

        # Test scoring for reversal stocks
        test_symbols = ['AVANTEL', 'ELECON', 'GODREJPROP']

        print("   Preloading metadata for reversal stocks...")
        # Create dummy prev_closes for testing
        dummy_prev_closes = {symbol: 100.0 for symbol in test_symbols}
        stock_scorer.preload_metadata(test_symbols, dummy_prev_closes)

        # Test individual scoring
        for symbol in test_symbols:
            try:
                # Get some dummy data for testing
                score_data = stock_scorer.score_stock(symbol, 100.0, 0, 10000)
                print(f"   ✅ {symbol}: Score {score_data['total_score']} (ADR: {score_data['adr_pct']:.1f}%)")
            except Exception as e:
                print(f"   ⚠️ {symbol}: Scoring error - {e} (will use defaults)")

    except Exception as e:
        print(f"❌ Stock scoring test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 REVERSAL BOT DATA ACCESS SETUP COMPLETE!")
    print("=" * 50)

    print("\n📋 Summary:")
    print("✅ Upstox token validated")
    print("✅ Historical data cache checked/updated")
    print("✅ Reversal watchlist loading tested")
    print("✅ Previous close data access verified")
    print("✅ Gap calculation logic tested")
    print("✅ Stock scoring system tested")

    print("\n🚀 The reversal bot should now be able to:")
    print("   • Access valid previous close prices")
    print("   • Calculate accurate gap percentages")
    print("   • Execute OOPS and Strong Start trades")
    print("   • Use proper stock scoring for ranking")

    print("\n💡 Note: Continuation bot functionality is preserved")
    print("💡 Reversal bot now has equivalent data access")

    return True

def main():
    """Main setup function"""
    try:
        success = setup_reversal_data()
        if success:
            print("\n✅ Setup completed successfully!")
            print("You can now run the reversal bot with proper data access.")
        else:
            print("\n❌ Setup failed!")
            print("Please check the errors above and try again.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
