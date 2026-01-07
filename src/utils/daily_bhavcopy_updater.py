#!/usr/bin/env python3
"""
Daily Bhavcopy Updater - Robust Production Solution
Handles daily NSE bhavcopy data updates with individual stock processing
"""

import pandas as pd
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .nse_fetcher import nse_bhavcopy_fetcher
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class DailyBhavcopyUpdater:
    """Robust daily bhavcopy update system with individual stock processing"""

    def __init__(self, batch_size: int = 25, max_retries: int = 3):
        self.batch_size = batch_size  # Process in small batches
        self.max_retries = max_retries
        self.stats = {
            'start_time': None,
            'end_time': None,
            'stocks_processed': 0,
            'stocks_updated': 0,
            'stocks_failed': 0,
            'stocks_skipped': 0
        }

    def update_daily_data(self, target_date: Optional[date] = None) -> Dict:
        """
        Main method to update daily bhavcopy data
        Processes stocks individually to avoid bulk failures
        """
        if target_date is None:
            # Default to yesterday (most common use case)
            target_date = date.today() - timedelta(days=1)

        logger.info(f"Starting daily bhavcopy update for {target_date}")
        self.stats['start_time'] = datetime.now()

        try:
            # Step 1: Download fresh bhavcopy data
            bhavcopy_df = self._download_bhavcopy_data(target_date)
            if bhavcopy_df is None or bhavcopy_df.empty:
                logger.error("Failed to download bhavcopy data")
                return self._finalize_stats("FAILED: Download failed")

            logger.info(f"Downloaded {len(bhavcopy_df)} stocks from NSE")

            # Step 2: Get list of stocks that need updating
            stocks_to_update = self._get_stocks_needing_update(target_date)
            logger.info(f"Found {len(stocks_to_update)} stocks needing {target_date} data")

            if not stocks_to_update:
                logger.info("All stocks already have current data")
                return self._finalize_stats("SUCCESS: All up to date")

            # Step 3: Process stocks in small batches
            self._process_stocks_in_batches(stocks_to_update, bhavcopy_df, target_date)

            # Step 4: Final verification
            final_check = self._verify_updates(target_date, stocks_to_update)

            return self._finalize_stats(final_check)

        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return self._finalize_stats(f"FAILED: {e}")

    def _download_bhavcopy_data(self, target_date: date) -> Optional[pd.DataFrame]:
        """Download and validate bhavcopy data"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Download attempt {attempt + 1}/{self.max_retries} for {target_date}")
                df = nse_bhavcopy_fetcher.download_bhavcopy(target_date)

                if df is not None and not df.empty and len(df) > 1000:
                    logger.info(f"Successfully downloaded {len(df)} stocks")
                    return df
                else:
                    logger.warning(f"Download returned invalid data (attempt {attempt + 1})")

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")

            if attempt < self.max_retries - 1:
                time.sleep(5)  # Wait before retry

        logger.error("All download attempts failed")
        return None

    def _get_stocks_needing_update(self, target_date: date) -> List[str]:
        """Get list of cached stocks that don't have data for target_date"""
        cache_dir = Path('data/cache')
        cached_files = list(cache_dir.glob('*.pkl'))

        needs_update = []
        target_timestamp = pd.Timestamp(target_date)

        for cache_file in cached_files:
            symbol = cache_file.stem
            try:
                df = cache_manager.load_cached_data(symbol)
                if df is not None and not df.empty:
                    # Check if target date exists
                    if target_timestamp not in df.index:
                        needs_update.append(symbol)
                else:
                    # No existing data, needs update
                    needs_update.append(symbol)

            except Exception as e:
                logger.warning(f"Error checking {symbol}: {e}")
                needs_update.append(symbol)  # Assume needs update

        return needs_update

    def _process_stocks_in_batches(self, stock_list: List[str], bhavcopy_df: pd.DataFrame,
                                 target_date: date):
        """Process stocks in small batches with individual error handling"""
        total_batches = (len(stock_list) + self.batch_size - 1) // self.batch_size
        logger.info(f"Processing {len(stock_list)} stocks in {total_batches} batches")

        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(stock_list))
            batch = stock_list[start_idx:end_idx]

            logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch)} stocks)")

            batch_results = self._process_batch(batch, bhavcopy_df, target_date)

            # Update stats
            self.stats['stocks_processed'] += len(batch)
            self.stats['stocks_updated'] += batch_results['updated']
            self.stats['stocks_failed'] += batch_results['failed']
            self.stats['stocks_skipped'] += batch_results['skipped']

            # Progress logging
            progress = (end_idx / len(stock_list)) * 100
            logger.info(f"  📈 Overall progress: {progress:.1f}% ({self.stats['stocks_updated']}/{len(stock_list)})")
            # Small delay between batches to avoid overwhelming system
            time.sleep(0.1)

    def _process_batch(self, batch: List[str], bhavcopy_df: pd.DataFrame,
                      target_date: date) -> Dict[str, int]:
        """Process a single batch of stocks individually"""
        results = {'updated': 0, 'failed': 0, 'skipped': 0}

        for symbol in batch:
            try:
                # Check if stock exists in bhavcopy data
                stock_data = bhavcopy_df[bhavcopy_df['symbol'] == symbol]

                if stock_data.empty:
                    logger.debug(f"{symbol}: Not found in bhavcopy data")
                    results['skipped'] += 1
                    continue

                # Get the stock's data
                row = stock_data.iloc[0]

                # Create individual DataFrame for this stock
                stock_df = pd.DataFrame([{
                    'date': target_date,
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }])

                # Set proper datetime index
                stock_df['date'] = pd.to_datetime(stock_df['date'])
                stock_df.set_index('date', inplace=True)

                # Update cache for this individual stock
                cache_manager.update_with_bhavcopy(symbol, stock_df)

                logger.debug(f"✅ {symbol}: Updated with {target_date} data")
                results['updated'] += 1

            except Exception as e:
                logger.error(f"❌ {symbol}: Update failed - {e}")
                results['failed'] += 1

        return results

    def _verify_updates(self, target_date: date, expected_stocks: List[str]) -> str:
        """Verify that updates were successful"""
        target_timestamp = pd.Timestamp(target_date)
        verified_count = 0

        for symbol in expected_stocks[:100]:  # Check first 100 for verification
            try:
                df = cache_manager.load_cached_data(symbol)
                if df is not None and target_timestamp in df.index:
                    verified_count += 1
            except:
                pass

        success_rate = (verified_count / min(100, len(expected_stocks))) * 100
        logger.info(f"Verification: {success_rate:.1f}% of stocks confirmed updated")

        if success_rate > 95:
            return "SUCCESS: Updates verified"
        elif success_rate > 80:
            return f"PARTIAL: {success_rate:.1f}% verified"
        else:
            return f"ISSUES: Only {success_rate:.1f}% verified"

    def _finalize_stats(self, status: str) -> Dict:
        """Finalize and return statistics"""
        self.stats['end_time'] = datetime.now()

        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            self.stats['duration_seconds'] = duration.total_seconds()

        self.stats['status'] = status
        self.stats['success_rate'] = (
            self.stats['stocks_updated'] /
            max(self.stats['stocks_processed'], 1) * 100
        )

        logger.info(f"Daily update completed: {status}")
        logger.info(f"Processed: {self.stats['stocks_processed']}, "
                   f"Updated: {self.stats['stocks_updated']}, "
                   f"Failed: {self.stats['stocks_failed']}")

        return self.stats.copy()

# Global instance
daily_updater = DailyBhavcopyUpdater()

def update_daily_bhavcopy(target_date: Optional[date] = None) -> Dict:
    """
    Convenience function to update daily bhavcopy data
    Call this every day at 6 PM when NSE data becomes available
    """
    return daily_updater.update_daily_data(target_date)

if __name__ == "__main__":
    # Test run - update yesterday's data
    print("🕐 Starting daily bhavcopy update...")
    result = update_daily_bhavcopy()

    print("📊 UPDATE RESULTS:")
    print(f"Status: {result['status']}")
    print(f"Duration: {result.get('duration_seconds', 'N/A'):.1f} seconds")
    print(f"Stocks Processed: {result['stocks_processed']}")
    print(f"Stocks Updated: {result['stocks_updated']}")
    print(f"Stocks Failed: {result['stocks_failed']}")
    print(f"Success Rate: {result['success_rate']:.1f}%")
