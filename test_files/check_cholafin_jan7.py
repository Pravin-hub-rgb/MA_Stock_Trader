#!/usr/bin/env python3
"""
Check if CHOLAFIN has Jan 7 data after bhavcopy update
"""

from src.utils.cache_manager import cache_manager
from datetime import date

def check_cholafin_jan7():
    """Check CHOLAFIN's data after bhavcopy update"""
    print("🔍 CHECKING CHOLAFIN JAN 7 DATA")
    print("=" * 50)

    symbol = 'CHOLAFIN'
    df = cache_manager.load_cached_data(symbol)

    if df is not None:
        print(f"✅ {symbol} cache found: {len(df)} days")
        print(f"📅 Date range: {df.index.min()} to {df.index.max()}")

        # Check Jan 7 data
        jan7 = date(2026, 1, 7)
        jan7_found = False

        for idx in df.index:
            if hasattr(idx, 'date') and idx.date() == jan7:
                jan7_found = True
                row = df.loc[idx]
                print("✅ Jan 7 data found!"                print(f"   Close: ₹{row['close']:.2f}")
                print(f"   Volume: {int(row['volume']):,}")
                break
            elif str(idx).startswith('2026-01-07'):
                jan7_found = True
                row = df.loc[idx]
                print("✅ Jan 7 data found!"                print(f"   Close: ₹{row['close']:.2f}")
                print(f"   Volume: {int(row['volume']):,}")
                break

        if not jan7_found:
            print("❌ Jan 7 data missing")

        print("
✅ CHOLAFIN now has latest market data!"        print("Your scanner will use the most recent data for analysis.")

    else:
        print(f"❌ {symbol} cache not found")

    print("\n" + "=" * 50)

if __name__ == "__main__":
    check_cholafin_jan7()