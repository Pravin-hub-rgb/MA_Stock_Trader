"""
Reversal setup analyzer for MA Stock Trader
"""

import logging
from datetime import date, timedelta
from typing import Optional, Dict, Tuple, List
import pandas as pd

from src.utils.database import db
from src.utils.data_fetcher import data_fetcher
from .filters import FilterEngine

logger = logging.getLogger(__name__)


class ReversalAnalyzer:
    """Handles reversal setup analysis"""

    def __init__(self, filter_engine: FilterEngine, reversal_params: Dict):
        self.filter_engine = filter_engine
        self.reversal_params = reversal_params

    def analyze_reversal_setup(self, symbol: str, scan_date: date, data: pd.DataFrame) -> Optional[Dict]:
        """Analyze stock for reversal setup (extended decline pattern, assumes data is pre-fetched)"""
        try:
            # Data is already provided and filtered
            latest = data.iloc[-1]

            # Check extended decline pattern
            if not self._check_extended_decline(data, symbol):
                return None

            # Find the best decline period
            best_period = self._find_best_decline_period(data)
            if not best_period:
                return None

            # Classify trend context
            trend_context = self._classify_trend_context(data, best_period['period'])

            # All checks passed - return candidate
            return {
                'symbol': symbol,
                'close': latest['close'],
                'period': best_period['period'],
                'red_days': best_period['red_days'],
                'green_days': best_period['green_days'],
                'decline_percent': best_period['decline_percent'],
                'trend_context': trend_context,
                'liquidity_verified': True,
                'adr_percent': latest['adr_percent']
            }

        except Exception as e:
            logger.error(f"Error analyzing reversal setup for {symbol}: {e}")
            return None
    def _find_best_decline_period(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Find the best decline period that meets all criteria
        Returns: Dictionary with period details or None if not qualified
        """
        best_setup = None
        max_decline = 0

        for period in [3, 4, 5, 6, 7, 8]:
            if len(data) < period:
                continue

            period_data = data.tail(period)

            # Count red and green days
            red_days = sum(1 for _, row in period_data.iterrows() if row['close'] < row['open'])
            green_days = period - red_days

            # Check pattern logic
            if not self._check_pattern_logic(red_days, green_days, period):
                continue

            # Calculate decline percentage
            start_price = period_data.iloc[0]['open']
            end_price = period_data.iloc[-1]['close']
            decline_percent = (start_price - end_price) / start_price

            if decline_percent >= self.reversal_params['min_decline_percent']:  # Use configurable minimum
                # Check liquidity
                if self._check_liquidity(period_data):
                    if decline_percent > max_decline:
                        max_decline = decline_percent
                        best_setup = {
                            'period': period,
                            'red_days': red_days,
                            'green_days': green_days,
                            'decline_percent': decline_percent
                        }

        return best_setup

    def _check_extended_decline(self, data: pd.DataFrame, symbol: str = "") -> bool:
        """Check for extended decline with correct pattern logic (3-8 days with >=13% drop)"""
        try:
            # Check periods 3-8 days
            for period in [3, 4, 5, 6, 7, 8]:
                if len(data) < period:
                    continue

                period_data = data.tail(period)

                # Count red and green days
                red_days = sum(1 for _, row in period_data.iterrows() if row['close'] < row['open'])
                green_days = period - red_days

                # Apply period-specific pattern logic
                if self._check_pattern_logic(red_days, green_days, period):
                    # Calculate 13% minimum decline
                    start_price = period_data.iloc[0]['open']
                    end_price = period_data.iloc[-1]['close']
                    decline_percent = (start_price - end_price) / start_price

                    if decline_percent >= self.reversal_params['min_decline_percent']:  # Use configurable minimum
                        # Check liquidity (1M+ volume on any day)
                        if self._check_liquidity(period_data):
                            return True

            return False

        except Exception as e:
            logger.error(f"Error checking extended decline: {e}")
            return False
    def _check_pattern_logic(self, red_days: int, green_days: int, period: int) -> bool:
        """
        Check if red/green pattern meets requirements for given period
        """
        if period == 3:
            return red_days == 3 and green_days == 0
        elif period in [4, 5]:
            return red_days > green_days
        elif period in [6, 7, 8]:
            return red_days + 1 > green_days
        return False

    def _check_liquidity(self, data: pd.DataFrame) -> bool:
        """Check if stock has 1M+ volume on any day in the period"""
        return (data['volume'] >= 1000000).any()

    def _classify_trend_context(self, data: pd.DataFrame, period: int) -> str:
        """
        Classify trend context for live trading
        Compare MA_20 at oldest decline day vs 5 days earlier
        Uses similar approach as continuation analyzer - simple and clean
        """
        # Get oldest day of decline period
        oldest_day_index = len(data) - period
        oldest_day_data = data.iloc[oldest_day_index]

        # Calculate MA_20 at oldest day
        ma_at_oldest = data['close'].rolling(20).mean().iloc[oldest_day_index]

        # Calculate MA_20 5 days before oldest day
        ma_5_days_earlier = data['close'].rolling(20).mean().iloc[oldest_day_index - 5]

        # Simple comparison - with proper data loading, we shouldn't get NaN
        if pd.isna(ma_at_oldest) or pd.isna(ma_5_days_earlier):
            # If we still get NaN, it means data loading issue - use conservative default
            return 'downtrend'

        return 'uptrend' if ma_at_oldest > ma_5_days_earlier else 'downtrend'

    def _check_oversold_condition(self, data: pd.DataFrame) -> Tuple[int, List[str]]:
        """Check for oversold conditions"""
        try:
            score = 0
            notes = []

            latest = data.iloc[-1]

            # Check distance from 20-day low
            distance_from_low = latest['distance_from_low']

            if distance_from_low <= 0.05:  # Within 5% of 20-day low
                score = 25
                notes.append("Near 20-day low (oversold)")
            elif distance_from_low <= 0.10:  # Within 10% of 20-day low
                score = 15
                notes.append("Near 20-day low")
            else:
                notes.append("Not oversold enough")

            return score, notes

        except Exception as e:
            logger.error(f"Error checking oversold condition: {e}")
            return 0, ["Error checking oversold"]

    def _get_decline_days(self, data: pd.DataFrame) -> int:
        """Get number of consecutive red candles"""
        try:
            recent_data = data.tail(15)
            red_days = 0
            for i in range(len(recent_data) - 1, -1, -1):
                if recent_data.iloc[i]['close'] < recent_data.iloc[i]['open']:
                    red_days += 1
                else:
                    break
            return red_days
        except:
            return 0

    def _get_decline_percent(self, data: pd.DataFrame) -> float:
        """Get percentage decline over recent period (first open to last close)"""
        try:
            recent_data = data.tail(15)
            down_days = self._get_decline_days(data)
            if down_days < 2:
                return 0

            start_price = recent_data.iloc[-down_days]['open']
            end_price = recent_data.iloc[-1]['close']
            return (start_price - end_price) / start_price
        except:
            return 0
