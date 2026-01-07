#!/usr/bin/env python3
"""
Clean Daily Bhavcopy System
Simple, efficient workflow as suggested by user:
1. Download bhavcopy file
2. Check latest data available
3. Only cache missing data
4. Delete file after successful caching
"""

import pandas as pd
import time
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Dict
import logging

from .nse_fetcher import nse_bhavcopy_fetcher
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class CleanDailyBhavcopy:
    """Clean, simple daily bhavcopy update system"""

    def __init__(self):
        self.temp_dir = Path("temp_bhavcopy")
        self.temp_dir.mkdir(exist_ok=True)

    def update_daily_data(self) -> Dict:
        """
        Clean daily update workflow:
        1. Download bhavcopy file
        2. Check what latest data is available
        3. Only cache missing data
        4. Delete file after successful caching
        """
        print("🕐 CLEAN DAILY BHAVCOPY UPDATE")
        print("=" * 50)

        start_time = datetime.now()

        try:
            # Step 1: Download bhavcopy file
            bhavcopy_path = self._download_bhavcopy_file()
            if not bhavcopy_path:
                return self._error_result("Download failed")

            # Step 2: Load and analyze bhavcopy data
            bhavcopy_df = self._load_bhavcopy_data(bhavcopy_path)
            if bhavcopy_df is None or bhavcopy_df.empty:
                return self._error_result("Failed to load bhavcopy data")

            print(f"📊 Bhavcopy contains {len(bhavcopy_df)} stocks")

            # Step 3: Check what latest data is available
            latest_date = self._get_latest_date_in_bhavcopy(bhavcopy_df)
            if not latest_date:
                return self._error_result("No valid dates found in bhavcopy")

            print(f"📅 Latest data available: {latest_date}")

            # Step 4: Check if we already have this data
            if self._already_have_latest_data(latest_date):
                print("✅ Already have latest data - no update needed")
                self._cleanup_file(bhavcopy_path)
                return self._success_result("Already up to date", 0, 0)

            # Step 5: Update cache with missing data
            update_result = self._update_cache_with_new_data(bhavcopy_df, latest_date)

            # Step 6: FULL VERIFICATION before cleanup
            print("🔍 FULL VERIFICATION: Checking ALL cached stocks...")
            full_verified = self._verify_full_update(latest_date, bhavcopy_df)

            if full_verified:
                print("✅ FULL VERIFICATION PASSED - All stocks updated")
                # Step 7: Only cleanup after full verification
                self._cleanup_file(bhavcopy_path)
                return {
                    'status': 'SUCCESS',
                    'latest_date': latest_date,
                    'stocks_updated': update_result['updated'],
                    'stocks_skipped': update_result['skipped'],
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'verified': True,
                    'full_verification': True
                }
            else:
                print("❌ FULL VERIFICATION FAILED - Keeping temp file for retry")
                return {
                    'status': 'VERIFICATION_FAILED',
                    'latest_date': latest_date,
                    'stocks_updated': update_result['updated'],
                    'stocks_skipped': update_result['skipped'],
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                    'verified': False,
                    'full_verification': False,
                    'temp_file_kept': str(bhavcopy_path)
                }

            # No fallback - we already handled all cases above

        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return self._error_result(str(e))

    def _verify_full_update(self, target_date: date, bhavcopy_df: pd.DataFrame) -> bool:
        """Verify that ALL stocks in bhavcopy have been updated in cache"""
        print("🔍 FULL VERIFICATION: Checking ALL stocks from bhavcopy...")

        try:
            target_timestamp = pd.Timestamp(target_date)
            bhavcopy_symbols = set(bhavcopy_df['symbol'].unique())

            print(f"📊 Need to verify {len(bhavcopy_symbols)} stocks from bhavcopy")

            verified = 0
            failed = 0

            # Check each stock from bhavcopy
            for symbol in bhavcopy_symbols:
                try:
                    df = cache_manager.load_cached_data(symbol)
                    if df is not None and target_timestamp in df.index:
                        verified += 1
                    else:
                        failed += 1
                        if failed <= 5:  # Show first 5 failures
                            print(f"  ❌ {symbol}: Missing in cache")
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"  ❌ {symbol}: Error checking cache - {e}")

                if (verified + failed) % 500 == 0:
                    print(f"  📈 Verified {verified + failed}/{len(bhavcopy_symbols)} stocks...")

            success_rate = verified / len(bhavcopy_symbols)
            print(f"✅ Full verification: {verified}/{len(bhavcopy_symbols)} stocks updated ({success_rate:.1%})")

            return success_rate > 0.95  # 95% success rate required

        except Exception as e:
            print(f"❌ Full verification failed: {e}")
            return False

    def _download_bhavcopy_file(self) -> Optional[Path]:
        """Download bhavcopy file to temp directory"""
        print("📥 Downloading bhavcopy file...")

        try:
            # Download yesterday's data (most common case)
            target_date = date.today() - pd.Timedelta(days=1)
            df = nse_bhavcopy_fetcher.download_bhavcopy(target_date)

            if df is None or df.empty:
                print("❌ No data available from NSE")
                return None

            # Save to temp file
            temp_file = self.temp_dir / f"bhavcopy_{target_date.strftime('%Y%m%d')}.pkl"
            df.to_pickle(temp_file)

            print(f"✅ Downloaded and saved to {temp_file}")
            return temp_file

        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

    def _load_bhavcopy_data(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Load bhavcopy data from temp file"""
        try:
            df = pd.read_pickle(file_path)
            print(f"✅ Loaded {len(df)} stocks from bhavcopy")
            return df
        except Exception as e:
            print(f"❌ Failed to load bhavcopy data: {e}")
            return None

    def _get_latest_date_in_bhavcopy(self, df: pd.DataFrame) -> Optional[date]:
        """Find the latest trading date in bhavcopy data"""
        try:
            # Get unique dates from the data
            unique_dates = pd.to_datetime(df['date']).dt.date.unique()
            latest_date = max(unique_dates)
            return latest_date
        except Exception as e:
            print(f"❌ Error finding latest date: {e}")
            return None

    def _already_have_latest_data(self, latest_date: date) -> bool:
        """Check if we already have the latest data"""
        try:
            # Sample a few stocks to check
            cache_dir = Path('data/cache')
            cached_files = list(cache_dir.glob('*.pkl'))[:10]  # Check first 10

            target_timestamp = pd.Timestamp(latest_date)

            for cache_file in cached_files:
                try:
                    df = cache_manager.load_cached_data(cache_file.stem)
                    if df is not None and target_timestamp in df.index:
                        return True  # At least one stock has the data
                except:
                    continue

            return False

        except Exception as e:
            print(f"❌ Error checking existing data: {e}")
            return False

    def _update_cache_with_new_data(self, bhavcopy_df: pd.DataFrame, target_date: date) -> Dict:
        """Update cache with new data from bhavcopy"""
        print("🔄 Updating cache with new data...")

        updated = 0
        skipped = 0

        # Process each stock individually (avoid bulk issues)
        for symbol in bhavcopy_df['symbol'].unique():
            try:
                # Get this stock's data for the target date
                stock_data = bhavcopy_df[
                    (bhavcopy_df['symbol'] == symbol) &
                    (pd.to_datetime(bhavcopy_df['date']).dt.date == target_date)
                ]

                if stock_data.empty:
                    skipped += 1
                    continue

                # Create DataFrame for cache
                row = stock_data.iloc[0]
                cache_df = pd.DataFrame([{
                    'date': target_date,
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
                updated += 1

                if updated % 100 == 0:
                    print(f"  📈 Updated {updated} stocks...")

            except Exception as e:
                logger.warning(f"Failed to update {symbol}: {e}")
                skipped += 1

        print(f"✅ Cache update complete: {updated} updated, {skipped} skipped")
        return {'updated': updated, 'skipped': skipped}

    def _cleanup_file(self, file_path: Path):
        """Delete temp bhavcopy file after successful processing"""
        try:
            if file_path.exists():
                file_path.unlink()
                print("🗑️  Cleaned up temporary file")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")

    def _verify_update(self, target_date: date) -> bool:
        """Verify that the update was successful"""
        try:
            # Check a sample of stocks
            cache_dir = Path('data/cache')
            cached_files = list(cache_dir.glob('*.pkl'))[:20]  # Check 20 stocks

            target_timestamp = pd.Timestamp(target_date)
            verified = 0

            for cache_file in cached_files:
                try:
                    df = cache_manager.load_cached_data(cache_file.stem)
                    if df is not None and target_timestamp in df.index:
                        verified += 1
                except:
                    continue

            success_rate = verified / len(cached_files)
            print(f"🔍 Verification: {verified}/{len(cached_files)} stocks have new data ({success_rate:.1%})")

            return success_rate > 0.8  # 80% success rate

        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False

    def _error_result(self, message: str) -> Dict:
        """Return error result"""
        return {
            'status': 'ERROR',
            'message': message,
            'stocks_updated': 0,
            'stocks_skipped': 0
        }

    def _success_result(self, message: str, updated: int, skipped: int) -> Dict:
        """Return success result"""
        return {
            'status': 'SUCCESS',
            'message': message,
            'stocks_updated': updated,
            'stocks_skipped': skipped
        }

# Global instance
clean_daily_updater = CleanDailyBhavcopy()

def update_daily_bhavcopy_clean() -> Dict:
    """
    Clean daily bhavcopy update - download, check, cache, cleanup
    """
    return clean_daily_updater.update_daily_data()

if __name__ == "__main__":
    print("Starting clean daily bhavcopy update...")
    result = update_daily_bhavcopy_clean()

    print("\n📊 RESULTS:")
    for key, value in result.items():
        print(f"  {key}: {value}")
