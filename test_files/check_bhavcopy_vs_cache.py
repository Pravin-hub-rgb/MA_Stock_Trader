#!/usr/bin/env python3
"""
Check if stocks missing Jan 6 data were actually in the bhavcopy file
"""

import pandas as pd
from pathlib import Path
from src.utils.cache_manager import cache_manager

def check_bhavcopy_vs_cache():
    """Compare bhavcopy contents with cache status for sample stocks"""

    print("🔍 CHECKING BHAVCOPY vs CACHE DISCREPANCY")
    print("=" * 50)

    # First, let's see if we can find any saved bhavcopy data
    bhavcopy_files = list(Path("temp_bhavcopy").glob("*.csv"))
    if bhavcopy_files:
        print(f"Found {len(bhavcopy_files)} bhavcopy files in temp_bhavcopy/")
        for f in bhavcopy_files[:3]:  # Show first 3
            print(f"  {f.name}")
    else:
        print("No bhavcopy files found in temp_bhavcopy/")

    # Get sample of stocks missing Jan 6 data
    print("\n📊 GETTING SAMPLE OF STOCKS MISSING JAN 6 DATA...")

    cache_dir = Path('data/cache')
    cached_files = list(cache_dir.glob('*.pkl'))

    target_date = pd.Timestamp('2026-01-06')
    missing_stocks = []

    # Check first 20 stocks to find some missing Jan 6
    for cache_file in cached_files[:20]:
        symbol = cache_file.stem
        try:
            df = cache_manager.load_cached_data(symbol)
            if df is not None and not df.empty:
                if target_date not in df.index:
                    missing_stocks.append(symbol)
                    if len(missing_stocks) >= 5:  # Get 5 examples
                        break
        except Exception as e:
            print(f"Error checking {symbol}: {e}")

    print(f"Found {len(missing_stocks)} stocks missing Jan 6 data (sample):")
    for stock in missing_stocks:
        print(f"  - {stock}")

    # Now try to redownload and check if these stocks are in bhavcopy
    print("\n🔄 ATTEMPTING TO CHECK BHAVCOPY CONTENTS...")
    print("Note: NSE data may no longer be available, but let's try...")

    from src.utils.nse_fetcher import nse_bhavcopy_fetcher
    from datetime import date

    try:
        bhavcopy_df = nse_bhavcopy_fetcher.download_bhavcopy(date(2026, 1, 6))

        if bhavcopy_df is None or bhavcopy_df.empty:
            print("❌ Cannot redownload bhavcopy data (NSE retention expired)")

            # Alternative: Check if we have any saved bhavcopy data
            print("\n🔍 CHECKING FOR SAVED BHAVCOPY DATA...")

            # Look for any CSV files that might contain bhavcopy data
            csv_files = list(Path(".").glob("*.csv"))
            if csv_files:
                print(f"Found CSV files: {[f.name for f in csv_files]}")
                # Try to load one
                for csv_file in csv_files:
                    if "bhavcopy" in csv_file.name.lower() or csv_file.stat().st_size > 1000000:  # Large file
                        print(f"Trying to load {csv_file.name}...")
                        try:
                            test_df = pd.read_csv(csv_file, nrows=5)  # Just peek
                            print(f"Columns: {list(test_df.columns)}")
                            if 'TckrSymb' in test_df.columns or 'SYMBOL' in test_df.columns:
                                print("✅ This looks like bhavcopy data!")
                                # Load fully
                                full_df = pd.read_csv(csv_file)
                                print(f"Total stocks in saved bhavcopy: {len(full_df)}")

                                # Check our sample stocks
                                print("\n📊 CHECKING SAMPLE STOCKS IN SAVED BHAVCOPY...")
                                for stock in missing_stocks:
                                    in_bhavcopy = stock in full_df.get('TckrSymb', full_df.get('SYMBOL', [])).values
                                    print(f"  {stock}: {'✅ IN bhavcopy' if in_bhavcopy else '❌ NOT in bhavcopy'}")

                                break
                        except Exception as e:
                            print(f"Error loading {csv_file.name}: {e}")
            else:
                print("No CSV files found with bhavcopy data")

        else:
            print(f"✅ Successfully redownloaded bhavcopy with {len(bhavcopy_df)} stocks")

            # Check our sample stocks
            print("\n📊 CHECKING SAMPLE STOCKS IN CURRENT BHAVCOPY...")
            for stock in missing_stocks:
                in_bhavcopy = stock in bhavcopy_df['symbol'].values
                print(f"  {stock}: {'✅ IN bhavcopy' if in_bhavcopy else '❌ NOT in bhavcopy'}")

                if in_bhavcopy:
                    # Show the data
                    stock_data = bhavcopy_df[bhavcopy_df['symbol'] == stock].iloc[0]
                    print(f"      OHLC: O:{stock_data['open']:.2f} H:{stock_data['high']:.2f} L:{stock_data['low']:.2f} C:{stock_data['close']:.2f}")

    except Exception as e:
        print(f"❌ Error checking bhavcopy: {e}")

    print("\n" + "=" * 50)
    print("ANALYSIS:")
    print("If stocks are IN bhavcopy but missing from cache:")
    print("  → Cache update failed (fixable)")
    print("If stocks are NOT in bhavcopy:")
    print("  → NSE filtering issue or data not available")

if __name__ == "__main__":
    check_bhavcopy_vs_cache()