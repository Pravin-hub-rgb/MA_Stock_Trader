#!/usr/bin/env python3
"""
Daily Data Update Script
Run this every day at 6 PM to update NSE bhavcopy data
"""

from datetime import date, datetime
from src.utils.daily_bhavcopy_updater import update_daily_bhavcopy

def main():
    """Main daily update function"""
    print("🕐 STARTING DAILY DATA UPDATE")
    print("=" * 50)
    print(f"Time: {datetime.now()}")
    print("Target: Yesterday's NSE bhavcopy data")
    print()

    # Update yesterday's data (most common case)
    result = update_daily_bhavcopy()

    print("\n" + "=" * 50)
    print("📊 DAILY UPDATE RESULTS:")
    print(f"Status: {result['status']}")
    print(f"Duration: {result.get('duration_seconds', 'N/A'):.1f} seconds")
    print(f"Stocks Processed: {result['stocks_processed']}")
    print(f"Stocks Updated: {result['stocks_updated']}")
    print(f"Stocks Failed: {result['stocks_failed']}")
    print(f"Stocks Skipped: {result['stocks_skipped']}")
    print(f"Success Rate: {result['success_rate']:.1f}%")

    # Summary
    if result['success_rate'] > 95:
        print("\n🎉 EXCELLENT: Daily update completed successfully!")
        print("All cached stocks now have the latest data.")
    elif result['success_rate'] > 80:
        print(f"\n⚠️  GOOD: Most stocks updated ({result['success_rate']:.1f}%)")
        print("Some stocks may need manual attention.")
    else:
        print(f"\n❌ ISSUES: Low success rate ({result['success_rate']:.1f}%)")
        print("Check logs and NSE data availability.")

    print("\n💡 Next update will run automatically tomorrow at 6 PM")

if __name__ == "__main__":
    main()
