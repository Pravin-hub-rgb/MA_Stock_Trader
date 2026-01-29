#!/usr/bin/env python3
"""
Simple test for BSE previous close using historical data
"""

import sys
import os
from datetime import date, timedelta

# Add src to path
sys.path.append('src')

def test_bse_previous_close_simple():
    """Test BSE previous close using historical data"""
    print("🧪 TESTING BSE PREVIOUS CLOSE - SIMPLE HISTORICAL")
    print("=" * 55)

    from utils.upstox_fetcher import UpstoxFetcher

    fetcher = UpstoxFetcher()

    print("Fetching historical data for BSE...")

    # Get last 5 days of data
    end_date = date.today()
    start_date = end_date - timedelta(days=5)

    df = fetcher.fetch_historical_data('BSE', start_date, end_date)

    if df.empty:
        print("❌ ERROR: No historical data fetched")
        return False

    print(f"✅ Fetched {len(df)} days of data")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

    # Find the most recent date before today
    today = date.today()
    prev_dates = df.index[df.index < today]

    if len(prev_dates) == 0:
        print("❌ ERROR: No previous dates found")
        return False

    # Get the most recent previous date
    prev_date = prev_dates[-1]  # Most recent
    prev_close = float(df.loc[prev_date, 'close'])

    print(f"📊 Previous trading day: {prev_date}")
    print(f"📊 BSE Previous Close: ₹{prev_close:.2f}")

    # Check if it matches expected value
    expected_close = 2744.90
    if abs(prev_close - expected_close) < 0.01:
        print(f"✅ CORRECT: Previous close matches expected ₹{expected_close:.2f}")
        return True
    else:
        print(f"❌ MISMATCH: Expected ₹{expected_close:.2f}, got ₹{prev_close:.2f}")
        return False

if __name__ == "__main__":
    success = test_bse_previous_close_simple()
    if success:
        print("\n🎉 BSE Previous Close Test PASSED!")
    else:
        print("\n❌ BSE Previous Close Test FAILED!")
    sys.exit(0 if success else 1)