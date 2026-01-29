#!/usr/bin/env python3
"""
Force download extended data for ALL stocks - bypass cache checks
"""

import os
from pathlib import Path
from src.utils.data_fetcher import data_fetcher
from src.utils.upstox_fetcher import upstox_fetcher
from datetime import datetime, timedelta

def force_download_all_stocks():
    """Force download 180 days for all NSE stocks, bypassing cache"""

    print("🚀 FORCE DOWNLOAD ALL STOCKS")
    print("=" * 40)
    print("Bypassing all cache checks")
    print("Downloading 180 days for ALL NSE stocks")
    print()

    # Get NSE stocks list
    print("📡 Getting NSE stocks list...")
    nse_stocks = data_fetcher.fetch_nse_stocks()

    if not nse_stocks:
        print("❌ Failed to get NSE stocks list")
        return False

    print(f" Found {len(nse_stocks)} NSE stocks")

    # Create cache directory if it doesn't exist
    cache_dir = Path('data/cache')
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Download parameters
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    print(f"📅 Date range: {start_date} to {end_date}")

    # Process stocks
    total_processed = 0
    total_success = 0
    total_failed = 0

    max_stocks = len(nse_stocks)  # All NSE stocks
    stocks_to_process = nse_stocks  # Process all stocks

    print(f"🎯 Processing first {max_stocks} stocks...")
    print()

    for i, stock in enumerate(stocks_to_process, 1):
        symbol = stock['symbol']

        try:
            print(f"📥 [{i}/{max_stocks}] Downloading {symbol}...")

            # Force download - bypass all cache checks
            data = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)

            if data.empty:
                print(f"   ❌ No data for {symbol}")
                total_failed += 1
                continue

            # Count trading days
            trading_days = sum(1 for idx in data.index if idx.weekday() < 5)

            # Save to cache
            from src.utils.cache_manager import cache_manager
            cache_manager.update_cache(symbol, data)

            print(f"    Cached {len(data)} days ({trading_days} trading) for {symbol}")
            total_success += 1

        except Exception as e:
            print(f"   ❌ Error with {symbol}: {str(e)[:50]}...")
            total_failed += 1

        total_processed += 1

        # Progress summary every 10 stocks
        if i % 10 == 0:
            print(f"  📈 Progress: {i}/{max_stocks} stocks processed")

    print("\n" + "=" * 40)
    print("FINAL RESULTS:")
    print(f"📊 Total processed: {total_processed}")
    print(f" Successful: {total_success}")
    print(f"❌ Failed: {total_failed}")
    print(f"📈 Success rate: {(total_success/total_processed*100):.1f}%" if total_processed > 0 else "N/A")

    if total_success > 0:
        print("🎉 SUCCESS! Extended historical data downloaded!")
        return True
    else:
        print("⚠️  No stocks were downloaded successfully")
        return False

if __name__ == "__main__":
    success = force_download_all_stocks()
    if success:
        print("\n🚀 Ready to test continuation scanner!")
    else:
        print("\n⚠️  Download failed")