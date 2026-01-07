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

            # All checks passed - return candidate
            return {
                'symbol': symbol,
                'close': latest['close'],
                'decline_days': self._get_decline_days(data),
                'decline_percent': self._get_decline_percent(data),
                'adr_percent': latest['adr_percent']
            }

        except Exception as e:
            logger.error(f"Error analyzing reversal setup for {symbol}: {e}")
            return None

    def _check_extended_decline(self, data: pd.DataFrame, symbol: str = "") -> bool:
        """Check for extended decline (3-8 consecutive red days with >=10% drop)"""
        try:
            # Get recent data
            recent_data = data.tail(15)

            # Count consecutive red candles (close < open)
            red_days = 0
            for i in range(len(recent_data) - 1, -1, -1):
                if recent_data.iloc[i]['close'] < recent_data.iloc[i]['open']:
                    red_days += 1
                else:
                    break

            min_days, max_days = self.reversal_params['decline_days']
            min_decline = self.reversal_params['min_decline_percent']

            if min_days <= red_days <= max_days:
                # Check decline percentage: first open to last close over the red candle period
                start_price = recent_data.iloc[-red_days]['open']
                end_price = recent_data.iloc[-1]['close']
                decline_percent = (start_price - end_price) / start_price

                if decline_percent >= min_decline:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking extended decline: {e}")
            return False

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
