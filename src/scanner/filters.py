"""
Common filter logic for MA Stock Trader scanner
"""

import logging
from typing import Dict, Tuple, List
import pandas as pd

logger = logging.getLogger(__name__)


class FilterEngine:
    """Handles common filtering logic for stock scans"""

    def __init__(self, continuation_params: Dict, reversal_params: Dict):
        self.continuation_params = continuation_params
        self.reversal_params = reversal_params

    def check_base_filters(self, latest: pd.Series, scan_type: str) -> bool:
        """Check base filters (price, volume, ADR)"""
        try:
            params = self.continuation_params if scan_type == 'continuation' else self.reversal_params

            # Price range check
            close_price = float(latest['close'])
            if not (params['price_min'] <= close_price <= params['price_max']):
                logger.info(f"Price filter failed: {close_price} not in range {params['price_min']}-{params['price_max']}")
                return False

            # ADR check
            adr_percent = float(latest['adr_percent'])
            if adr_percent < params['min_adr'] * 100:
                logger.info(f"ADR filter failed: {adr_percent} < {params['min_adr'] * 100}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking base filters: {e}")
            return False

    def check_volume_confirmation(self, data: pd.DataFrame, scan_type: str) -> bool:
        """Check volume confirmation requirements"""
        try:
            # Check if there's at least 1 day with 1M+ volume in last month
            recent_data = data.tail(20)  # Last month

            params = self.continuation_params if scan_type == 'continuation' else self.reversal_params
            volume_threshold = params['volume_threshold']
            min_volume_days = params['min_volume_days']

            high_volume_days = (recent_data['volume'] >= volume_threshold).sum()
            return high_volume_days >= min_volume_days

        except Exception as e:
            logger.error(f"Error checking volume confirmation: {e}")
            return False

    def check_rising_ma(self, data: pd.DataFrame, latest: pd.Series) -> bool:
        """Check if 20-day MA is rising (current > max of previous 5 days)"""
        try:
            if len(data) < 25:  # Need 20 + 5 buffer
                logger.info(f"Not enough data for MA comparison (need 25 days, got {len(data)})")
                return False

            current_ma = latest['ma_20']
            ma_prev_max = data.iloc[-6:-1]['ma_20'].max()  # Max of prev 5 days (excluding current)

            if current_ma <= ma_prev_max:
                logger.info(f"MA not rising (Current: {current_ma:.2f}, prev 5 max: {ma_prev_max:.2f})")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking rising MA: {e}")
            return False

    def check_adr_threshold(self, latest: pd.Series) -> bool:
        """Check ADR is above 3% threshold"""
        try:
            adr_percent = float(latest['adr_percent'])
            if adr_percent < 3.0:
                logger.info(f"ADR too low ({adr_percent:.2f}%)")
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking ADR threshold: {e}")
            return False
