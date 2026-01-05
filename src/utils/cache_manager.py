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
            return data['date'].iloc[-1]
        return None
    
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
            # Remove duplicates and sort by date
            combined_data = combined_data.drop_duplicates(subset=['date']).sort_values('date')
        else:
            # No existing data, use new data
            combined_data = new_data
        
        # Save updated data
        self.save_cached_data(symbol, combined_data)
    
    def get_data_for_date_range(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Get data for specific date range from cache"""
        cached_data = self.load_cached_data(symbol)
        if cached_data is None or cached_data.empty:
            return pd.DataFrame()
        
        # Filter for date range
        mask = (cached_data['date'] >= start_date) & (cached_data['date'] <= end_date)
        return cached_data[mask].copy()

# Global cache manager instance
cache_manager = CacheManager()
