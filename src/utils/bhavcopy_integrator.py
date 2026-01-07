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
from datetime import date, datetime
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

    def update_latest_bhavcopy(self, target_date: date = None) -> Dict:
        """
        Download latest bhavcopy and update all cached stocks
        Returns status and statistics
        """
        print("🚀 INTEGRATED BHAVCOPY UPDATE")
        print("=" * 50)

        start_time = datetime.now()

        if target_date is None:
            target_date = date.today()

        print(f"Target Date: {target_date}")

        try:
            # Step 1: Download bhavcopy
            print("\n📥 Downloading bhavcopy...")
            bhavcopy_df = self._download_bhavcopy(target_date)

            if bhavcopy_df is None or bhavcopy_df.empty:
                return {
                    'status': 'FAILED',
                    'error': 'Could not download bhavcopy',
                    'date': target_date
                }

            print(f"✅ Downloaded {len(bhavcopy_df)} stocks from bhavcopy")

            # Step 2: Update all cached stocks
            print("\n🔄 Updating cache with bhavcopy data...")
            update_result = self._update_all_cached_stocks(bhavcopy_df, target_date)

            end_time = datetime.now()
            duration = end_time - start_time

            result = {
                'status': 'SUCCESS',
                'date': target_date,
                'bhavcopy_stocks': len(bhavcopy_df),
                'stocks_updated': update_result['updated'],
                'stocks_already_had_data': update_result['already_had'],
                'stocks_not_in_bhavcopy': update_result['not_in_bhavcopy'],
                'duration_seconds': duration.total_seconds(),
                'success_rate': update_result['success_rate']
            }

            # Step 3: Generate comprehensive reports
            print("\n📊 Generating daily reports...")
            try:
                report_path = reporting_system.generate_daily_reports(
                    update_date=target_date,
                    bhavcopy_data=bhavcopy_df,
                    update_stats=result
                )
                print(f"📁 Reports saved to: {report_path}")
                result['reports_path'] = report_path
            except Exception as e:
                logger.warning(f"Failed to generate reports: {e}")
                print("⚠️  Report generation failed, but update was successful")

            print("\n" + "=" * 50)
            print("UPDATE COMPLETE")
            print(f"⏱️  Duration: {duration}")
            print(f"📊 Bhavcopy stocks: {len(bhavcopy_df)}")
            print(f"✅ Updated: {update_result['updated']}")
            print(f"📅 Already had: {update_result['already_had']}")
            print(f"⚠️  Not in bhavcopy: {update_result['not_in_bhavcopy']}")
            print(f"📈 Success rate: {update_result['success_rate']:.1f}%")
            if 'reports_path' in result:
                print(f"📋 Reports: {result['reports_path']}")

            return result

        except Exception as e:
            logger.error(f"Bhavcopy update failed: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'date': target_date
            }

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
