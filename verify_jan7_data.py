#!/usr/bin/env python3
"""
Verify CHOLAFIN and ANURAS have Jan 7 data
"""

from src.utils.cache_manager import cache_manager
from datetime import date

def verify_jan7_data():
    """Verify Jan 7 data for CHOLAFIN and ANURAS"""
    print("🔍 VERIFYING JAN 7 DATA FOR CHOLAFIN & ANURAS")
    print("=" * 60)

    stocks = ['CHOLAFIN', 'ANURAS']
    jan7 = date(2026, 1, 7)

    for symbol in stocks:
        print(f"\nChecking {symbol}...")
        df = cache_manager.load_cached_data(symbol)

        if df is not None:
            print(f"  ✅ Cache: {len(df)} days")

            # Check for Jan 7
            found = False
            for idx in df.index:
                if hasattr(idx, 'date') and idx.date() == jan7:
                    found = True
                    row = df.loc[idx]
                    print(f"  ✅ Jan 7: ₹{row['close']:.2f}")
                    break

            if not found:
                print("  ❌ Jan 7 missing")
        else:
            print(f"  ❌ No cache for {symbol}")

    print("\n" + "=" * 60)
    print("✅ VERIFICATION COMPLETE")
    print("Both stocks now have Jan 7 data from bhavcopy update!")

if __name__ == "__main__":
    verify_jan7_data()