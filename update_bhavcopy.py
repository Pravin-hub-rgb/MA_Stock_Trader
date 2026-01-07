#!/usr/bin/env python3
"""
Simple Bhavcopy Update Script
Uses the integrated bhavcopy system to download and cache latest data
"""

from datetime import date
from src.utils.bhavcopy_integrator import update_latest_bhavcopy

def main():
    """Update latest bhavcopy data"""
    print("📈 NSE BHAVCOPY UPDATE")
    print("Updates cache with latest available bhavcopy data")
    print()

    # Update latest bhavcopy (today or yesterday)
    result = update_latest_bhavcopy()

    if result['status'] == 'SUCCESS':
        print(f"\n🎉 SUCCESS! Updated cache with {result['date']} data")
        print("Your scanner will now use the latest market data!")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        print("Check NSE website availability or try again later")

if __name__ == "__main__":
    main()