#!/usr/bin/env python3
"""
Integrated Bhavcopy System for MA Stock Trader
Seamlessly downloads latest bhavcopy and updates cache
"""

import logging
import requests
import pandas as pd
import zipfile
import io
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

from .cache_manager import cache_manager
from .reporting_system import reporting_system

logger = logging.getLogger(__name__)

class BhavcopyIntegrator:
    """Integrated bhavcopy download and cache update system"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/zip,*/*',
        })

    def _update_for_date(self, target_date: date) -> Dict:
        """
        Download bhavcopy for specific date and update all cached stocks
        Returns status and statistics
        """
        try:
            # Step 1: Download bhavcopy
            bhavcopy_df = self._download_bhavcopy(target_date)

            if bhavcopy_df is None or bhavcopy_df.empty:
                return {
                    'status': 'FAILED',
                    'error': 'Could not download bhavcopy',
                    'date': target_date
                }

            # Step 2: Update all cached stocks
            update_result = self._update_all_cached_stocks(bhavcopy_df, target_date)

            result = {
                'status': 'SUCCESS',
                'date': target_date,
                'bhavcopy_stocks': len(bhavcopy_df),
                'stocks_updated': update_result['updated'],
                'stocks_already_had_data': update_result['already_had'],
                'stocks_not_in_bhavcopy': update_result['not_in_bhavcopy'],
                'duration_seconds': 0,  # Will be set by caller
                'success_rate': update_result['success_rate']
            }

            # Step 3: Generate comprehensive reports
            try:
                report_path = reporting_system.generate_daily_reports(
                    update_date=target_date,
                    bhavcopy_data=bhavcopy_df,
                    update_stats=result
                )
                result['reports_path'] = report_path
            except Exception as e:
                logger.warning(f"Failed to generate reports: {e}")

            return result

        except Exception as e:
            logger.error(f"Bhavcopy update failed for {target_date}: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'date': target_date
            }

    def update_latest_bhavcopy(self, target_date: date = None) -> Dict:
        """
        Smart bhavcopy update - fills gaps from latest cache date to today
        Returns status and statistics
        """
        print("🚀 INTEGRATED BHAVCOPY UPDATE")
        print("=" * 50)

        start_time = datetime.now()

        if target_date is not None:
            # Manual update for specific date
            print(f"Manual Update - Target Date: {target_date}")
            result = self._update_for_date(target_date)

            if result['status'] == 'SUCCESS':
                print("\n✅ Manual update completed")
                print(f"📊 Bhavcopy stocks: {result['bhavcopy_stocks']}")
                print(f"✅ Updated: {result['stocks_updated']}")
                print(f"📅 Already had: {result['stocks_already_had_data']}")
                print(f"⚠️  Not in bhavcopy: {result['stocks_not_in_bhavcopy']}")
                print(f"📈 Success rate: {result['success_rate']:.1f}%")

            return result

        # Smart gap-filling update
        print("Smart Update - Filling data gaps...")

        # Find latest cache date
        latest_cache_date = cache_manager.get_latest_cache_date()
        if latest_cache_date is None:
            print("No cached data found, trying today...")
            return self._update_for_date(date.today())

        start_date = latest_cache_date + timedelta(days=1)
        end_date = date.today()

        print(f"Cache latest date: {latest_cache_date}")
        print(f"Filling gaps from: {start_date} to {end_date}")

        successful_updates = []
        total_updated = 0
        total_already_had = 0
        total_not_in_bhavcopy = 0

        current_date = start_date
        while current_date <= end_date:
            print(f"\n📅 Trying date: {current_date}")

            result = self._update_for_date(current_date)

            if result['status'] == 'SUCCESS':
                successful_updates.append(result)
                total_updated += result['stocks_updated']
                total_already_had += result['stocks_already_had_data']
                total_not_in_bhavcopy += result['stocks_not_in_bhavcopy']
                print(f"✅ Successfully updated {result['stocks_updated']} stocks for {current_date}")
            elif result['status'] == 'FAILED' and 'Could not download bhavcopy' in result.get('error', ''):
                print(f"❌ No bhavcopy data available for {current_date} (holiday/weekend)")
            else:
                print(f"⚠️  Failed to update for {current_date}: {result.get('error', 'Unknown error')}")

            current_date += timedelta(days=1)

        end_time = datetime.now()
        duration = end_time - start_time

        if not successful_updates:
            print("\n❌ No successful updates in the date range")
            return {
                'status': 'FAILED',
                'error': 'No successful updates in the date range',
                'date_range': f"{start_date} to {end_date}",
                'duration_seconds': duration.total_seconds()
            }

        # Return combined result
        result = {
            'status': 'SUCCESS',
            'date_range': f"{start_date} to {end_date}",
            'successful_dates': len(successful_updates),
            'total_stocks_updated': total_updated,
            'total_stocks_already_had_data': total_already_had,
            'total_stocks_not_in_bhavcopy': total_not_in_bhavcopy,
            'duration_seconds': duration.total_seconds(),
            'results': successful_updates
        }

        print("\n" + "=" * 50)
        print("SMART UPDATE COMPLETE")
        print(f"⏱️  Duration: {duration}")
        print(f"📅 Dates processed: {start_date} to {end_date}")
        print(f"✅ Successful dates: {len(successful_updates)}")
        print(f"📊 Total stocks updated: {total_updated}")
        print(f"📅 Total stocks already had data: {total_already_had}")
        print(f"⚠️  Total stocks not in bhavcopy: {total_not_in_bhavcopy}")

        return result

    def _download_bhavcopy(self, target_date: date) -> Optional[pd.DataFrame]:
        """Download and parse bhavcopy for target date"""
        try:
            # Primary URL (confirmed working)
            yyyymmdd = target_date.strftime('%Y%m%d')
            url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"

            logger.info(f"Downloading bhavcopy from: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parse ZIP content
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logger.error("No CSV file found in ZIP")
                    return None

                with zf.open(csv_files[0]) as f:
                    # Try different encodings
                    try:
                        df = pd.read_csv(f, encoding='utf-8')
                    except UnicodeDecodeError:
                        f.seek(0)
                        df = pd.read_csv(f, encoding='cp1252')

            # Process the data (new UDiFF format)
            return self._process_udiff_bhavcopy(df, target_date)

        except Exception as e:
            logger.error(f"Bhavcopy download failed: {e}")
            return None

    def _process_udiff_bhavcopy(self, df: pd.DataFrame, target_date: date) -> pd.DataFrame:
        """Process new UDiFF format bhavcopy data"""
        try:
            # Filter for equity series
            if 'SctySrs' in df.columns:
                df = df[df['SctySrs'] == 'EQ']

            # Map columns to standard format
            column_mapping = {
                'TckrSymb': 'symbol',
                'TradDt': 'date',
                'OpnPric': 'open',
                'HghPric': 'high',
                'LwPric': 'low',
                'ClsPric': 'close',
                'TtlTradgVol': 'volume'
            }

            df = df.rename(columns=column_mapping)

            # Select required columns
            required_cols = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in required_cols if col in df.columns]

            if len(available_cols) < len(required_cols):
                missing = set(required_cols) - set(available_cols)
                logger.error(f"Missing required columns: {missing}")
                return pd.DataFrame()

            df = df[available_cols]

            # Convert data types
            df['volume'] = df['volume'].astype(int)
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

            # Ensure date is correct
            df['date'] = pd.to_datetime(target_date).date()

            logger.info(f"Processed {len(df)} equity stocks from bhavcopy")
            return df

        except Exception as e:
            logger.error(f"Error processing bhavcopy data: {e}")
            return pd.DataFrame()

    def _update_all_cached_stocks(self, bhavcopy_df: pd.DataFrame, target_date: date) -> Dict:
        """Update all cached stocks with bhavcopy data"""
        from pathlib import Path

        cache_dir = Path('data/cache')
        cached_files = list(cache_dir.glob('*.pkl')) if cache_dir.exists() else []

        updated = 0
        already_had = 0
        not_in_bhavcopy = 0

        print(f"Processing {len(cached_files)} cached stocks...")

        for i, cache_file in enumerate(cached_files):
            symbol = cache_file.stem

            try:
                # Check if stock already has this date
                df = cache_manager.load_cached_data(symbol)
                if df is not None:
                    date_exists = any(
                        (hasattr(idx, 'date') and idx.date() == target_date) or
                        str(idx).startswith(target_date.strftime('%Y-%m-%d'))
                        for idx in df.index
                    )

                    if date_exists:
                        already_had += 1
                        continue

                # Check if stock is in bhavcopy
                stock_data = bhavcopy_df[bhavcopy_df['symbol'] == symbol]
                if stock_data.empty:
                    not_in_bhavcopy += 1
                    continue

                # Update cache with bhavcopy data
                row = stock_data.iloc[0]
                cache_df = pd.DataFrame([{
                    'date': row['date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }])

                cache_df['date'] = pd.to_datetime(cache_df['date'])
                cache_df.set_index('date', inplace=True)

                cache_manager.update_with_bhavcopy(symbol, cache_df)
                updated += 1

                if (i + 1) % 500 == 0:
                    print(f"  Progress: {i + 1}/{len(cached_files)} stocks")

            except Exception as e:
                logger.warning(f"Failed to update {symbol}: {e}")
                continue

        success_rate = (updated / (updated + already_had + not_in_bhavcopy)) * 100 if (updated + already_had + not_in_bhavcopy) > 0 else 0

        return {
            'updated': updated,
            'already_had': already_had,
            'not_in_bhavcopy': not_in_bhavcopy,
            'total_processed': len(cached_files),
            'success_rate': success_rate
        }

# Global instance
bhavcopy_integrator = BhavcopyIntegrator()

def update_latest_bhavcopy(target_date: date = None) -> Dict:
    """
    Integrated bhavcopy update - download and cache in one step
    """
    return bhavcopy_integrator.update_latest_bhavcopy(target_date)
