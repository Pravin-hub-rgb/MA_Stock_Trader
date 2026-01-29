#!/usr/bin/env python3
"""
Bhavcopy Updater for MA Stock Trader
Updates all cached stocks with latest bhavcopy data (Jan 6, 2026)
"""

import logging
from datetime import datetime
from pathlib import Path

from src.utils.data_fetcher import data_fetcher

logger = logging.getLogger(__name__)

def update_all_stocks_with_bhavcopy(target_date=None):
    """Update all cached stocks with latest bhavcopy data"""
    if target_date is None:
        from datetime import date
        target_date = date.today()

    print("=" * 60)
    print(f"BHAVCOPY UPDATER - Adding {target_date} Data")
    print("=" * 60)

    start_time = datetime.now()

    try:
        # Update all stocks with latest bhavcopy
        result = data_fetcher.update_daily_bhavcopy()

        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n⏱️  Total time: {duration}")

        if 'error' not in result:
            print(" Bhavcopy update completed successfully!")
            print(f"   Total stocks in bhavcopy: {result['total_stocks']}")
            print(f"   Stocks updated: {result['updated']}")
            if result['errors'] > 0:
                print(f"   Errors: {result['errors']}")

            success_rate = (result['updated'] / result['total_stocks'] * 100) if result['total_stocks'] > 0 else 0
            print(f"   Success rate: {success_rate:.1f}%")

        else:
            print(f"❌ Error: {result['error']}")
            print("\n💡 Note: Bhavcopy data is typically available after 6-7 PM IST on trading days")
            print("   If you're testing, try using a historical date that has available data")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_cache_status():
    """Check current cache status"""
    from src.utils.cache_manager import cache_manager
    from pathlib import Path

    cache_dir = Path("data/cache")
    cached_files = list(cache_dir.glob("*.pkl")) if cache_dir.exists() else []

    print("\n" + "="*50)
    print("CACHE STATUS AFTER BHAVCOPY UPDATE")
    print("="*50)
    print(f"Cached Files: {len(cached_files)}")
    print(f"Cache Size: {sum(f.stat().st_size for f in cached_files) / (1024*1024):.2f} MB")

    # Check a few sample stocks
    if cached_files:
        print("\nSample stock data ranges:")
        for i, cache_file in enumerate(cached_files[:5]):
            symbol = cache_file.stem
            try:
                data = cache_manager.load_cached_data(symbol)
                if data is not None and not data.empty:
                    date_range = f"{data.index.min()} to {data.index.max()}"
                    days = len(data)
                    print(f"  {symbol}: {days} days ({date_range})")
            except Exception as e:
                print(f"  {symbol}: Error loading data")

def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Starting Bhavcopy Updater...")
    print("This will add latest available bhavcopy data to all cached stocks")

    print("\nOptions:")
    print("1. Use latest bhavcopy (today/yesterday)")
    print("2. Test with specific historical date")

    choice = input("\nChoose option (1-2): ").strip()

    if choice == '1':
        print("\nUsing latest bhavcopy (Jan 6, 2026)...")
        update_all_stocks_with_bhavcopy()
        check_cache_status()

    elif choice == '2':
        from datetime import date
        test_date = input("Enter date (YYYY-MM-DD) or press Enter for Dec 20, 2025: ").strip()
        if not test_date:
            test_date = "2025-12-20"

        try:
            target_date = date.fromisoformat(test_date)
            print(f"\nTesting with bhavcopy for {target_date}...")
            update_all_stocks_with_bhavcopy(target_date)
            check_cache_status()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")

    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()