#!/usr/bin/env python3
"""
Historical Data Cacher for MA Stock Trader
Simple script to download and cache historical data for first 50 NSE stocks
Tracks incomplete data that needs complete data till Jan 5
"""

import json
import logging
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict
import pandas as pd

from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager

logger = logging.getLogger(__name__)

class HistoricalDataCacher:
    """Simple cacher for historical data with incomplete tracking"""

    def __init__(self):
        self.incomplete_file = "incomplete_stocks.json"
        self.target_date = date(2026, 1, 5)  # Jan 5, 2026
        self.continuation_days = 120  # 80 + 40 buffer
        self.reversal_days = 60       # 30 + 30 buffer

    def check_data_complete(self, symbol: str) -> bool:
        """Check if stock has complete data till target date"""
        try:
            data = cache_manager.load_cached_data(symbol)
            if data is None or data.empty:
                return False

            # Check if data reaches target date (date is the index)
            return data.index.max() >= self.target_date

        except Exception:
            return False

    def load_incomplete_stocks(self) -> list:
        """Load list of incomplete stocks"""
        if os.path.exists(self.incomplete_file):
            try:
                with open(self.incomplete_file, 'r') as f:
                    data = json.load(f)
                    return data.get('incomplete_stocks', [])
            except Exception:
                pass
        return []

    def save_incomplete_stocks(self, incomplete_list: list):
        """Save list of incomplete stocks"""
        try:
            data = {
                'incomplete_stocks': incomplete_list,
                'last_updated': datetime.now().isoformat(),
                'target_date': self.target_date.isoformat()
            }
            with open(self.incomplete_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving incomplete stocks: {e}")

    def update_incomplete_list(self, stocks_list: list):
        """Update the incomplete stocks list by checking current cache"""
        incomplete = []
        for stock in stocks_list:
            symbol = stock['symbol']
            if not self.check_data_complete(symbol):
                incomplete.append(stock)

        self.save_incomplete_stocks(incomplete)
        return incomplete

    def download_stock_data(self, symbol: str, days_back: int) -> bool:
        """Download and cache data for a single stock"""
        try:
            # Calculate start date
            start_date = self.target_date - timedelta(days=days_back)
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = self.target_date.strftime('%Y-%m-%d')

            logger.info(f"Downloading {days_back} days for {symbol}: {start_str} to {end_str}")

            # Fetch data
            data = data_fetcher.fetch_historical_data(symbol, start_str, end_str)

            if data.empty:
                logger.warning(f"No data fetched for {symbol}")
                return False

            # Calculate technical indicators
            data = data_fetcher.calculate_technical_indicators(data)

            # Update cache
            cache_manager.update_cache(symbol, data)

            logger.info(f"Successfully cached {len(data)} days for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error downloading data for {symbol}: {e}")
            return False

    def download_all_nse_stocks(self, batch_size: int = 100) -> Dict:
        """Download data for ALL NSE stocks in batches"""
        logger.info("Downloading data for ALL NSE stocks...")

        # Get NSE stocks
        nse_stocks = data_fetcher.fetch_nse_stocks()
        if not nse_stocks:
            return {'error': 'Failed to fetch NSE stocks'}

        total_stocks = len(nse_stocks)
        logger.info(f"Found {total_stocks} NSE stocks to process in batches of {batch_size}")

        results = {
            'total_stocks': total_stocks,
            'batches_processed': 0,
            'total_success': 0,
            'total_failed': 0,
            'failed_list': [],
            'incomplete_after_download': [],
            'timestamp': datetime.now().isoformat(),
            'estimated_time_hours': round((total_stocks * 2) / 3600, 1)  # Rough estimate: 2 seconds per stock
        }

        # Process in batches
        for batch_start in range(0, total_stocks, batch_size):
            batch_end = min(batch_start + batch_size, total_stocks)
            batch_stocks = nse_stocks[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_stocks + batch_size - 1) // batch_size

            print(f"\n🔄 Processing batch {batch_num}/{total_batches} (stocks {batch_start+1}-{batch_end})")

            batch_results = self._download_batch(batch_stocks, batch_num, total_batches)

            # Accumulate results
            results['total_success'] += batch_results['success']
            results['total_failed'] += batch_results['failed']
            results['failed_list'].extend(batch_results['failed_list'])
            results['batches_processed'] += 1

            # Progress report
            completed = results['total_success'] + results['total_failed']
            success_rate = (results['total_success'] / completed * 100) if completed > 0 else 0
            print(f"📊 Progress: {completed}/{total_stocks} stocks processed ({success_rate:.1f}% success)")

            # Optional: Add delay between batches to be respectful to API
            if batch_num < total_batches:
                import time
                print("⏳ Waiting 10 seconds before next batch...")
                time.sleep(10)

        # Final completeness check
        print("\n🔍 Performing final completeness check...")
        for stock in nse_stocks:
            symbol = stock['symbol']
            if not self.check_data_complete(symbol):
                results['incomplete_after_download'].append(symbol)

        # Update incomplete stocks list
        incomplete_stocks = [{'symbol': s} for s in results['incomplete_after_download']]
        self.save_incomplete_stocks(incomplete_stocks)

        results['final_incomplete_count'] = len(results['incomplete_after_download'])
        results['final_success_rate'] = round(results['total_success'] / total_stocks * 100, 1)

        logger.info(f"All stocks download completed: {results['total_success']}/{total_stocks} successful")
        logger.info(f"Incomplete stocks: {len(results['incomplete_after_download'])}")

        return results

    def _download_batch(self, stocks_batch: list, batch_num: int, total_batches: int) -> Dict:
        """Download data for a single batch of stocks"""
        results = {
            'success': 0,
            'failed': 0,
            'failed_list': []
        }

        for i, stock in enumerate(stocks_batch, 1):
            symbol = stock['symbol']
            stock_num = (batch_num - 1) * len(stocks_batch) + i

            # Show progress within batch
            if i % 20 == 0 or i == len(stocks_batch):
                print(f"  ↳ Batch {batch_num}/{total_batches}: {i}/{len(stocks_batch)} stocks")

            # Download continuation data (120 days - sufficient for both setups)
            if self.download_stock_data(symbol, self.continuation_days):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_list'].append(symbol)

        return results

    def download_first_50_stocks(self) -> Dict:
        """Download data for first 50 NSE stocks and track incomplete ones"""
        logger.info("Downloading data for first 50 NSE stocks...")

        # Get NSE stocks
        nse_stocks = data_fetcher.fetch_nse_stocks()
        if not nse_stocks:
            return {'error': 'Failed to fetch NSE stocks'}

        # Take first 50
        stocks_to_download = nse_stocks[:50]
        logger.info(f"Processing first {len(stocks_to_download)} stocks")

        results = {
            'total_attempted': len(stocks_to_download),
            'success': 0,
            'failed': 0,
            'failed_list': [],
            'incomplete_after_download': [],
            'timestamp': datetime.now().isoformat()
        }

        for i, stock in enumerate(stocks_to_download, 1):
            symbol = stock['symbol']
            print(f"Processing {i}/{len(stocks_to_download)}: {symbol}")

            # Download continuation data (120 days - sufficient for both setups)
            if self.download_stock_data(symbol, self.continuation_days):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['failed_list'].append(symbol)

        # After all downloads, check completeness of all 50 stocks
        for stock in stocks_to_download:
            symbol = stock['symbol']
            if not self.check_data_complete(symbol):
                results['incomplete_after_download'].append(symbol)

        # Update incomplete stocks list
        incomplete_stocks = [{'symbol': s} for s in results['incomplete_after_download']]
        self.save_incomplete_stocks(incomplete_stocks)

        logger.info(f"Download completed: {results['success']}/{results['total_attempted']} stocks")
        logger.info(f"Incomplete stocks: {len(results['incomplete_after_download'])}")

        return results

    def get_cache_status(self) -> Dict:
        """Get current cache status"""
        cache_dir = Path("data/cache")
        cached_files = list(cache_dir.glob("*.pkl")) if cache_dir.exists() else []

        total_size = 0
        if cached_files:
            total_size = sum(f.stat().st_size for f in cached_files)

        return {
            'cached_files_count': len(cached_files),
            'total_cache_size_mb': round(total_size / (1024*1024), 2),
            'cache_directory_exists': cache_dir.exists()
        }

    def print_status(self):
        """Print current status"""
        status = self.get_cache_status()
        incomplete = self.load_incomplete_stocks()

        print("\n" + "="*50)
        print("HISTORICAL DATA CACHE STATUS")
        print("="*50)
        print(f"Cached Files: {status['cached_files_count']}")
        print(f"Total Cache Size: {status['total_cache_size_mb']} MB")
        print(f"Target Date: {self.target_date}")
        print(f"Incomplete Stocks: {len(incomplete)}")
        print(f"Continuation Buffer: {self.continuation_days} days")
        print(f"Reversal Buffer: {self.reversal_days} days")

        if incomplete:
            print(f"Incomplete symbols: {', '.join([s['symbol'] for s in incomplete[:10]])}")
            if len(incomplete) > 10:
                print(f"... and {len(incomplete) - 10} more")
        print()


# Global cacher instance
data_cacher = HistoricalDataCacher()


def main():
    """Main function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("Starting Historical Data Cacher...")

    # Print current status
    data_cacher.print_status()

    # Ask user what to do
    print("OPTIONS:")
    print("1. Download first 50 stocks")
    print("2. Download ALL NSE stocks (2084+ stocks)")
    print("3. Exit")

    while True:
        try:
            choice = input("Choose option (1-3): ").strip()

            if choice == '1':
                print("\nDownloading first 50 stocks...")
                result = data_cacher.download_first_50_stocks()

                if 'error' not in result:
                    print(f"\n✅ Download completed!")
                    print(f"   Successful: {result['success']}/{result['total_attempted']}")
                    if result['failed'] > 0:
                        print(f"   Failed: {result['failed']} ({', '.join(result['failed_list'])})")

                    # Print updated status
                    data_cacher.print_status()
                else:
                    print(f"❌ Error: {result['error']}")

            elif choice == '2':
                print("\n⚠️  WARNING: This will download data for ALL NSE stocks (~2084 stocks)")
                print("   Estimated time: Several hours")
                print("   Data volume: ~400-500 MB")
                confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()

                if confirm == 'yes':
                    result = data_cacher.download_all_nse_stocks()

                    if 'error' not in result:
                        print(f"\n✅ All NSE stocks download completed!")
                        print(f"   Successful: {result['total_success']}/{result['total_stocks']} ({result['final_success_rate']}%)")
                        print(f"   Failed: {result['total_failed']}")
                        print(f"   Incomplete: {result['final_incomplete_count']}")
                        print(f"   Batches processed: {result['batches_processed']}")

                        # Print updated status
                        data_cacher.print_status()
                    else:
                        print(f"❌ Error: {result['error']}")
                else:
                    print("Operation cancelled.")

            elif choice == '3':
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please select 1-3.")

        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
