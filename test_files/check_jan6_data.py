#!/usr/bin/env python3
"""
Check OHLC Values for 5 Stocks from Jan 6, 2026 Cache
"""

from src.utils.cache_manager import cache_manager
import pandas as pd

def main():
    print("📊 OHLC VALUES FOR JAN 6, 2026 FROM CACHE")
    print("=" * 50)

    # Check 5 stocks that were updated with Jan 6 data
    stocks_to_check = ['BLSE', 'GOLD360', 'SILVER360', 'BSLGOLDETF', '20MICRONS']

    for stock in stocks_to_check:
        try:
            df = cache_manager.load_cached_data(stock)
            if df is not None and not df.empty:
                # Find Jan 6 data - handle different index types
                target_date = pd.Timestamp('2026-01-06')
                if hasattr(df.index, 'date'):
                    # DatetimeIndex
                    jan6_data = df[df.index.date == target_date.date()]
                else:
                    # Regular index with date column
                    jan6_data = df[df.index == target_date]

                if not jan6_data.empty:
                    row = jan6_data.iloc[0]
                    print(f'{stock:<12}: O:{row["open"]:>8.2f} H:{row["high"]:>8.2f} L:{row["low"]:>8.2f} C:{row["close"]:>8.2f} V:{row["volume"]:>10.0f}')
                else:
                    print(f'{stock:<12}: No Jan 6 data found')
            else:
                print(f'{stock:<12}: No cache data')
        except Exception as e:
            print(f'{stock:<12}: Error - {e}')

if __name__ == "__main__":
    main()