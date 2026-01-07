#!/usr/bin/env python3
"""
Check if the first 5 stocks (used by scanner for date detection) have Jan 7 data
"""

from src.utils.cache_manager import cache_manager
from datetime import date

def check_sample_stocks_jan7():
    """Check the first 5 stocks that scanner uses for date detection"""
    print("🔍 CHECKING SCANNER'S SAMPLE STOCKS FOR JAN 7 DATA")
    print("=" * 60)

    # These are the first 5 stocks the scanner checks
    sample_stocks = ['20MICRONS', '21STCENMGM', '360ONE', '3IINFOLTD', '3MINDIA']
    jan7 = date(2026, 1, 7)

    stocks_with_jan7 = 0

    for symbol in sample_stocks:
        print(f"\nChecking {symbol}...")
        df = cache_manager.load_cached_data(symbol)

        if df is not None:
            print(f"  ✅ Cache found: {len(df)} days")
            print(f"  📅 Date range: {df.index.min()} to {df.index.max()}")

            # Check for Jan 7
            jan7_found = False
            for idx in df.index:
                if hasattr(idx, 'date') and idx.date() == jan7:
                    jan7_found = True
                    row = df.loc[idx]
                    print(f"  ✅ Jan 7 found: Close ₹{row['close']:.2f}")
                    stocks_with_jan7 += 1
                    break
                elif str(idx).startswith('2026-01-07'):
                    jan7_found = True
                    row = df.loc[idx]
                    print(f"  ✅ Jan 7 found: Close ₹{row['close']:.2f}")
                    stocks_with_jan7 += 1
                    break

            if not jan7_found:
                print("  ❌ Jan 7 data missing")
        else:
            print(f"  ❌ Cache not found for {symbol}")

    print(f"\n" + "="*60)
    print(f"RESULTS: {stocks_with_jan7}/{len(sample_stocks)} sample stocks have Jan 7 data")

    if stocks_with_jan7 >= 3:
        print("✅ Scanner should detect Jan 7 (has 3+ stocks)")
    else:
        print("❌ Scanner will fail - needs 3+ stocks with Jan 7 data")

    print("\nThe scanner requires at least 3 of these sample stocks to have data")
    print("before it considers Jan 7 as an available scan date.")

if __name__ == "__main__":
    check_sample_stocks_jan7()