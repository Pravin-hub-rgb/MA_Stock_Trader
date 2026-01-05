"""
Continuation setup analyzer for MA Stock Trader
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict
import pandas as pd

from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager
from .filters import FilterEngine

logger = logging.getLogger(__name__)


class ContinuationAnalyzer:
    """Handles continuation setup analysis"""

    def __init__(self, filter_engine: FilterEngine):
        self.filter_engine = filter_engine

    def analyze_continuation_setup(self, symbol: str, scan_date: date) -> Optional[Dict]:
        """Analyze stock for continuation setup using simplified base filters"""
        try:
            # Get historical data from cache or fetch if needed
            end_date = scan_date.strftime('%Y-%m-%d')
            start_date = (scan_date - timedelta(days=365)).strftime('%Y-%m-%d')  # Get 1 year of data

            # Check cache first
            cached_data = data_fetcher.get_data_for_date_range(symbol,
                datetime.strptime(start_date, '%Y-%m-%d').date(),
                datetime.strptime(end_date, '%Y-%m-%d').date())

            # Check if we have data for the scan_date
            scan_date_in_cache = not cached_data.empty and scan_date in cached_data['date'].values

            if cached_data.empty or not scan_date_in_cache:
                # For current date, try real-time data first
                current_date = date.today()
                if scan_date == current_date:
                    logger.info(f"Fetching real-time data for {symbol} on current date {scan_date}")
                    realtime_data = data_fetcher.fetch_realtime_data(symbol)
                    if realtime_data and realtime_data.get('current_price', 0) > 0:
                        # Create a data row for today from real-time data
                        today_data = pd.DataFrame([{
                            'date': scan_date,
                            'open': realtime_data['open_price'],
                            'high': realtime_data['high_price'],
                            'low': realtime_data['low_price'],
                            'close': realtime_data['current_price'],
                            'volume': realtime_data['volume'],
                            'adj_close': realtime_data['current_price'],
                            'vwap': (realtime_data['high_price'] + realtime_data['low_price'] + realtime_data['current_price']) / 3
                        }])

                        # Combine with existing cached data
                        if not cached_data.empty:
                            data = pd.concat([cached_data, today_data]).drop_duplicates(subset=['date']).sort_values('date')
                        else:
                            # If no cached data, we need historical data too
                            logger.info(f"No cached data for {symbol}, fetching historical data first")
                            hist_data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
                            if not hist_data.empty:
                                data = pd.concat([hist_data, today_data]).drop_duplicates(subset=['date']).sort_values('date')
                            else:
                                data = today_data

                        # Update cache
                        cache_manager.update_cache(symbol, data)
                        logger.info(f"Updated cache for {symbol} with real-time data: ₹{realtime_data['current_price']:.2f}")
                    else:
                        # Fallback to historical data fetch
                        logger.info(f"Real-time data not available for {symbol}, fetching historical data")
                        data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
                        if data.empty:
                            logger.warning(f"No data available for {symbol}")
                            return None
                        cache_manager.update_cache(symbol, data)
                else:
                    # For past dates, fetch historical data
                    logger.info(f"Missing data for {symbol} on {scan_date}, fetching historical data")
                    data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
                    if data.empty:
                        logger.warning(f"No data available for {symbol}")
                        return None
                    cache_manager.update_cache(symbol, data)
                    logger.info(f"Updated cache for {symbol} with {len(data)} days of data")
            else:
                data = cached_data

            # Calculate technical indicators
            data = data_fetcher.calculate_technical_indicators(data)

            # Get latest data
            latest = data.iloc[-1]

            # Check base filters - ALL must pass
            if not self.filter_engine.check_base_filters(latest, 'continuation'):
                logger.info(f"{symbol}: Failed base filters")
                return None

            # Check Rising MA using simple comparison (Current MA > 7 days ago MA)
            if not self.filter_engine.check_rising_ma(data, latest):
                return None  # MA not rising

            # Check Volume: At least 1 day with 1M+ volume in last month (20 days)
            if not self.filter_engine.check_volume_confirmation(data, 'continuation'):
                return None  # No high volume days

            # Check ADR: > 3%
            if not self.filter_engine.check_adr_threshold(latest):
                return None  # ADR too low

            # All base filters passed - return qualified stock
            return {
                'symbol': symbol,
                'price': latest['close'],
                'adr_percent': latest['adr_percent']
            }

        except Exception as e:
            logger.error(f"Error analyzing continuation setup for {symbol}: {e}")
            return None
