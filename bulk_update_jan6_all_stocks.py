#!/usr/bin/env python3
"""
Bulk Update All Cached Stocks with Jan 6, 2026 Data
Fixes the incomplete cache updates from the original bhavcopy download
"""

import pandas as pd
from datetime import date, datetime
from pathlib import Path
from src.utils.cache_manager import cache_manager
from src.utils.nse_fetcher import nse_bhavcopy_fetcher

def get_stocks_needing_update():
    """Get list of cached stocks that don't have Jan 6 data"""
    print("🔍 IDENTIFYING STOCKS NEEDING JAN 6 DATA...")
    print("-" * 50)

    cache_dir = Path('data/cache')
    cached_files = list(cache_dir.glob('*.pkl'))

    target_date = pd.Timestamp('2026-01-06')
    needs_update = []
    already_have = []

    for cache_file in cached_files:
        symbol = cache_file.stem
        try:
            df = cache_manager.load_cached_data(symbol)
            if df is not None and not df.empty:
                if target_date in df.index:
                    already_have.append(symbol)
                else:
                    needs_update.append(symbol)
        except Exception as e:
            print(f"  Error checking {symbol}: {e}")
            needs_update.append(symbol)  # Assume needs update if error

    print(f"Stocks with Jan 6 data: {len(already_have)}")
    print(f"Stocks needing Jan 6 data: {len(needs_update)}")

    return needs_update, already_have

def bulk_update_stocks(stock_list, bhavcopy_df, batch_size=50):
    """Update stocks in batches with proper error handling"""
    print(f"\n🔄 UPDATING {len(stock_list)} STOCKS IN BATCHES OF {batch_size}")
    print("=" * 60)

    total_updated = 0
    total_failed = 0

    for i in range(0, len(stock_list), batch_size):
        batch = stock_list[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(stock_list) + batch_size - 1) // batch_size

        print(f"\n📦 Batch {batch_num}/{total_batches} ({len(batch)} stocks)")

        batch_updated = 0
        batch_failed = 0

        for symbol in batch:
            try:
                # Get this stock's data from bhavcopy
                stock_data = bhavcopy_df[bhavcopy_df['symbol'] == symbol]

                if stock_data.empty:
                    print(f"  ⚠️  {symbol}: Not found in bhavcopy data")
                    batch_failed += 1
                    continue

                row = stock_data.iloc[0]

                # Create cache DataFrame
                cache_df = pd.DataFrame([{
                    'date': row['date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }])

                cache_df['date'] = pd.to_datetime(cache_df['date'])
                cache_df.set_index('date', inplace=True)

                # Update cache
                cache_manager.update_with_bhavcopy(symbol, cache_df)

                print(f"  ✅ {symbol}")
                batch_updated += 1
                total_updated += 1

            except Exception as e:
                print(f"  ❌ {symbol}: {str(e)[:50]}...")
                batch_failed += 1
                total_failed += 1

        print(f"  📊 Batch complete: {batch_updated} updated, {batch_failed} failed")

        # Progress summary every 10 batches
        if batch_num % 10 == 0:
            progress = (i + len(batch)) / len(stock_list) * 100
            print(f"  📈 Overall progress: {progress:.1f}% ({total_updated}/{len(stock_list)})")

    return total_updated, total_failed

def main():
    """Main bulk update process"""
    print("🚀 BULK JAN 6 DATA UPDATE FOR ALL CACHED STOCKS")
    print("=" * 60)

    start_time = datetime.now()

    # Step 1: Identify stocks needing update
    needs_update, already_have = get_stocks_needing_update()

    if not needs_update:
        print("\n🎉 ALL STOCKS ALREADY HAVE JAN 6 DATA!")
        return

    # Step 2: Download fresh bhavcopy data
    print("\n📥 DOWNLOADING FRESH JAN 6 BHAVCOPY DATA...")
    bhavcopy_df = nse_bhavcopy_fetcher.download_bhavcopy(date(2026, 1, 6))

    if bhavcopy_df is None or bhavcopy_df.empty:
        print("❌ FAILED TO DOWNLOAD BHAVCOPY DATA")
        print("Please run again when NSE data is available")
        return

    print(f"✅ Downloaded {len(bhavcopy_df)} stocks from NSE")

    # Step 3: Bulk update in batches
    updated, failed = bulk_update_stocks(needs_update, bhavcopy_df, batch_size=100)

    # Step 4: Final verification
    print("\n🔍 FINAL VERIFICATION...")
    _, final_already_have = get_stocks_needing_update()

    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("FINAL RESULTS:")
    print(f"⏱️  Total time: {duration}")
    print(f"📊 Stocks already had data: {len(already_have)}")
    print(f"🔄 Stocks updated: {updated}")
    print(f"❌ Update failures: {failed}")
    print(f"✅ Final total with Jan 6: {len(final_already_have)}")
    print(f"📈 Success rate: {(updated/(updated+failed)*100):.1f}%" if (updated+failed) > 0 else "N/A")

    if len(final_already_have) == len(already_have) + updated:
        print("\n🎉 SUCCESS! All targeted stocks now have Jan 6 data!")
    else:
        print(f"\n⚠️  Discrepancy detected. Expected {len(already_have) + updated}, got {len(final_already_have)}")

if __name__ == "__main__":
    main()