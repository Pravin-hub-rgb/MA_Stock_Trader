#!/usr/bin/env python3
"""
MA Stock Trader - Terminal Version
Simple terminal-based market scanner for continuation scans
"""

import sys
import os
import argparse
import pandas as pd
from datetime import date, datetime, time, timedelta
from typing import List, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scanner.scanner import scanner
from src.utils.data_fetcher import data_fetcher

def get_scan_date() -> date:
    """
    Determine the correct scan date based on current time
    During market hours (9:15-3:30): use previous day data
    After market close: use current day data
    """
    current_time = datetime.now().time()
    current_date = date.today()
    
    # Market hours: 9:15 AM to 3:30 PM
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    if market_open <= current_time <= market_close:
        # Market is open - use previous day data
        # Handle weekend case: if today is Monday, go back to Friday
        if current_date.weekday() == 0:  # Monday
            scan_date = current_date - timedelta(days=3)  # Go back to Friday
        else:
            scan_date = current_date - timedelta(days=1)  # Previous day
    else:
        # Market is closed - use current day data
        scan_date = current_date
    
    return scan_date

def display_continuation_results(results: List[Dict]):
    """Display continuation scan results in clean terminal format"""
    if not results:
        print("\n❌ No stocks met continuation criteria")
        return
    
    print(f"\n=== CONTINUATION SCANNER RESULTS ===")
    print(f"Date: {date.today().strftime('%Y-%m-%d')}")
    print(f"Total candidates: {len(results)}")
    print("\nQualified Stocks:")
    print("-" * 80)
    print(f"{'Symbol':<12} {'Price (₹)':<12} {'ADR %':<8} {'MA Status':<15} {'Volume':<10} {'Notes'}")
    print("-" * 80)
    
    for result in results:
        symbol = result['symbol']
        price = f"₹{result['price']:.2f}"
        adr_value = result.get('adr_percent', 0)
        if pd.isna(adr_value) or adr_value == 0:
            adr = "N/A"
        else:
            adr = f"{adr_value:.2f}%"
        ma_status = "✅ Rising"
        volume = "✅ Confirmed"
        notes = result.get('notes', '')
        
        print(f"{symbol:<12} {price:<12} {adr:<8} {ma_status:<15} {volume:<10} {notes}")

def run_continuation_scan():
    """Run continuation scan with clean output"""
    scan_date = get_scan_date()
    print(f"🔍 Running Continuation Scan for {scan_date}...")
    print("Criteria: Price ₹100-2000, ADR > 3%, Rising 20MA, 1M+ volume")
    
    try:
        results = scanner.run_continuation_scan(scan_date)
        display_continuation_results(results)
        return results
    except Exception as e:
        print(f"❌ Error running continuation scan: {e}")
        return []

def prepare_data(args):
    """Run data preparation to download and cache latest market data"""
    print("🚀 MA Stock Trader - Data Preparation")
    print("=" * 50)
    print("Downloading and caching latest market data...")

    days_back = args.days if hasattr(args, 'days') else 30
    max_stocks = args.stocks if hasattr(args, 'stocks') else 500

    print(f"📊 Preparing data for last {days_back} days")
    print(f"📈 Processing up to {max_stocks} stocks")

    try:
        summary = data_fetcher.prepare_market_data(days_back=days_back, max_stocks=max_stocks)

        if 'error' in summary:
            print(f"\n❌ Data preparation failed: {summary['error']}")
            return

        print(f"\n✅ Data preparation completed!")
        print(f"📊 Total stocks processed: {summary['total_stocks']}")
        print(f"🔄 Updated: {summary['updated']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        print(f"❌ Errors: {summary['errors']}")
        print(f"📅 Total trading days added: {summary['total_days_added']}")

        if summary['updated'] > 0:
            print("\n💾 Cache updated with latest market data")
            print("🎯 Ready for scanning with fresh data!")
    except Exception as e:
        print(f"\n❌ Error during data preparation: {e}")

def main():
    """Main entry point with command line argument handling"""
    parser = argparse.ArgumentParser(description='MA Stock Trader Terminal')
    parser.add_argument('--prep', action='store_true',
                       help='Prepare/download latest market data and update cache')
    parser.add_argument('--days', type=int, default=30,
                       help='Number of days of historical data to prepare (default: 30)')
    parser.add_argument('--stocks', type=int, default=500,
                       help='Maximum number of stocks to process (default: 500)')

    args = parser.parse_args()

    if args.prep:
        prepare_data(args)
        return

    # Default: Run continuation scan
    print("🚀 MA Stock Trader - Terminal Version")
    print("=" * 50)
    print("Continuation Scan")
    print("Running scan...")

    results = run_continuation_scan()

    if results:
        print(f"\n✅ Scan completed successfully!")
        print(f"Found {len(results)} potential continuation candidates")
    else:
        print("\nNo stocks met the continuation criteria")
        print("This is normal - market conditions may not favor continuation setups today")

    print("\nKey criteria checked:")
    print("✅ Price range: ₹100-2000")
    print("✅ ADR > 3% (volatility check)")
    print("✅ Rising 20-day moving average")
    print("✅ 1M+ volume in last month")

if __name__ == "__main__":
    main()
