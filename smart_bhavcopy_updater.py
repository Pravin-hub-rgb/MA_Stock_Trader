#!/usr/bin/env python3
"""
Smart Bhavcopy Updater for MA Stock Trader
Intelligently fills gaps in historical data by checking cache vs available bhavcopy data
"""

import logging
from datetime import datetime, timedelta, date
from pathlib import Path
import pandas as pd

from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager
from src.utils.nse_fetcher import nse_bhavcopy_fetcher

logger = logging.getLogger(__name__)

class SmartBhavcopyUpdater:
    """Smart updater that fills data gaps using bhavcopy"""

    def __init__(self):
        self.max_days_back = 30  # Look back maximum 30 days for missing data

    def get_cached_stocks_info(self) -> dict:
        """Get information about all cached stocks and their date ranges"""
        cache_dir = Path("data/cache")
        cached_files = list(cache_dir.glob("*.pkl")) if cache_dir.exists() else []

        stocks_info = {}
        for cache_file in cached_files:
            symbol = cache_file.stem
            try:
                data = cache_manager.load_cached_data(symbol)
                if data is not None and not data.empty:
                    stocks_info[symbol] = {
                        'last_date': data.index.max(),
                        'total_days': len(data),
                        'date_range': f"{data.index.min()} to {data.index.max()}"
                    }
            except Exception as e:
                logger.warning(f"Error reading cache for {symbol}: {e}")

        return stocks_info

    def find_missing_dates_for_stock(self, symbol: str, stock_info: dict) -> list:
        """Find which dates are missing for a specific stock"""
        last_cached_date = stock_info['last_date']
        today = date.today()

        # Look back from today to find potential missing dates
        # But don't go back further than last cached date + max_days_back
        start_check = min(last_cached_date + timedelta(days=1),
                         today - timedelta(days=self.max_days_back))

        missing_dates = []

        # Check each date from start_check to yesterday
        current_date = start_check
        while current_date < today:
            # Skip weekends (no trading)
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                missing_dates.append(current_date)
            current_date += timedelta(days=1)

        return missing_dates

    def get_available_bhavcopy_dates(self, missing_dates: list) -> list:
        """Check which of the missing dates have available bhavcopy data"""
        available_dates = []

        for check_date in missing_dates:
            try:
                # Try to download bhavcopy for this date
                bhavcopy_df = nse_bhavcopy_fetcher.download_bhavcopy(check_date)
                if bhavcopy_df is not None and not bhavcopy_df.empty:
                    available_dates.append(check_date)
                    logger.info(f"Found bhavcopy data for {check_date}")
                else:
                    logger.info(f"No bhavcopy data for {check_date}")
            except Exception as e:
                logger.warning(f"Error checking bhavcopy for {check_date}: {e}")

        return available_dates

    def update_stock_with_missing_dates(self, symbol: str, available_dates: list) -> dict:
        """Update a specific stock with missing bhavcopy data"""
        updated_dates = []
        errors = []

        for bhavcopy_date in available_dates:
            try:
                # Download bhavcopy for this date
                bhavcopy_df = nse_bhavcopy_fetcher.download_bhavcopy(bhavcopy_date)
                if bhavcopy_df is None or bhavcopy_df.empty:
                    errors.append(f"No data for {bhavcopy_date}")
                    continue

                # Extract this stock's data
                stock_data = nse_bhavcopy_fetcher.get_stock_from_bhavcopy(symbol, bhavcopy_df)
                if stock_data.empty:
                    errors.append(f"No {symbol} data in {bhavcopy_date} bhavcopy")
                    continue

                # Update cache
                cache_manager.update_with_bhavcopy(symbol, stock_data)
                updated_dates.append(bhavcopy_date)
                logger.info(f"Added {bhavcopy_date} data for {symbol}")

            except Exception as e:
                errors.append(f"Error updating {bhavcopy_date}: {str(e)}")
                logger.error(f"Error updating {symbol} with {bhavcopy_date}: {e}")

        return {
            'symbol': symbol,
            'updated_dates': updated_dates,
            'errors': errors,
            'success_count': len(updated_dates)
        }

    def update_all_stocks_smart(self) -> dict:
        """Smart update for all cached stocks"""
        print("=" * 70)
        print("SMART BHAVCOPY UPDATER - Filling Data Gaps")
        print("=" * 70)

        start_time = datetime.now()

        # Get all cached stocks info
        print("\n🔍 Analyzing cached stocks...")
        stocks_info = self.get_cached_stocks_info()
        total_stocks = len(stocks_info)

        if total_stocks == 0:
            return {'error': 'No cached stocks found'}

        print(f"Found {total_stocks} cached stocks")

        # Find missing dates for each stock
        print("\n📅 Finding missing dates...")
        stocks_missing_data = {}

        for symbol, info in stocks_info.items():
            missing_dates = self.find_missing_dates_for_stock(symbol, info)
            if missing_dates:
                stocks_missing_data[symbol] = {
                    'info': info,
                    'missing_dates': missing_dates
                }

        stocks_with_gaps = len(stocks_missing_data)
        print(f"Found {stocks_with_gaps} stocks with potential data gaps")

        if stocks_with_gaps == 0:
            print("\n✅ All stocks appear to be up to date!")
            return {'message': 'All stocks up to date'}

        # Check which missing dates have available bhavcopy
        print("\n📥 Checking available bhavcopy data...")
        all_missing_dates = set()
        for stock_data in stocks_missing_data.values():
            all_missing_dates.update(stock_data['missing_dates'])

        missing_dates_list = sorted(list(all_missing_dates))
        print(f"Checking {len(missing_dates_list)} potential dates: {missing_dates_list[0]} to {missing_dates_list[-1]}")

        available_dates = self.get_available_bhavcopy_dates(missing_dates_list)
        print(f"Found {len(available_dates)} dates with available bhavcopy")

        if not available_dates:
            print("\n❌ No new bhavcopy data available to add")
            return {'message': 'No new data available'}

        # Update stocks with available data
        print("\n🔄 Updating stocks with missing data...")
        results = {
            'total_stocks_analyzed': total_stocks,
            'stocks_with_gaps': stocks_with_gaps,
            'available_dates': len(available_dates),
            'updated_stocks': 0,
            'total_updates': 0,
            'errors': 0,
            'stock_results': []
        }

        for symbol, stock_data in stocks_missing_data.items():
            # Find which of this stock's missing dates are available
            stock_available_dates = [d for d in stock_data['missing_dates'] if d in available_dates]

            if stock_available_dates:
                print(f"  Updating {symbol}: adding {len(stock_available_dates)} dates...")
                update_result = self.update_stock_with_missing_dates(symbol, stock_available_dates)

                results['stock_results'].append(update_result)
                results['total_updates'] += update_result['success_count']
                results['errors'] += len(update_result['errors'])

                if update_result['success_count'] > 0:
                    results['updated_stocks'] += 1

        # Summary
        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n⏱️  Total time: {duration}")
        print("\n📊 UPDATE SUMMARY:")
        print(f"   Stocks analyzed: {results['total_stocks_analyzed']}")
        print(f"   Stocks with gaps: {results['stocks_with_gaps']}")
        print(f"   Available bhavcopy dates: {results['available_dates']}")
        print(f"   Stocks updated: {results['updated_stocks']}")
        print(f"   Total data points added: {results['total_updates']}")
        if results['errors'] > 0:
            print(f"   Errors: {results['errors']}")

        # Show sample updated stocks
        if results['stock_results']:
            print("\n📈 Sample updates:")
            for result in results['stock_results'][:3]:  # Show first 3
                if result['success_count'] > 0:
                    print(f"   {result['symbol']}: +{result['success_count']} days")

        return results

def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Starting Smart Bhavcopy Updater...")
    print("This will intelligently fill gaps in your cached data using bhavcopy")

    updater = SmartBhavcopyUpdater()

    # Confirm before proceeding
    confirm = input("\nRun smart bhavcopy update? (yes/no): ").strip().lower()

    if confirm == 'yes':
        result = updater.update_all_stocks_smart()

        if 'error' in result:
            print(f"\n❌ Error: {result['error']}")
        elif 'message' in result:
            print(f"\nℹ️  {result['message']}")
        else:
            print("\n✅ Smart update completed successfully!")
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()