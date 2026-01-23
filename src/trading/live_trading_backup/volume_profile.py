"""
Volume Profile Calculator for Live Trading Bot
Calculates Value Area High (VAH) from previous day's volume profile
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List
import pytz

try:
    # Try relative import first (when run as part of package)
    from ...utils.upstox_fetcher import UpstoxFetcher
except ImportError:
    # Fallback to absolute import (when run standalone)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from utils.upstox_fetcher import UpstoxFetcher

logger = logging.getLogger(__name__)

# DISABLE LOGGING FOR SUBPROCESS EXECUTION
# The UI runs the bot as a subprocess and logging causes hangs
import os
if os.environ.get('PYTHONUNBUFFERED') == '1':
    # We're running in a subprocess (UI execution)
    logger.disabled = True
    logger.setLevel(logging.CRITICAL)
    # Disable all handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
else:
    # Direct execution - enable logging
    logger.setLevel(logging.INFO)
IST = pytz.timezone('Asia/Kolkata')


class VolumeProfileCalculator:
    """Calculates volume profile and VAH for stocks"""

    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.bin_size = 0.05  # Price bin size for volume distribution
        self.value_area_pct = 0.70  # 70% of volume for value area

    def get_previous_trading_day(self, current_date: date = None) -> date:
        """
        Get the previous trading day, skipping weekends and holidays
        Tests data availability to confirm it's a trading day

        Args:
            current_date: Date to calculate from (default: today)

        Returns:
            Previous trading day date
        """
        if current_date is None:
            current_date = datetime.now(IST).date()

        prev_day = current_date - timedelta(days=1)
        test_symbol = "BSE"  # Use a reliable stock for testing

        while True:
            df = self.fetch_intraday_data(test_symbol, prev_day)
            if df is not None and not df.empty:
                logger.info(f"Found trading day: {prev_day}")
                return prev_day

            logger.warning(f"No data for {prev_day} - likely holiday/weekend. Trying previous.")
            prev_day -= timedelta(days=1)

            # Safety: Prevent infinite loop (max 10 days back)
            if (current_date - prev_day).days > 10:
                raise ValueError("No trading day found in last 10 days - check API or market status.")

    def fetch_intraday_data(self, symbol: str, target_date: date) -> Optional[pd.DataFrame]:
        """
        Fetch 1-minute OHLCV data for a specific date using V3 API

        Args:
            symbol: Stock symbol
            target_date: Date to fetch data for

        Returns:
            DataFrame with OHLCV data or None if failed
        """
        try:
            import requests

            instrument_key = self.upstox_fetcher.get_instrument_key(symbol)
            if not instrument_key:
                logger.error(f"No instrument key found for {symbol}")
                return None

            # V3 URL: Note 'minutes/1' for 1-min; to_date and from_date same for one day
            date_str = target_date.strftime('%Y-%m-%d')
            url = f"https://api.upstox.com/v3/historical-candle/{instrument_key}/minutes/1/{date_str}/{date_str}"

            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.upstox_fetcher.access_token}"
            }

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(f"API error for {symbol}: {response.status_code} - {response.text}")
                return None

            data = response.json()
            if data.get('status') != 'success' or not data.get('data', {}).get('candles'):
                logger.warning(f"No candles for {symbol} on {target_date}")
                return None

            # To DataFrame (candles descending; reverse if needed)
            df = pd.DataFrame(data['data']['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi'])
            df = df[['open', 'high', 'low', 'close', 'volume']]  # Drop timestamp/oi if not needed

            # Convert numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna()

            logger.info(f"Fetched {len(df)} 1-min candles for {symbol} on {target_date}")
            return df

        except Exception as e:
            logger.error(f"Error fetching for {symbol}: {e}")
            return None

    def calculate_volume_profile(self, ohlcv_df: pd.DataFrame) -> Dict:
        """
        Calculate volume profile and VAH from OHLCV data

        Args:
            ohlcv_df: DataFrame with OHLCV data

        Returns:
            Dict with 'poc', 'vah', 'val', 'profile'
        """
        try:
            if ohlcv_df.empty or len(ohlcv_df) < 10:
                logger.warning("Insufficient OHLCV data for volume profile calculation")
                return {'poc': None, 'vah': None, 'val': None, 'profile': {}}

            # Step 1: Define price bins
            min_price = ohlcv_df['low'].min()
            max_price = ohlcv_df['high'].max()

            if min_price >= max_price:
                logger.warning("Invalid price range for volume profile")
                return {'poc': None, 'vah': None, 'val': None, 'profile': {}}

            bins = np.arange(min_price, max_price + self.bin_size, self.bin_size)
            bin_centers = (bins[:-1] + bins[1:]) / 2

            # Step 2: Initialize volume per bin
            volume_profile = {price: 0 for price in bin_centers}

            # Step 3: Distribute volume for each bar
            for _, bar in ohlcv_df.iterrows():
                bar_low = bar['low']
                bar_high = bar['high']
                bar_volume = bar['volume']

                # Find bins in this bar's range
                bar_bins = bins[(bins >= bar_low) & (bins <= bar_high)]
                if len(bar_bins) > 1:
                    # Evenly distribute volume across bins
                    vol_per_bin = bar_volume / (len(bar_bins) - 1)
                    for i in range(len(bar_bins) - 1):
                        center = (bar_bins[i] + bar_bins[i+1]) / 2
                        if center in volume_profile:
                            volume_profile[center] += vol_per_bin

            # Step 4: Find POC and calculate value area
            profile_items = sorted(volume_profile.items())
            prices = [p for p, v in profile_items]
            volumes = np.array([v for p, v in profile_items])
            total_volume = volumes.sum()

            if total_volume == 0:
                logger.warning("No volume data for profile calculation")
                return {'poc': None, 'vah': None, 'val': None, 'profile': {}}

            # Find POC
            poc_idx = np.argmax(volumes)
            poc_price = prices[poc_idx]

            # Expand to 70% value area
            accumulated_volume = volumes[poc_idx]
            left_idx, right_idx = poc_idx - 1, poc_idx + 1
            target_volume = total_volume * self.value_area_pct

            while accumulated_volume < target_volume and (left_idx >= 0 or right_idx < len(volumes)):
                left_vol = volumes[left_idx] if left_idx >= 0 else 0
                right_vol = volumes[right_idx] if right_idx < len(volumes) else 0

                if left_vol >= right_vol and left_idx >= 0:
                    accumulated_volume += left_vol
                    left_idx -= 1
                elif right_idx < len(volumes):
                    accumulated_volume += right_vol
                    right_idx += 1
                else:
                    break

            val_price = prices[max(0, left_idx + 1)]
            vah_price = prices[min(len(prices) - 1, right_idx - 1)]

            result = {
                'poc': round(poc_price, 2),
                'vah': round(vah_price, 2),
                'val': round(val_price, 2),
                'profile': dict(profile_items)
            }

            logger.info(f"Volume profile calculated - POC: {result['poc']}, VAH: {result['vah']}, VAL: {result['val']}")
            return result

        except Exception as e:
            logger.error(f"Error calculating volume profile: {e}")
            return {'poc': None, 'vah': None, 'val': None, 'profile': {}}

    def calculate_vah_for_stocks(self, symbols: List[str]) -> Dict[str, float]:
        """
        Calculate VAH for multiple stocks

        Args:
            symbols: List of stock symbols

        Returns:
            Dict mapping symbol to VAH price
        """
        vah_dict = {}

        # Get previous trading day
        prev_day = self.get_previous_trading_day()
        logger.info(f"Calculating VAH using data from previous trading day: {prev_day}")

        for symbol in symbols:
            try:
                # Fetch intraday data
                ohlcv_df = self.fetch_intraday_data(symbol, prev_day)

                if ohlcv_df is None or ohlcv_df.empty:
                    logger.warning(f"Skipping {symbol} - no intraday data available")
                    continue

                # Calculate volume profile
                profile_result = self.calculate_volume_profile(ohlcv_df)

                if profile_result['vah'] is not None:
                    vah_dict[symbol] = profile_result['vah']
                    logger.info(f"{symbol}: VAH = ₹{profile_result['vah']:.2f}")
                else:
                    logger.warning(f"Could not calculate VAH for {symbol}")

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")

        logger.info(f"VAH calculated for {len(vah_dict)} out of {len(symbols)} stocks")
        return vah_dict


# Global instance
volume_profile_calculator = VolumeProfileCalculator()
