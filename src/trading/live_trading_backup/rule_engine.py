"""
Rule Engine - Validates trading rules and conditions
"""

import sys
import os
import logging
from typing import List, Dict, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import *
from continuation_stock_monitor import StockState

logger = logging.getLogger(__name__)


class RuleEngine:
    """Engine for evaluating trading rules"""

    @staticmethod
    def validate_gap_up(open_price: float, previous_close: float) -> Dict[str, any]:
        """Validate gap up conditions"""
        gap_pct = (open_price - previous_close) / previous_close

        result = {
            'valid': False,
            'gap_pct': gap_pct,
            'reason': None
        }

        if gap_pct < GAP_UP_MIN:
            result['reason'] = f"Gap down: {gap_pct:.1%} < {GAP_UP_MIN:.1%}"
        elif gap_pct > GAP_UP_MAX:
            result['reason'] = f"Gap up too high: {gap_pct:.1%} > {GAP_UP_MAX:.1%}"
        else:
            result['valid'] = True

        return result

    @staticmethod
    def validate_low_violation(daily_low: float, open_price: float) -> Dict[str, any]:
        """Validate low violation conditions"""
        threshold = open_price * (1 - LOW_VIOLATION_PCT)

        result = {
            'valid': daily_low >= threshold,
            'threshold': threshold,
            'violation_amount': threshold - daily_low if daily_low < threshold else 0
        }

        return result

    @staticmethod
    def calculate_entry_levels(daily_high: float) -> Dict[str, float]:
        """Calculate entry high and stop loss levels"""
        entry_high = daily_high
        stop_loss = entry_high * (1 - ENTRY_SL_PCT)

        return {
            'entry_high': entry_high,
            'stop_loss': stop_loss
        }

    @staticmethod
    def check_entry_signal(current_price: float, entry_high: float) -> bool:
        """Check if entry signal triggered"""
        return current_price >= entry_high

    @staticmethod
    def check_exit_signal(current_price: float, stop_loss: float) -> bool:
        """Check if exit signal triggered"""
        return current_price <= stop_loss

    @staticmethod
    def validate_stock_for_trading(stock: StockState) -> Dict[str, any]:
        """Comprehensive validation of a stock's trading readiness"""
        validation = {
            'symbol': stock.symbol,
            'overall_valid': False,
            'checks': {}
        }

        # Check 1: Has open price
        validation['checks']['has_open'] = {
            'valid': stock.open_price is not None,
            'value': stock.open_price
        }

        # Check 2: Gap up validation
        if stock.open_price:
            gap_check = RuleEngine.validate_gap_up(stock.open_price, stock.previous_close)
            validation['checks']['gap_up'] = gap_check

        # Check 3: Low violation check
        if stock.open_price:
            low_check = RuleEngine.validate_low_violation(stock.daily_low, stock.open_price)
            validation['checks']['low_violation'] = low_check

        # Check 4: Entry readiness
        validation['checks']['entry_ready'] = {
            'valid': stock.entry_ready,
            'entry_high': stock.entry_high,
            'stop_loss': stock.entry_sl
        }

        # Check 5: Not already entered
        validation['checks']['not_entered'] = {
            'valid': not stock.entered,
            'entry_price': stock.entry_price
        }

        # Overall validity
        validation['overall_valid'] = all(
            check['valid'] for check in validation['checks'].values()
        )

        return validation

    @staticmethod
    def get_rejection_summary(stocks: List[StockState]) -> Dict[str, any]:
        """Get summary of rejections"""
        rejected = [s for s in stocks if not s.is_active]
        active = [s for s in stocks if s.is_active]

        reasons = {}
        for stock in rejected:
            reason = stock.rejection_reason or "Unknown"
            reasons[reason] = reasons.get(reason, 0) + 1

        return {
            'total_stocks': len(stocks),
            'active_stocks': len(active),
            'rejected_stocks': len(rejected),
            'rejection_reasons': reasons,
            'qualified_stocks': len([s for s in active if s.entry_ready])
        }
