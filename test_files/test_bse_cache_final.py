#!/usr/bin/env python3
"""
Test BSE Previous Close using cache data
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_bse_previous_close_cache():
    """Test BSE previous close using cache data"""
    print("🧪 TESTING BSE PREVIOUS CLOSE - CACHE DATA")
    print("=" * 50)

    def get_previous_close_from_cache(symbol: str):
        """Get previous working day close from cache data"""
        try:
            import pandas as pd
            cache_file = f"data/cache/{symbol}.pkl"

            if not os.path.exists(cache_file):
                print(f"❌ Cache file not found: {cache_file}")
                return None

            # Load cache data
            df = pd.read_pickle(cache_file)

            if df.empty:
                print(f"❌ Empty cache data for {symbol}")
                return None

            print(f"✅ Loaded cache data: {len(df)} records")
            print(f"   Date range: {df.index.min()} to {df.index.max()}")

            # Sort by date (most recent first)
            df_sorted = df.sort_index(ascending=False)

            # Find the most recent date before today
            from datetime import date, datetime
            today = date.today()
            today_datetime = datetime.combine(today, datetime.min.time())
            prev_dates = df_sorted.index[df_sorted.index < today_datetime]

            if len(prev_dates) > 0:
                prev_date = prev_dates[0]  # Most recent previous date
                prev_close = float(df_sorted.loc[prev_date, 'close'])
                print(f"✅ Previous date found: {prev_date}")
                return prev_close

            print(f"❌ No previous dates found in cache for {symbol}")
            return None

        except Exception as e:
            print(f"❌ Error reading cache for {symbol}: {e}")
            return None

    print("Testing cache-based previous close fetch for BSE...")

    # Test the cache method
    prev_close = get_previous_close_from_cache('BSE')

    if prev_close is not None:
        print(f"📊 BSE Previous Close: ₹{prev_close:.2f}")

        # Check if it matches expected value
        expected_close = 2744.90
        if abs(prev_close - expected_close) < 0.01:
            print(f"✅ CORRECT: Previous close matches expected ₹{expected_close:.2f}")
            return True
        else:
            print(f"❌ MISMATCH: Expected ₹{expected_close:.2f}, got ₹{prev_close:.2f}")
            return False
    else:
        print("❌ ERROR: No previous close found in cache")
        return False

if __name__ == "__main__":
    success = test_bse_previous_close_cache()
    if success:
        print("\n🎉 BSE Cache Previous Close Test PASSED!")
    else:
        print("\n❌ BSE Cache Previous Close Test FAILED!")
    sys.exit(0 if success else 1)
