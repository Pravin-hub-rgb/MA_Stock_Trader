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

    def analyze_reversal_setup(self, symbol: str, scan_date: date) -> Optional[Dict]:
        """Analyze stock for reversal setup"""
        try:
            # Get historical data
            end_date = scan_date.strftime('%Y-%m-%d')
            start_date = (scan_date - timedelta(days=30)).strftime('%Y-%m-%d')

            data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)

            if data.empty:
                return None

            # Calculate technical indicators
            data = data_fetcher.calculate_technical_indicators(data)

            # Get latest data
            latest = data.iloc[-1]

            # Check base filters
            if not self.filter_engine.check_base_filters(latest, 'reversal'):
                return None

            # Calculate score
            score = 0
            notes = []

            # Check 1: Extended decline
            decline_score, decline_notes = self._check_extended_decline(data)
            score += decline_score
            notes.extend(decline_notes)

            # Check 2: Volume confirmation
            if self.filter_engine.check_volume_confirmation(data, 'reversal'):
                score += 25
                notes.append("Volume confirmation present")
            else:
                notes.append("Volume confirmation missing")

            # Check 3: Oversold condition
            oversold_score, oversold_notes = self._check_oversold_condition(data)
            score += oversold_score
            notes.extend(oversold_notes)

            # Check 4: ADR requirement
            if latest['adr_percent'] >= self.reversal_params['min_adr'] * 100:
                score += 25
                notes.append(f"ADR {latest['adr_percent']:.1f}% meets requirement")
            else:
                notes.append(f"ADR {latest['adr_percent']:.1f}% too low")

            # Insert stock if not exists
            stock_id = db.get_stock_id(symbol)
            if stock_id is None:
                # Try to get name from symbol or use symbol itself
                name = symbol  # Use symbol as name for now
                stock_id = db.insert_stock(symbol, name=name)

            return {
                'stock_id': stock_id,
                'symbol': symbol,
                'score': score,
                'notes': '; '.join(notes),
                'decline_days': self._get_decline_days(data),
                'decline_percent': self._get_decline_percent(data),
                'volume_confirmation': self.filter_engine.check_volume_confirmation(data, 'reversal'),
                'oversold': self._check_oversold_condition(data)[0] > 0
            }

        except Exception as e:
            logger.error(f"Error analyzing reversal setup for {symbol}: {e}")
            return None

    def _check_extended_decline(self, data: pd.DataFrame) -> Tuple[int, List[str]]:
        """Check for extended decline (4-7 days)"""
        try:
            score = 0
            notes = []

            # Get recent data
            recent_data = data.tail(15)

            # Count consecutive down days
            down_days = 0
            for i in range(len(recent_data) - 1, 0, -1):
                if recent_data.iloc[i]['close'] < recent_data.iloc[i-1]['close']:
                    down_days += 1
                else:
                    break

            min_days, max_days = self.reversal_params['decline_days']
            min_decline = self.reversal_params['min_decline_percent']

            if min_days <= down_days <= max_days:
                # Check decline percentage
                start_price = recent_data.iloc[-down_days]['close']
                end_price = recent_data.iloc[-1]['close']
                decline_percent = (start_price - end_price) / start_price

                if decline_percent >= min_decline:
                    score = 50
                    notes.append(f"Extended decline: {down_days} days, {decline_percent*100:.1f}%")
                else:
                    score = 25
                    notes.append(f"Decline too small: {decline_percent*100:.1f}% < {min_decline*100:.1f}%")
            else:
                notes.append(f"Wrong decline duration: {down_days} days")

            return score, notes

        except Exception as e:
            logger.error(f"Error checking extended decline: {e}")
            return 0, ["Error checking decline"]

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
        """Get number of consecutive decline days"""
        try:
            recent_data = data.tail(15)
            down_days = 0
            for i in range(len(recent_data) - 1, 0, -1):
                if recent_data.iloc[i]['close'] < recent_data.iloc[i-1]['close']:
                    down_days += 1
                else:
                    break
            return down_days
        except:
            return 0

    def _get_decline_percent(self, data: pd.DataFrame) -> float:
        """Get percentage decline over recent period"""
        try:
            recent_data = data.tail(15)
            down_days = self._get_decline_days(data)
            if down_days < 2:
                return 0

            start_price = recent_data.iloc[-down_days]['close']
            end_price = recent_data.iloc[-1]['close']
            return (start_price - end_price) / start_price
        except:
            return 0
