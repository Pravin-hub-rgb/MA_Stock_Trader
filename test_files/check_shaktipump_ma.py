#!/usr/bin/env python3
"""
Check SHAKTIPUMP MA calculations
"""

import pandas as pd
from src.utils.cache_manager import cache_manager
from src.utils.data_fetcher import data_fetcher
from datetime import date, timedelta

def check_shaktipump_ma():
    """Check SHAKTIPUMP MA values for specific dates"""
    print("Checking SHAKTIPUMP MA calculations")
    print("=" * 50)

    # Get SHAKTIPUMP data
    symbol = 'SHAKTIPUMP'
    scan_date = date(2026, 1, 6)
    data = data_fetcher.get_data_for_date_range(symbol, scan_date - timedelta(days=90), scan_date)
    data = data_fetcher.calculate_technical_indicators(data)

    print(f"Data shape: {data.shape}")
    print(f"Date range: {data.index.min()} to {data.index.max()}")
    print()

    # Check MA calculation manually
    data['SMA20_manual'] = data['close'].rolling(window=20).mean()

    # Key dates mentioned by user
    key_dates = ['2025-10-24', '2025-10-31', '2025-11-06', '2025-12-12']

    print("MA Values for key dates:")
    print("-" * 50)

    for date_str in key_dates:
        try:
            # Find the date in index
            matching_dates = [d for d in data.index if str(d.date()) == date_str]
            if matching_dates:
                d = matching_dates[0]
                row = data.loc[d]
                close = row['close']
                ma20 = row.get('ma_20', float('nan'))
                ma20_manual = row['SMA20_manual']

                print(f"{date_str}:")
                print(f"  Close: {close:.2f}")
                print(f"  MA20 (data_fetcher): {ma20:.2f}")
                print(f"  MA20 (manual): {ma20_manual:.2f}")
                print(f"  Close > MA: {close > ma20 if not pd.isna(ma20) else 'MA is NaN'}")
                print()
        except Exception as e:
            print(f"Error checking {date_str}: {e}")
            print()

    # Show first 25 days to see when MA starts
    print("First 25 days of data (when MA should start):")
    print("-" * 50)
    for i, (idx, row) in enumerate(data.head(25).iterrows()):
        close = row['close']
        ma20 = row.get('ma_20', float('nan'))
        ma20_manual = row['SMA20_manual']
        date_str = str(idx.date()) if hasattr(idx, 'date') else str(idx)

        print(f"{i+1:2d}: {date_str} Close={close:.2f}, MA={ma20:.2f}, Manual_MA={ma20_manual:.2f}")

if __name__ == "__main__":
    check_shaktipump_ma()