"""
Reversal-specific monitoring logic
Extends stock monitoring with reversal situation handling
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, time
import pytz

IST = pytz.timezone('Asia/Kolkata')

class ReversalMonitor:
    """Handles reversal-specific monitoring logic"""

    def __init__(self):
        # 3-min OHLC tracking for climax detection
        self.three_min_bars = {}  # symbol -> list of 3-min bars

    def validate_reversal_gap(self, open_price: float, previous_close: float,
                            situation: str) -> tuple[bool, str]:
        """
        Validate gap based on situation

        Args:
            open_price: Market open price
            previous_close: Previous day's close
            situation: 'continuation', 'reversal_s1', or 'reversal_s2'

        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        if open_price is None or previous_close is None:
            return False, "Missing price data"

        gap_pct = (open_price - previous_close) / previous_close

        if situation in ['continuation', 'reversal_s1']:
            # Gap up required (0-5%)
            if gap_pct < 0:
                return False, f"Gap down: {gap_pct:.1f} (need gap up for {situation})"
            if gap_pct > 0.05:
                return False, f"Gap up too high: {gap_pct:.1f} > 5%"
            return True, f"Gap up validated: {gap_pct:.1f}"
        elif situation == 'reversal_s2':
            # Gap down required (-5% to 0%)
            if gap_pct > 0:
                return False, f"Gap up: {gap_pct:.1f} (need gap down for reversal_s2)"
            if gap_pct < -0.05:
                return False, f"Gap down too low: {gap_pct:.1f} < -5%"
            return True, f"Gap down validated: {gap_pct:.1f}"
        else:
            return False, f"Unknown situation: {situation}"

    def detect_subcase_2a(self, open_price: float, daily_low: float) -> bool:
        """
        Detect sub-case 2A: Gap down + open = low (strong start)

        Args:
            open_price: Market open price
            daily_low: Current daily low

        Returns:
            bool: True if 2A conditions met
        """
        if open_price is None or daily_low is None:
            return False

        # Open equals low (within 1 paisa tolerance)
        return abs(open_price - daily_low) <= 0.01

    def process_three_min_bar(self, symbol: str, ohlc_data: Dict) -> None:
        """
        Process 3-minute OHLC bar for climax detection

        Args:
            symbol: Stock symbol
            ohlc_data: OHLC data dict
        """
        if symbol not in self.three_min_bars:
            self.three_min_bars[symbol] = []

        # Keep last 10 bars for climax analysis
        self.three_min_bars[symbol].append(ohlc_data)
        if len(self.three_min_bars[symbol]) > 10:
            self.three_min_bars[symbol].pop(0)

    def detect_climax_bar(self, symbol: str) -> bool:
        """
        Detect if the latest 3-min bar is a climax bar

        Args:
            symbol: Stock symbol

        Returns:
            bool: True if climax bar detected
        """
        if symbol not in self.three_min_bars:
            return False

        bars = self.three_min_bars[symbol]
        if len(bars) < 3:
            return False

        # Get latest bar
        latest_bar = bars[-1]
        latest_range = latest_bar.get('high', 0) - latest_bar.get('low', 0)

        # Check if it's the largest range in recent bars
        recent_ranges = [bar.get('high', 0) - bar.get('low', 0) for bar in bars[-6:]]  # Last 6 bars
        max_recent_range = max(recent_ranges)

        return latest_range >= max_recent_range

    def calculate_dynamic_retracement(self, daily_low: float, current_high: float) -> float:
        """
        Calculate 40% retracement trigger from daily range

        Args:
            daily_low: Lowest low of the day
            current_high: Current high of the day

        Returns:
            float: Entry trigger price
        """
        if daily_low is None or current_high is None:
            return float('inf')

        daily_range = current_high - daily_low
        return daily_low + (daily_range * 0.4)

    def should_enter_subcase_2a(self, stock_state, current_time: time) -> bool:
        """
        Check if should enter for sub-case 2A (within first 5 min)

        Args:
            stock_state: StockState object
            current_time: Current market time

        Returns:
            bool: True if should enter
        """
        # Must be within first 5 minutes
        market_open = time(9, 15)
        five_min_later = time(9, 20)

        if not (market_open <= current_time <= five_min_later):
            return False

        # Must have gap validated and open = low
        if not (hasattr(stock_state, 'gap_validated') and stock_state.gap_validated):
            return False

        return self.detect_subcase_2a(stock_state.open_price, stock_state.daily_low)

    def should_enter_subcase_2b(self, stock_state, current_time: time) -> tuple[bool, float]:
        """
        Check if should enter for sub-case 2B (dynamic retracement, no time limit)

        Args:
            stock_state: StockState object
            current_time: Current market time

        Returns:
            Tuple[bool, float]: (should_enter, trigger_price)
        """
        # Must have climax bar detected
        if not hasattr(stock_state, 'climax_detected') or not stock_state.climax_detected:
            return False, float('inf')

        # Calculate current trigger
        trigger = self.calculate_dynamic_retracement(stock_state.daily_low, stock_state.daily_high)

        # Check if price has reached trigger
        if stock_state.current_price and stock_state.current_price >= trigger:
            return True, trigger

        return False, trigger

    def prepare_reversal_entry(self, stock_state, situation: str) -> None:
        """
        Prepare entry levels for reversal situations

        Args:
            stock_state: StockState object
            situation: Trading situation
        """
        if situation in ['continuation', 'reversal_s1']:
            # Standard continuation entry
            stock_state.entry_high = stock_state.daily_high
            stock_state.entry_sl = stock_state.entry_high * 0.96  # 4% below

        elif situation == 'reversal_s2':
            # Situation 2: Wait for sub-case determination
            # Entry levels set dynamically based on sub-case
            pass

        stock_state.entry_ready = True

    def update_retracement_trigger(self, stock_state) -> None:
        """
        Update retracement trigger when new daily high is made

        Args:
            stock_state: StockState object
        """
        if hasattr(stock_state, 'retracement_trigger'):
            new_trigger = self.calculate_dynamic_retracement(stock_state.daily_low, stock_state.daily_high)
            stock_state.retracement_trigger = new_trigger
