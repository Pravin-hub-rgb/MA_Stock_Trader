"""
Market Scanner for MA Stock Trader
Implements continuation and reversal scan algorithms
"""

import logging
from datetime import date, datetime, time, timedelta
from typing import List, Dict, Optional
import pandas as pd

from src.utils.database import db
from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager
from .filters import FilterEngine
from .continuation_analyzer import ContinuationAnalyzer
from .reversal_analyzer import ReversalAnalyzer

logger = logging.getLogger(__name__)


class Scanner:
    """Main scanner class for continuation and reversal detection"""

    def __init__(self):
        # Common scan parameters
        self.common_params = {
            'min_volume_days': 2,            # At least 2 days with 1M+ volume
            'volume_threshold': 1000000,     # 1M shares
            'min_movement_days': 2,          # At least 2 days with 5%+ green candles
            'movement_threshold_pct': 0.05,  # 5% price movement threshold
            'lookback_days': 30,             # 30-day lookback period for volume and movement
            'min_adr': 0.03,                 # 3% ADR (same for both scans)
            'price_min': 100,                # ₹100 minimum
            'price_max': 2000,               # ₹2000 maximum
        }

        # Continuation scan parameters
        self.continuation_params = {
            **self.common_params,            # Include common parameters
            'near_ma_threshold': 0.05,       # 5% near MA threshold
            'max_body_percentage': 0.05,     # 5% max body size
        }

        # Reversal scan parameters
        self.reversal_params = {
            **self.common_params,            # Include common parameters
            'decline_days': (3, 8),          # 3-8 days decline
            'min_decline_percent': 0.10,     # 10% minimum decline
        }

        # Initialize analyzer modules
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.continuation_analyzer = ContinuationAnalyzer(self.filter_engine)
        self.reversal_analyzer = ReversalAnalyzer(self.filter_engine, self.reversal_params)

    def update_price_filters(self, min_price: int, max_price: int):
        """Update price filter parameters"""
        self.common_params['price_min'] = min_price
        self.common_params['price_max'] = max_price

        # Update dependent parameter sets
        self.continuation_params.update(self.common_params)
        self.reversal_params.update(self.common_params)

        # Re-initialize filter engine with updated parameters
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.continuation_analyzer = ContinuationAnalyzer(self.filter_engine)
        self.reversal_analyzer = ReversalAnalyzer(self.filter_engine, self.reversal_params)

        logger.info(f"Updated price filters: ₹{min_price} - ₹{max_price}")

    def update_near_ma_threshold(self, threshold_percent: int):
        """Update near MA threshold parameter"""
        self.continuation_params['near_ma_threshold'] = threshold_percent / 100.0  # Convert % to decimal

        # Re-initialize filter engine with updated parameters
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.continuation_analyzer = ContinuationAnalyzer(self.filter_engine)

        logger.info(f"Updated near MA threshold: {threshold_percent}%")

    def update_max_body_percentage(self, threshold_percent: int):
        """Update max body percentage parameter"""
        self.continuation_params['max_body_percentage'] = threshold_percent / 100.0  # Convert % to decimal

        # Re-initialize filter engine with updated parameters
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.continuation_analyzer = ContinuationAnalyzer(self.filter_engine)

        logger.info(f"Updated max body percentage: {threshold_percent}%")

    def update_min_decline_percent(self, decline_percent: int):
        """Update minimum decline percentage parameter for reversals"""
        self.reversal_params['min_decline_percent'] = decline_percent / 100.0  # Convert % to decimal

        # Re-initialize filter engine with updated parameters
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.reversal_analyzer = ReversalAnalyzer(self.filter_engine, self.reversal_params)

        logger.info(f"Updated min decline percent: {decline_percent}%")
    
    def _ensure_data_cached(self, nse_stocks: List[Dict], scan_date: date, progress_callback=None):
        """Filter stocks to only those with cached data for scan date"""
        logger.info("Filtering stocks to those with cached data...")

        stocks_with_data = []
        total_checked = len(nse_stocks)

        # Check which NSE stocks have cached data
        for i, stock in enumerate(nse_stocks, 1):
            symbol = stock['symbol']
            try:
                # Load cached data directly (NO API calls)
                cached_data = cache_manager.load_cached_data(symbol)

                if cached_data is not None and not cached_data.empty and scan_date in cached_data.index:
                    stocks_with_data.append(stock)
                # else: Skip stocks without data

                # Progress update
                if progress_callback and (i % 100 == 0 or i == total_checked):
                    progress_percent = int((i / total_checked) * 50)
                    progress_callback(progress_percent, f"Checked {i}/{total_checked} stocks")

            except Exception as e:
                logger.warning(f"Error checking cache for {symbol}: {e}")
                continue

        available_stocks = len(stocks_with_data)
        logger.info(f"✅ Found {available_stocks} stocks with cached data for {scan_date} (from {total_checked} NSE stocks)")

        if available_stocks == 0:
            logger.error("CRITICAL: No stocks have cached data!")
            if progress_callback:
                progress_callback(50, "ERROR: No stocks have cached data")
            return []
        else:
            if progress_callback:
                progress_callback(50, f"Found {available_stocks} stocks with cached data")
            return stocks_with_data

    def _get_all_cached_stocks_with_data(self, scan_date: date, progress_callback=None):
        """Get ALL cached stocks that have data for scan_date (not just NSE API stocks)"""
        logger.info("Getting all cached stocks with data...")

        from pathlib import Path
        cache_dir = Path('data/cache')
        cached_files = list(cache_dir.glob('*.pkl'))

        stocks_with_data = []
        total_cached = len(cached_files)

        logger.info(f"Checking {total_cached} cached stock files...")

        # Check each cached stock
        for i, cache_file in enumerate(cached_files, 1):
            symbol = cache_file.stem

            # Skip non-stock cache files (like market breadth cache)
            if '_' in symbol or not symbol.isupper():
                continue

            try:
                # Load cached data directly (NO API calls)
                cached_data = cache_manager.load_cached_data(symbol)

                if cached_data is not None and not cached_data.empty:
                    # Check if scan_date exists in data (more robust check)
                    try:
                        target_timestamp = pd.Timestamp(scan_date)
                        has_data = target_timestamp in cached_data.index
                        # Alternative check: look for date in the index
                        if not has_data:
                            # Check if any date in index matches scan_date
                            for idx_date in cached_data.index:
                                # idx_date is already a date-like object from DatetimeIndex
                                if hasattr(idx_date, 'date'):
                                    # It's a Timestamp, convert to date
                                    idx_date_only = idx_date.date()
                                else:
                                    # It's already a date
                                    idx_date_only = idx_date
                                if idx_date_only == scan_date:
                                    has_data = True
                                    break

                        if has_data:
                            # Create stock dict like NSE API format
                            stocks_with_data.append({'symbol': symbol, 'name': symbol, 'series': 'EQ'})
                    except Exception as e:
                        logger.warning(f"Error checking date for {symbol}: {e}")
                        continue
                # else: Skip stocks without data

                # Progress update
                if progress_callback and (i % 200 == 0 or i == total_cached):
                    progress_percent = int((i / total_cached) * 50)
                    progress_callback(progress_percent, f"Verified cache for {i}/{total_cached} stocks")

            except Exception as e:
                logger.warning(f"Error checking cache for {symbol}: {e}")
                continue

        available_stocks = len(stocks_with_data)
        logger.info(f"Found {available_stocks} cached stocks with data for {scan_date}")

        if available_stocks == 0:
            logger.error("CRITICAL: No cached stocks have data!")
            if progress_callback:
                progress_callback(50, "ERROR: No cached stocks have data")
            return []
        else:
            if progress_callback:
                progress_callback(50, f"Found {available_stocks} cached stocks with data")
            return stocks_with_data

    def run_continuation_scan(self, scan_date: date = None, progress_callback=None, min_price: int = None, max_price: int = None) -> List[Dict]:
        """
        Run continuation scan using the most recent available cached data
        Returns list of potential continuation candidates
        """
        if scan_date is None:
            # Auto-detect the latest available date with cached data
            scan_date = self._find_latest_available_scan_date()
            if scan_date is None:
                logger.error("No cached data available for scanning")
                if progress_callback:
                    progress_callback(0, "ERROR: No cached data available")
                return []

        logger.info(f"Running continuation scan for {scan_date} (latest available data)")
        if progress_callback:
            progress_callback(0, f"SCAN_DATE:{scan_date}")
            progress_callback(0, f"Loading historical data for {scan_date}")

        try:
            # Get ALL cached stocks (not just NSE API stocks)
            filtered_stocks = self._get_all_cached_stocks_with_data(scan_date, progress_callback)

            if not filtered_stocks:  # No stocks have data
                logger.warning("No stocks have cached data - cannot run scan")
                return []

            candidates = []
            logger.info(f"Scanning {len(filtered_stocks)} stocks with cached data")

            # Scan each stock (with progress updates)
            total_stocks = len(filtered_stocks)
            for i, stock in enumerate(filtered_stocks, 1):
                try:
                    symbol = stock['symbol']

                    # Get cached data (should be available after pre-caching)
                    # Load ALL available historical data for proper MA calculation throughout 80-day window
                    data = data_fetcher.get_data_for_date_range(
                        symbol,
                        None,  # From earliest available
                        scan_date
                    )


                    # Check if scan_date exists in data (robust check)
                    target_timestamp = pd.Timestamp(scan_date)
                    has_scan_date = target_timestamp in data.index
                    # Alternative check: look for date in the index
                    if not has_scan_date:
                        # Check if any date in index matches scan_date
                        for idx_date in data.index:
                            if idx_date.date() == scan_date:
                                has_scan_date = True
                                break

                    if data.empty or not has_scan_date:
                        logger.warning(f"No cached data for {symbol}, skipping")
                        continue

                    # Calculate technical indicators
                    data = data_fetcher.calculate_technical_indicators(data)
                    latest = data.iloc[-1]

                    # Apply base filters
                    if not self.filter_engine.check_base_filters(latest, 'continuation'):
                        continue

                    # Check Liquidity (combined volume + price movement)
                    if not self.filter_engine.check_liquidity_confirmation(data, 'continuation'):
                        continue

                    # Check ADR
                    if not self.filter_engine.check_adr_threshold(latest):
                        continue

                    # Now run pattern analysis
                    result = self.continuation_analyzer.analyze_continuation_setup(symbol, scan_date, data)

                    if result:
                        candidates.append(result)

                    # Progress update during scanning
                    if progress_callback and (i % 20 == 0 or i == total_stocks):
                        progress_percent = int(50 + (i / total_stocks) * 50)  # 50-100% for scanning
                        progress_callback(progress_percent, f"Scanned {i}/{total_stocks} stocks, found {len(candidates)} candidates")

                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue

            # Sort alphabetically by symbol
            candidates.sort(key=lambda x: x['symbol'])

            logger.info(f"Found {len(candidates)} continuation candidates")
            return candidates

        except Exception as e:
            logger.error(f"Error in continuation scan: {e}")
            return []
    
    def run_reversal_scan(self, scan_date: date = None, progress_callback=None) -> List[Dict]:
        """
        Run reversal scan using the most recent available cached data
        Returns list of potential reversal candidates
        """
        if scan_date is None:
            # Auto-detect the latest available date with cached data
            scan_date = self._find_latest_available_scan_date()
            if scan_date is None:
                logger.error("No cached data available for scanning")
                if progress_callback:
                    progress_callback(0, "ERROR: No cached data available")
                return []

        logger.info(f"Running reversal scan for {scan_date} (latest available data)")
        if progress_callback:
            progress_callback(0, f"SCAN_DATE:{scan_date}")
            progress_callback(0, f"Scanning data for {scan_date}")

        try:
            # Get ALL cached stocks (not just NSE API stocks)
            filtered_stocks = self._get_all_cached_stocks_with_data(scan_date, progress_callback)

            if not filtered_stocks:  # No stocks have data
                logger.warning("No stocks have cached data - cannot run scan")
                return []

            candidates = []
            logger.info(f"Scanning {len(filtered_stocks)} stocks with cached data")

            # Scan each stock (with progress updates)
            total_stocks = len(filtered_stocks)
            for i, stock in enumerate(filtered_stocks, 1):
                try:
                    symbol = stock['symbol']

                    # Get cached data (should be available after pre-caching)
                    # Get last 50 days for proper MA calculation in trend classification
                    data = data_fetcher.get_data_for_date_range(
                        symbol,
                        scan_date - timedelta(days=50), scan_date
                    )

                    # Check if scan_date exists in data (robust check)
                    target_timestamp = pd.Timestamp(scan_date)
                    has_scan_date = target_timestamp in data.index
                    # Alternative check: look for date in the index
                    if not has_scan_date:
                        # Check if any date in index matches scan_date
                        for idx_date in data.index:
                            if idx_date.date() == scan_date:
                                has_scan_date = True
                                break

                    if data.empty or not has_scan_date:
                        logger.warning(f"No cached data for {symbol}, skipping")
                        continue

                    # Calculate technical indicators
                    data = data_fetcher.calculate_technical_indicators(data)
                    latest = data.iloc[-1]

                    # Apply base filters
                    base_pass = self.filter_engine.check_base_filters(latest, 'reversal')
                    if symbol == 'ITC':
                        logger.info(f"ITC DEBUG: base filters pass: {base_pass}")
                        if not base_pass:
                            logger.info(f"ITC DEBUG: price={latest['close']}, adr={latest.get('adr_percent', 0)}")
                    if not base_pass:
                        continue

                    # Check Liquidity (combined volume + price movement)
                    liquidity_pass = self.filter_engine.check_liquidity_confirmation(data, 'reversal')
                    if symbol == 'ITC':
                        logger.info(f"ITC DEBUG: liquidity check pass: {liquidity_pass}")
                    if not liquidity_pass:
                        continue

                    # Now run pattern analysis
                    result = self.reversal_analyzer.analyze_reversal_setup(symbol, scan_date, data)

                    if result:
                        candidates.append(result)

                    # Progress update during scanning
                    if progress_callback and (i % 20 == 0 or i == total_stocks):
                        progress_percent = int(50 + (i / total_stocks) * 50)  # 50-100% for scanning
                        progress_callback(progress_percent, f"Scanned {i}/{total_stocks} stocks, found {len(candidates)} candidates")

                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue

            # Sort alphabetically by symbol
            candidates.sort(key=lambda x: x['symbol'])

            logger.info(f"Found {len(candidates)} reversal candidates")
            return candidates

        except Exception as e:
            logger.error(f"Error in reversal scan: {e}")
            return []

    def _get_previous_trading_day(self, current_date: date) -> date:
        """Get the previous trading day, skipping weekends"""
        prev = current_date - timedelta(days=1)
        while prev.weekday() >= 5:  # Saturday=5, Sunday=6
            prev -= timedelta(days=1)
        return prev

    def _find_latest_available_scan_date(self) -> Optional[date]:
        """
        Find the most recent date that has cached data for stocks.
        Simply finds the latest cached date without weekend checks (handles Budget Day exceptions).
        """
        from pathlib import Path

        cache_dir = Path('data/cache')
        cached_files = list(cache_dir.glob('*.pkl'))

        if not cached_files:
            logger.error("No cached stock files found")
            return None

        # Filter to only stock cache files
        stock_cache_files = [f for f in cached_files if '_' not in f.stem and f.stem.isupper()]
        
        if not stock_cache_files:
            logger.error("No stock cache files found")
            return None

        # Find the most recent date across all cached files
        latest_date = None
        
        for cache_file in stock_cache_files:
            symbol = cache_file.stem
            try:
                df = cache_manager.load_cached_data(symbol)
                if df is not None and not df.empty:
                    # Get the latest date in this stock's data
                    if isinstance(df.index, pd.DatetimeIndex):
                        file_latest_date = df.index[-1].date() if hasattr(df.index[-1], 'date') else df.index[-1]
                    else:
                        # Handle non-DatetimeIndex
                        file_latest_date = df.index[-1]
                    
                    # Convert to date if it's a timestamp
                    if hasattr(file_latest_date, 'date'):
                        file_latest_date = file_latest_date.date()
                    
                    # Update global latest date
                    if latest_date is None or file_latest_date > latest_date:
                        latest_date = file_latest_date
                        
            except Exception as e:
                logger.warning(f"Error checking cache for {symbol}: {e}")
                continue

        if latest_date:
            logger.info(f"Found latest available scan date: {latest_date}")
            return latest_date
        else:
            logger.error("No cached data found with valid dates")
            return None

    def _get_stock_price(self, symbol: str) -> float:
        """Get current stock price for filtering"""
        try:
            data = data_fetcher.get_latest_data(symbol, days=1)
            return data.get('close', 0)
        except:
            return 0



# Global scanner instance
scanner = Scanner()
