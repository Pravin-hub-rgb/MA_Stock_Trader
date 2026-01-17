#!/usr/bin/env python3
"""
Cache Manager for MA Stock Trader
Handles data caching and incremental updates
"""

import os
import pickle
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

class CacheManager:
    """Manages data caching for stocks"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, symbol: str) -> str:
        """Get cache file path for symbol"""
        return os.path.join(self.cache_dir, f"{symbol}.pkl")
    
    def load_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load cached data for symbol"""
        cache_path = self.get_cache_path(symbol)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"Loaded cached data for {symbol}: {len(data)} days")
                return data
            except Exception as e:
                logger.error(f"Error loading cache for {symbol}: {e}")
                return None
        return None
    
    def save_cached_data(self, symbol: str, data: pd.DataFrame):
        """Save data to cache for symbol"""
        cache_path = self.get_cache_path(symbol)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Saved cache for {symbol}: {len(data)} days")
        except Exception as e:
            logger.error(f"Error saving cache for {symbol}: {e}")
    
    def get_last_update_date(self, symbol: str) -> Optional[date]:
        """Get last update date for symbol"""
        data = self.load_cached_data(symbol)
        if data is not None and not data.empty:
            # Date is the index in Upstox data format
            last_date = data.index[-1]
            if hasattr(last_date, 'date'):  # If it's a Timestamp
                return last_date.date()
            else:  # If it's already a date
                return last_date
        return None

    def get_latest_cache_date(self) -> Optional[date]:
        """Get the latest date across all cached stocks"""
        from pathlib import Path

        cache_dir = Path(self.cache_dir)
        if not cache_dir.exists():
            return None

        latest = None
        for pkl_file in cache_dir.glob('*.pkl'):
            symbol = pkl_file.stem
            last_date = self.get_last_update_date(symbol)
            if last_date and (latest is None or last_date > latest):
                latest = last_date

        return latest
    
    def needs_update(self, symbol: str, days_back: int = 3) -> bool:
        """Check if symbol needs update (no data for last N days)"""
        last_date = self.get_last_update_date(symbol)
        if last_date is None:
            return True
        
        today = date.today()
        days_diff = (today - last_date).days
        return days_diff >= days_back
    
    def update_cache(self, symbol: str, new_data: pd.DataFrame):
        """Update cache with new data"""
        # Load existing data
        existing_data = self.load_cached_data(symbol)

        if existing_data is not None and not existing_data.empty:
            # Combine existing and new data
            combined_data = pd.concat([existing_data, new_data])
            # Reset index to work with date column
            combined_data = combined_data.reset_index()
            # Remove duplicates and sort by date
            combined_data = combined_data.drop_duplicates(subset=['date']).sort_values('date')
            # Set date back as index
            combined_data = combined_data.set_index('date')
        else:
            # No existing data, use new data
            combined_data = new_data

        # Add update timestamp
        combined_data['last_updated'] = pd.Timestamp.now()

        # Save updated data
        self.save_cached_data(symbol, combined_data)
    
    def update_with_bhavcopy(self, symbol: str, bhavcopy_data: pd.DataFrame):
        """Update existing cache with latest bhavcopy data"""
        existing_data = self.load_cached_data(symbol)

        try:
            if existing_data is not None and not existing_data.empty:
                # Ensure both DataFrames have compatible date indexing
                if not isinstance(existing_data.index, pd.DatetimeIndex):
                    # Convert existing data to DatetimeIndex if needed
                    existing_data.index = pd.to_datetime(existing_data.index)

                if not isinstance(bhavcopy_data.index, pd.DatetimeIndex):
                    # Convert bhavcopy data to DatetimeIndex if needed
                    bhavcopy_data.index = pd.to_datetime(bhavcopy_data.index)

                # Combine existing with new data
                combined = pd.concat([existing_data, bhavcopy_data])

                # Remove duplicates based on date index (keep last/latest)
                combined = combined[~combined.index.duplicated(keep='last')]

                # Sort by date index
                combined = combined.sort_index()
            else:
                combined = bhavcopy_data

            # Ensure we have a proper DatetimeIndex
            if not isinstance(combined.index, pd.DatetimeIndex):
                combined.index = pd.to_datetime(combined.index)

            # Add technical indicators (recalculate for updated data)
            try:
                from src.utils.data_fetcher import data_fetcher
                combined = data_fetcher.calculate_technical_indicators(combined)
            except ImportError:
                # Skip technical indicators if data_fetcher not available
                pass

            # Save updated cache
            self.save_cached_data(symbol, combined)
            logger.info(f"Updated {symbol} cache with bhavcopy data: {len(combined)} total days")

        except Exception as e:
            logger.error(f"Error updating {symbol} cache with bhavcopy data: {e}")
            # Don't raise - allow partial success
            raise

    def get_data_for_date_range(self, symbol: str, start_date: Optional[date], end_date: date) -> pd.DataFrame:
        """Get data for specific date range from cache"""
        cached_data = self.load_cached_data(symbol)
        if cached_data is None or cached_data.empty:
            return pd.DataFrame()

        # Ensure index is DatetimeIndex for proper comparison
        if not isinstance(cached_data.index, pd.DatetimeIndex):
            cached_data.index = pd.to_datetime(cached_data.index)

        # Filter for date range
        if start_date is None:
            # Return all data up to end_date
            end_ts = pd.Timestamp(end_date)
            mask = cached_data.index <= end_ts
        else:
            # Filter between start_date and end_date
            start_ts = pd.Timestamp(start_date)
            end_ts = pd.Timestamp(end_date)
            mask = (cached_data.index >= start_ts) & (cached_data.index <= end_ts)

        return cached_data[mask].copy()

# Global cache manager instance
cache_manager = CacheManager()
