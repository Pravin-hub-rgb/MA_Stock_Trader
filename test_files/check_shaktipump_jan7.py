#!/usr/bin/env python3
"""
Check if SHAKTIPUMP has Jan 7 data after the bulk update
"""

from src.utils.cache_manager import cache_manager
from datetime import date

def check_shaktipump_jan7():
    """Check SHAKTIPUMP's cache data"""
    print("🔍 CHECKING SHAKTIPUMP JAN 7 DATA")
    print("=" * 50)

    symbol = 'SHAKTIPUMP'
    df = cache_manager.load_cached_data(symbol)

    if df is not None:
        print(f"✅ {symbol} cache found with {len(df)} days of data")
        print(f"Date range: {df.index.min()} to {df.index.max()}")

        # Check if Jan 7 is there (handle both date and datetime index)
        jan7 = date(2026, 1, 7)
        jan7_found = False

        # Try different ways to find Jan 7
        if jan7 in df.index:
            jan7_found = True
        else:
            # Check if any index matches Jan 7 date
            for idx in df.index:
                if hasattr(idx, 'date') and idx.date() == jan7:
                    jan7_found = True
                    break
                elif str(idx).startswith('2026-01-07'):
                    jan7_found = True
                    break

        if jan7_found:
            print("✅ Jan 7 data found!")

            # Get the row (handle different index types)
            try:
                row = df.loc[jan7]
            except KeyError:
                # Find the correct index
                for idx in df.index:
                    if hasattr(idx, 'date') and idx.date() == jan7:
                        row = df.loc[idx]
                        break
                    elif str(idx).startswith('2026-01-07'):
                        row = df.loc[idx]
                        break

            print(f"Jan 7 close: ₹{row['close']:.2f}")
            print(f"Jan 7 volume: {int(row['volume']):,}")
        else:
            print("❌ Jan 7 data missing")
            print("Bulk update may not have worked for SHAKTIPUMP")

        # Show last few days
        print(f"\nLast 5 days of {symbol} data:")
        for idx in df.index[-5:]:
            row = df.loc[idx]
            date_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
            print(f"  {date_str}: ₹{row['close']:.2f}")

    else:
        print(f"❌ {symbol} cache not found")
        print("Bulk update definitely failed")

    print("\n" + "="*50)

if __name__ == "__main__":
    check_shaktipump_jan7()