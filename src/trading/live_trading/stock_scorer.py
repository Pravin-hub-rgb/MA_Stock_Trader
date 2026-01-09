"""
Stock Scorer - Calculates quality scores for stock selection
Based on ADR, Price, and Early Volume parameters
"""

import sys
import os
import logging
from typing import Dict, Optional
import pandas as pd

import sys
import os
# Ensure we can import from the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.cache_manager import cache_manager
from src.utils.upstox_fetcher import upstox_fetcher

logger = logging.getLogger(__name__)


class StockScorer:
    """Calculates quality scores for stock selection"""

    def __init__(self):
        self.stock_metadata = {}  # Cache for pre-calculated values

    def preload_metadata(self, symbols: list, prev_closes: dict = None):
        """Pre-calculate ADR and price data at prep time"""
        logger.info(f"Preloading metadata for {len(symbols)} stocks")
        if prev_closes is None:
            prev_closes = {}

        for symbol in symbols:
            try:
                # Get ADR from cache (REQUIRED - no defaults)
                adr_data = cache_manager.load_cached_data(symbol)
                if adr_data.empty or 'adr_percent' not in adr_data.columns:
                    raise ValueError(f"No ADR data available for {symbol}")

                latest_adr = adr_data['adr_percent'].iloc[-1]
                if pd.isna(latest_adr):
                    raise ValueError(f"ADR data is NaN for {symbol}")

                current_adr = float(latest_adr)
                logger.debug(f"[{symbol}] ADR loaded: {current_adr:.2f}%")

                # Get current price (use fallback in test mode)
                ltp_data = upstox_fetcher.get_ltp_data(symbol)
                if ltp_data and 'ltp' in ltp_data:
                    current_price = float(ltp_data['ltp'])
                    logger.debug(f"[{symbol}] Price loaded: ₹{current_price:.2f}")
                else:
                    # Fallback for test mode or when LTP unavailable
                    from config import TEST_MODE
                    if TEST_MODE:
                        # Use previous close as fallback for test mode
                        current_price = float(prev_closes.get(symbol, 500.0))
                        logger.debug(f"[{symbol}] Using fallback price (test mode): ₹{current_price:.2f}")
                    else:
                        raise ValueError(f"No LTP data available for {symbol}")

                # Get volume baseline (REQUIRED - no defaults)
                volume_baseline = self._get_volume_baseline(symbol)
                if volume_baseline <= 0:
                    raise ValueError(f"No volume baseline available for {symbol}")

                logger.debug(f"[{symbol}] Volume baseline: {volume_baseline:,.0f}")

                self.stock_metadata[symbol] = {
                    'adr_percent': current_adr,
                    'current_price': current_price,
                    'volume_baseline': volume_baseline
                }

                # Log all metadata loads
                logger.info(f"📊 {symbol}: ADR {current_adr:.1f}%, Price ₹{current_price:.0f}, Vol Baseline {volume_baseline:,.0f}")

            except Exception as e:
                logger.error(f"Failed to load metadata for {symbol}: {e}")
                # Don't add to metadata - stock will be skipped from scoring
                continue

    def _get_volume_baseline(self, symbol: str) -> float:
        """Get volume baseline for scoring"""
        try:
            cached_data = cache_manager.load_cached_data(symbol)
            if not cached_data.empty and len(cached_data) >= 10:
                # Use last 10 days average
                avg_volume = cached_data['volume'].tail(10).mean()
                return max(avg_volume, 500000)  # Minimum 5 lakh
            else:
                return 1000000  # Scanner minimum
        except:
            return 1000000  # Safe fallback

    def calculate_adr_score(self, adr_percent: float) -> int:
        """Calculate ADR score (0-10 points)"""
        if adr_percent >= 5.0:
            return 10  # Excellent volatility for 15% targets
        elif adr_percent >= 4.0:
            return 8   # Very good
        elif adr_percent >= 3.0:
            return 6   # Good
        elif adr_percent >= 2.5:
            return 4   # Average
        else:
            return 2   # Below average

    def calculate_price_score(self, current_price: float) -> int:
        """Calculate price score (0-10 points) - liquidity proxy"""
        if current_price >= 1000:
            return 10  # Large cap liquidity
        elif current_price >= 500:
            return 7   # Good liquidity
        elif current_price >= 200:
            return 5   # Medium liquidity
        else:
            return 3   # Lower liquidity

    def calculate_volume_score(self, early_volume: float, volume_baseline: float) -> int:
        """Calculate early volume score (0-10 points)"""
        if volume_baseline <= 0:
            return 5  # Neutral if no baseline

        ratio = early_volume / volume_baseline

        if ratio >= 0.25:     # 25% of daily volume in 5 min
            return 10
        elif ratio >= 0.20:   # 20%
            return 8
        elif ratio >= 0.15:   # 15%
            return 6
        elif ratio >= 0.10:   # 10%
            return 4
        else:                 # Below 10%
            return 2

    def calculate_total_score(self, symbol: str, early_volume: float = 0) -> Dict:
        """Calculate complete score for a stock"""
        if symbol not in self.stock_metadata:
            raise ValueError(f"No metadata available for {symbol} - cannot calculate score")

        metadata = self.stock_metadata[symbol]

        adr_score = self.calculate_adr_score(metadata['adr_percent'])
        price_score = self.calculate_price_score(metadata['current_price'])
        volume_score = self.calculate_volume_score(early_volume, metadata['volume_baseline'])

        total_score = adr_score + price_score + volume_score

        result = {
            'symbol': symbol,
            'adr_percent': metadata['adr_percent'],
            'current_price': metadata['current_price'],
            'volume_baseline': metadata['volume_baseline'],
            'early_volume': early_volume,
            'adr_score': adr_score,
            'price_score': price_score,
            'volume_score': volume_score,
            'total_score': total_score
        }

        return result

    def rank_stocks(self, stocks_data: list) -> list:
        """Rank stocks by total score (highest first)"""
        return sorted(stocks_data, key=lambda x: x['total_score'], reverse=True)

    def get_top_stocks(self, symbols: list, early_volumes: Dict[str, float], max_select: int = 2) -> list:
        """Get top N stocks by score"""
        stock_scores = []

        for symbol in symbols:
            early_volume = early_volumes.get(symbol, 0)
            score_data = self.calculate_total_score(symbol, early_volume)
            stock_scores.append(score_data)

        ranked = self.rank_stocks(stock_scores)
        return ranked[:max_select]

    def get_scoring_summary(self, symbols: list, early_volumes: Dict[str, float]) -> Dict:
        """Get detailed scoring summary for analysis"""
        all_scores = []

        for symbol in symbols:
            early_volume = early_volumes.get(symbol, 0)
            score_data = self.calculate_total_score(symbol, early_volume)
            all_scores.append(score_data)

        ranked = self.rank_stocks(all_scores)

        return {
            'all_scores': ranked,
            'top_selection': ranked[:2] if len(ranked) >= 2 else ranked,
            'scoring_breakdown': {
                'adr_weights': {'5%+': 10, '4%+': 8, '3%+': 6, '2.5%+': 4, '<2.5%': 2},
                'price_weights': {'1000+': 10, '500+': 7, '200+': 5, '<200': 3},
                'volume_weights': {'25%+': 10, '20%+': 8, '15%+': 6, '10%+': 4, '<10%': 2}
            }
        }


# Global instance
stock_scorer = StockScorer()
