"""
Stock Scorer - Quality scoring for stock selection
Based on ADR (volatility), Price range, and Volume metrics
"""

import os
import json
import logging
from typing import Dict, List, Any, Tuple
import pandas as pd
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class StockScorer:
    """Handles quality scoring of stocks for selection"""

    def __init__(self):
        self.cache_file = os.path.join('bhavcopy_cache', 'stock_scores.json')
        self.scores_cache = {}
        self.adr_cache = {}
        self._load_cache()

    def _load_cache(self):
        """Load cached scores if available"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scores_cache = data.get('scores', {})
                    self.adr_cache = data.get('adr', {})
                logger.info("Loaded stock scores from cache")
        except Exception as e:
            logger.warning(f"Could not load scores cache: {e}")

    def _save_cache(self):
        """Save scores to cache"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'scores': self.scores_cache,
                    'adr': self.adr_cache,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save scores cache: {e}")

    def calculate_adr(self, symbol: str) -> float:
        """Calculate Average Daily Range for a stock"""
        if symbol in self.adr_cache:
            return self.adr_cache[symbol]

        try:
            # Try to load from bhavcopy data with timeout protection
            bhavcopy_file = os.path.join('bhavcopy_cache', f'{symbol.lower()}_daily.csv')
            if os.path.exists(bhavcopy_file):
                # Check file size - skip suspiciously large files (>50MB)
                file_size = os.path.getsize(bhavcopy_file)
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    logger.warning(f"Skipping {symbol}: CSV file too large ({file_size} bytes)")
                    return 0.03

                # Use a timeout for CSV reading to prevent hanging
                import signal
                from contextlib import contextmanager

                @contextmanager
                def timeout_context(seconds):
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"CSV reading timed out after {seconds} seconds")

                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(seconds)
                    try:
                        yield
                    finally:
                        signal.alarm(0)

                try:
                    with timeout_context(10):  # 10 second timeout
                        df = pd.read_csv(bhavcopy_file, parse_dates=['date'], encoding='utf-8')
                        # Use last 14 trading days
                        recent = df.tail(14)
                        if len(recent) >= 5:
                            adr = ((recent['high'] - recent['low']) / recent['close']).mean()
                            self.adr_cache[symbol] = adr
                            return adr
                except TimeoutError:
                    logger.warning(f"Timeout reading CSV for {symbol}, using default ADR")
                    return 0.03
                except Exception as e:
                    logger.debug(f"Error reading CSV for {symbol}: {e}")
                    return 0.03

        except Exception as e:
            logger.debug(f"Could not calculate ADR for {symbol}: {e}")

        # Default ADR based on price range (rough estimate)
        return 0.03  # 3% default

    def score_stock(self, symbol: str, price: float, volume: float, early_volume: float = 0) -> Dict[str, Any]:
        """Score a stock based on multiple factors"""

        # ADR Score (volatility - higher is better, up to 5%)
        adr = self.calculate_adr(symbol)
        if adr >= 0.05:
            adr_score = 10  # Very volatile
        elif adr >= 0.03:
            adr_score = 8   # Good volatility
        elif adr >= 0.02:
            adr_score = 6   # Moderate
        elif adr >= 0.01:
            adr_score = 4   # Low volatility
        else:
            adr_score = 2   # Very low

        # Price Score (prefer 100-2000 range)
        if 100 <= price <= 2000:
            price_score = 10
        elif 50 <= price <= 3000:
            price_score = 8
        elif price < 50 or price > 5000:
            price_score = 4
        else:
            price_score = 6

        # Volume Score (based on early volume in first 5 min)
        if early_volume >= 100000:  # 1 lakh shares
            volume_score = 10
        elif early_volume >= 50000:
            volume_score = 8
        elif early_volume >= 25000:
            volume_score = 6
        elif early_volume >= 10000:
            volume_score = 4
        else:
            volume_score = 2

        # Total score
        total_score = adr_score + price_score + volume_score

        return {
            'symbol': symbol,
            'adr_score': adr_score,
            'price_score': price_score,
            'volume_score': volume_score,
            'total_score': total_score,
            'adr_pct': adr * 100,
            'price': price,
            'early_volume': early_volume
        }

    def get_top_stocks(self, symbols: List[str], early_volumes: Dict[str, float] = None,
                      max_count: int = 2) -> List[Dict[str, Any]]:
        """Get top scored stocks from the list"""

        if early_volumes is None:
            early_volumes = {}

        scored_stocks = []

        for symbol in symbols:
            try:
                # Get current price (assume we have it from upstox_fetcher)
                # For now, use a placeholder price - this would be passed in
                price = 500  # Placeholder - should be passed from caller

                early_volume = early_volumes.get(symbol, 0)
                score_data = self.score_stock(symbol, price, 0, early_volume)
                scored_stocks.append(score_data)

            except Exception as e:
                logger.warning(f"Could not score {symbol}: {e}")
                # Add with minimum score
                scored_stocks.append({
                    'symbol': symbol,
                    'adr_score': 1,
                    'price_score': 1,
                    'volume_score': 1,
                    'total_score': 3,
                    'adr_pct': 1.0,
                    'price': 0,
                    'early_volume': 0
                })

        # Sort by total score (descending)
        scored_stocks.sort(key=lambda x: x['total_score'], reverse=True)

        # Return top N
        return scored_stocks[:max_count]

    def preload_metadata(self, symbols: List[str], prev_closes: Dict[str, float]):
        """Preload metadata for faster scoring"""
        logger.info(f"Preloading metadata for {len(symbols)} stocks...")

        # Calculate ADR for all symbols
        for symbol in symbols:
            self.calculate_adr(symbol)

        # Save cache
        self._save_cache()

        logger.info("Stock metadata preloaded")

# Global instance
stock_scorer = StockScorer()
