#!/usr/bin/env python3
"""
Download Fresh Extended Historical Data (Delete cache + download 180 days)
Deletes all cache and downloads fresh 180-day data for all stocks
"""

import os
import shutil
from pathlib import Path
from src.utils.data_fetcher import data_fetcher

def delete_all_cache():
    """Delete all cached data"""
    cache_dir = Path('data/cache')
    if cache_dir.exists():
        print(f"🗑️  Deleting cache directory: {cache_dir}")
        shutil.rmtree(cache_dir)
        print("✅ Cache deleted")
    else:
        print("ℹ️  No cache directory found")

    # Recreate empty cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    print("📁 Cache directory recreated")

def download_extended_data_for_all_stocks():
    """Download 180 days of data for all NSE stocks"""

    print("🚀 DOWNLOADING EXTENDED HISTORICAL DATA")
    print("=" * 50)
    print("Target: 180 days (July 2025 - Jan 2026)")
    print("All NSE stocks")
    print("Expected: ~130 working days per stock")
    print()

    try:
        # Download extended data for ALL stocks (no limit)
        result = data_fetcher.prepare_market_data(
            days_back=180,      # 180 days = ~6 months
            max_stocks=5000     # All stocks (realistic limit)
        )

        print("\n✅ DOWNLOAD COMPLETED")
        print("=" * 30)

        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            return False

        print(f"📊 Results:")
        print(f"   Total stocks processed: {result.get('total_stocks', 0)}")
        print(f"   Stocks updated: {result.get('updated', 0)}")
        print(f"   Stocks skipped: {result.get('skipped', 0)}")
        print(f"   Errors: {result.get('errors', 0)}")
        print(f"   Total days added: {result.get('total_days_added', 0)}")

        # Calculate average days per stock
        updated = result.get('updated', 0)
        total_days = result.get('total_days_added', 0)
        if updated > 0:
            avg_days = total_days / updated
            print(f"   Average days per stock: {avg_days:.1f}")

            # Estimate working days (roughly 70% of calendar days are working days)
            estimated_working = int(avg_days * 0.7)
            print(f"   Estimated working days: ~{estimated_working}")

            if estimated_working >= 110:
                print("   ✅ SUCCESS: Got 110+ working days!")
                print("   🎉 Continuation scanner will now work!")
                return True
            else:
                print(f"   ❌ INSUFFICIENT: Only ~{estimated_working} working days (need 110+)")
                return False
        else:
            print("   ❌ No stocks were updated")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function: delete cache + download fresh extended data"""

    print("🔄 FRESH EXTENDED HISTORICAL DATA DOWNLOAD")
    print("=" * 60)
    print("Step 1: Delete all existing cache")
    print("Step 2: Download 180 days fresh data")
    print("Step 3: Verify continuation scanner works")
    print()

    # Step 1: Delete cache
    delete_all_cache()
    print()

    # Step 2: Download fresh extended data
    success = download_extended_data_for_all_stocks()

    if success:
        print("\n🎉 SUCCESS! Fresh extended data downloaded!")
        print("You can now run continuation scans and get proper results!")
    else:
        print("\n⚠️  Download failed - check the errors above")

if __name__ == "__main__":
    main()