#!/usr/bin/env python3
"""
NSE Bhavcopy Fetcher for MA Stock Trader
Handles same-day EOD data from NSE bhavcopy files using jugaad-data
"""

import os
import logging
import pandas as pd
import zipfile
from datetime import date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class NSEBhavcopyFetcher:
    """Fetches and processes NSE bhavcopy data using jugaad-data"""

    def __init__(self, cache_dir: str = "temp_bhavcopy"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def download_bhavcopy(self, target_date: date) -> Optional[pd.DataFrame]:
        """
        Download and parse bhavcopy for specific date using prioritized fallbacks
        Priority: Direct URL → NSE API → jugaad-data → Custom requests
        Returns DataFrame with all stock data or None if not available
        """
        # Layer 1: Direct URL (fastest, most reliable when available)
        try:
            logger.info(f"Trying direct URL for {target_date}")
            df = self._download_bhavcopy_direct(target_date)
            if df is not None:
                return df
        except Exception as e:
            logger.warning(f"Direct URL failed for {target_date}: {e}")

        # Layer 2: NSE API (dynamic resolution for complex cases)
        try:
            logger.info(f"Trying NSE API for {target_date}")
            df = self._download_bhavcopy_api(target_date)
            if df is not None:
                return df
        except Exception as e:
            logger.warning(f"NSE API failed for {target_date}: {e}")

        # Layer 3: jugaad-data (library abstraction)
        try:
            logger.info(f"Trying jugaad-data for {target_date}")
            df = self._download_with_jugaad(target_date)
            if df is not None:
                return df
        except Exception as e:
            logger.warning(f"jugaad-data failed for {target_date}: {e}")

        # Layer 4: Custom requests (legacy compatibility)
        try:
            logger.info(f"Trying custom requests for {target_date}")
            return self._download_bhavcopy_custom(target_date)
        except Exception as e:
            logger.error(f"All methods failed for {target_date}: {e}")
            return None

    def _download_bhavcopy_direct(self, target_date: date) -> Optional[pd.DataFrame]:
        """Download bhavcopy using direct URL pattern (post-2024 UDiFF)"""
        try:
            import requests
            import time
            import io

            # Direct URL pattern for UDiFF bhavcopy (confirmed working)
            yyyymmdd = target_date.strftime('%Y%m%d')
            url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.nseindia.com/all-reports',
                'Accept': 'application/zip',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }

            # Create session and get cookies
            session = requests.Session()
            session.get('https://www.nseindia.com', headers=headers, timeout=10)

            # Try with retries for timing issues
            for attempt in range(3):
                try:
                    logger.info(f"Direct URL attempt {attempt + 1} for {target_date}: {url}")
                    response = session.get(url, headers=headers, timeout=15)
                    response.raise_for_status()

                    # Process ZIP content
                    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                        csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                        if not csv_files:
                            logger.error(f"No CSV file found in ZIP for {target_date}")
                            return None

                        with zf.open(csv_files[0]) as f:
                            df = pd.read_csv(f)

                    # Process the data
                    return self._process_bhavcopy_data(df, target_date, "direct-url")

                except Exception as e:
                    logger.warning(f"Direct URL attempt {attempt + 1} failed: {e}")

                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(5)  # Wait before retry

            logger.error(f"All direct URL attempts failed for {target_date}")
            return None

        except Exception as e:
            logger.error(f"Direct URL download failed for {target_date}: {e}")
            return None

    def _download_with_jugaad(self, target_date: date) -> Optional[pd.DataFrame]:
        """Download using jugaad-data library"""
        try:
            import io
            from jugaad_data.nse import bhavcopy_save

            zip_path = bhavcopy_save(target_date, str(self.cache_dir))

            # Extract and parse CSV
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                csv_name = zip_ref.namelist()[0]
                with zip_ref.open(csv_name) as csv_file:
                    df = pd.read_csv(csv_file)

            # Process the data
            return self._process_bhavcopy_data(df, target_date, "jugaad-data")

        except Exception as e:
            logger.error(f"jugaad-data failed for {target_date}: {e}")
            return None

    def _download_bhavcopy_api(self, target_date: date) -> Optional[pd.DataFrame]:
        """Download bhavcopy using NSE API for dynamic URLs with enhanced error handling"""
        try:
            import requests
            import json
            import time

            # Format date as DD-MMM-YYYY (e.g., 06-Jan-2026)
            date_str = target_date.strftime('%d-%b-%Y')

            # Create archives parameter for API - exact name from NSE documentation
            archives_param = json.dumps([{
                "name": "CM-UDiFF Common Bhavcopy Final (zip)",
                "startDate": date_str,
                "endDate": date_str
            }])

            api_url = f"https://www.nseindia.com/api/reports?archives={archives_param}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.nseindia.com/all-reports',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            }

            # Create session and get cookies
            session = requests.Session()
            session.get('https://www.nseindia.com', headers=headers, timeout=10)

            zip_url = None

            # Try API with retries for timing issues
            for attempt in range(3):
                try:
                    logger.info(f"API attempt {attempt + 1} for {target_date}")
                    response = session.get(api_url, headers=headers, timeout=15)

                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"API response received: {type(data)}")

                        # Extract download link with multiple fallback paths
                        if isinstance(data, list) and data and 'link' in data[0]:
                            zip_url = data[0]['link']
                        elif data and 'link' in data:
                            zip_url = data['link']
                        elif data and 'data' in data and isinstance(data['data'], list) and data['data']:
                            zip_url = data['data'][0].get('link')

                        if zip_url:
                            logger.info(f"Found download URL via API: {zip_url[:50]}...")
                            break

                    logger.warning(f"API attempt {attempt + 1} failed with status {response.status_code}")

                except Exception as e:
                    logger.warning(f"API attempt {attempt + 1} error: {e}")

                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(5)  # Wait before retry

            # Fallback to direct URLs if API fails
            if not zip_url:
                logger.info("API failed, trying direct URL fallbacks...")

                # Try multiple direct URL patterns (2024+ UDiFF format)
                yyyymmdd = target_date.strftime('%Y%m%d')
                fallback_urls = [
                    f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip",
                    f"https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip",
                    f"https://www.nseindia.com/content/equities/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"
                ]

                for fallback_url in fallback_urls:
                    try:
                        logger.info(f"Trying direct URL: {fallback_url}")
                        test_response = session.head(fallback_url, headers=headers, timeout=10)
                        if test_response.status_code == 200:
                            zip_url = fallback_url
                            logger.info(f"Direct URL works: {zip_url[:50]}...")
                            break
                    except Exception as e:
                        logger.debug(f"Direct URL failed: {fallback_url} - {e}")

            if not zip_url:
                logger.error(f"No download URL found for {target_date} via API or direct fallbacks")
                return None

            # Download the ZIP file
            logger.info("Downloading ZIP file...")
            zip_response = session.get(zip_url, headers=headers, timeout=30)
            zip_response.raise_for_status()

            # Process ZIP content
            import io
            with zipfile.ZipFile(io.BytesIO(zip_response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logger.error(f"No CSV file found in ZIP for {target_date}")
                    return None

                with zf.open(csv_files[0]) as f:
                    df = pd.read_csv(f)

            # Process the data
            return self._process_bhavcopy_data(df, target_date, "nse-api")

        except Exception as e:
            logger.error(f"API download failed for {target_date}: {e}")
            return None

    def _download_bhavcopy_custom(self, target_date: date) -> Optional[pd.DataFrame]:
        """Custom bhavcopy download as fallback"""
        try:
            import requests
            from pathlib import Path

            # Generate URL (old format for compatibility)
            date_str = target_date.strftime('%d%b%Y').upper()
            month_str = target_date.strftime('%b').upper()
            year_str = target_date.strftime('%Y')
            url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_str}/{month_str}/cm{date_str}bhav.csv.zip"

            logger.info(f"Custom request to: {url}")

            # Create session with headers
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/zip,*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive'
            })

            response = session.get(url, timeout=30)
            response.raise_for_status()

            # Parse ZIP
            import io
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    return None

                with zf.open(csv_files[0]) as f:
                    df = pd.read_csv(f, encoding='cp1252')

            # Process the data
            return self._process_bhavcopy_data(df, target_date, "custom")

        except Exception as e:
            logger.error(f"Custom download failed for {target_date}: {e}")
            return None

    def _process_bhavcopy_data(self, df: pd.DataFrame, target_date: date, source: str) -> pd.DataFrame:
        """Process raw bhavcopy data into standardized format"""
        try:
            # Filter for equity series
            df = df[df['SERIES'] == 'EQ']

            # Standardize columns (handle both old and new formats)
            column_mapping = {
                'SYMBOL': 'symbol',
                'DATE1': 'date',  # UDiFF format
                'OPEN_PRICE': 'open',
                'HIGH_PRICE': 'high',
                'LOW_PRICE': 'low',
                'CLOSE_PRICE': 'close',
                'TTL_TRD_QNTY': 'volume',
                # Fallback for old format
                'OPEN': 'open',
                'HIGH': 'high',
                'LOW': 'low',
                'CLOSE': 'close',
                'TOTTRDQTY': 'volume'
            }

            df = df.rename(columns=column_mapping)

            # Set date if not present
            if 'date' not in df.columns:
                df['date'] = target_date
            else:
                df['date'] = pd.to_datetime(df['date']).dt.date

            # Select required columns
            df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]

            # Convert data types
            df['volume'] = df['volume'].astype(int)
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

            logger.info(f"Processed {len(df)} stocks from {source} for {target_date}")
            return df

        except Exception as e:
            logger.error(f"Error processing bhavcopy data: {e}")
            return pd.DataFrame()

    def get_latest_bhavcopy(self) -> Optional[pd.DataFrame]:
        """Get the latest available bhavcopy"""
        from datetime import timedelta

        # Try yesterday first (most likely available)
        yesterday = date.today() - timedelta(days=1)
        df = self.download_bhavcopy(yesterday)

        if df is not None:
            logger.info(f"Using bhavcopy for {yesterday}")
            return df

        logger.warning("No bhavcopy data available")
        return None

    def get_stock_from_bhavcopy(self, symbol: str, bhavcopy_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract specific stock data from bhavcopy DataFrame
        Returns formatted DataFrame for cache storage
        """
        try:
            # Find the stock (case insensitive)
            stock_data = bhavcopy_df[bhavcopy_df['symbol'].str.upper() == symbol.upper()]

            if stock_data.empty:
                logger.warning(f"Stock {symbol} not found in bhavcopy")
                return pd.DataFrame()

            # Get the row (should be only one)
            row = stock_data.iloc[0]

            # Create DataFrame in our standard format
            df = pd.DataFrame([{
                'date': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }])

            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error extracting {symbol} from bhavcopy: {e}")
            return pd.DataFrame()


# Global instance
nse_bhavcopy_fetcher = NSEBhavcopyFetcher()
