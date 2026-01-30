"""
Tick Processor Module

Implements self-contained tick processing for reversal trading stocks to eliminate
cross-contamination and nested loops. Each stock processes only its own ticks using
its own price data and state-based routing.
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ReversalTickProcessor:
    """Handles tick processing for individual reversal stocks"""
    
    def __init__(self, stock):
        """
        Initialize tick processor for a specific stock
        
        Args:
            stock: ReversalStockState instance
        """
        self.stock = stock
    
    def process_tick(self, price: float, timestamp: datetime, reversal_monitor=None):
        """
        Process a tick for THIS stock only with real-time high/low tracking
        
        Args:
            price: Current price for THIS stock
            timestamp: Tick timestamp
            reversal_monitor: ReversalMonitor instance for trigger checks
        """
        # Always update price tracking regardless of state
        self.stock.update_price(price, timestamp)
        
        # Real-time high/low tracking for both Strong Start and OOPS
        # This should be called for all active stocks to update entry levels
        if self.stock.is_active:
            self._track_entry_levels(price, timestamp)
        
        # Route to state-specific handlers
        if self.stock.is_in_state(self.stock.state, 'monitoring_entry'):
            self._handle_entry_monitoring(price, timestamp, reversal_monitor)
        
        elif self.stock.is_in_state(self.stock.state, 'monitoring_exit'):
            self._handle_exit_monitoring(price, timestamp)
        
        # Other states don't need tick processing:
        # - INITIALIZED, WAITING_FOR_OPEN: No data yet
        # - GAP_VALIDATED, QUALIFIED, SELECTED: Waiting for entry time
        # - REJECTED, NOT_SELECTED, UNSUBSCRIBED, EXITED: Terminal states

    def _track_entry_levels(self, price: float, timestamp: datetime):
        """
        Track entry levels and check for low violations in real-time
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        # FIX: Only Strong Start stocks need to track entry levels (high/low monitoring)
        # OOPS stocks only need to monitor if price crosses previous close
        if self.stock.situation == 'reversal_s1':
            # Update entry high as price moves higher
            if self.stock.daily_high > self.stock.open_price:
                new_entry_high = self.stock.daily_high
                new_entry_sl = new_entry_high * (1 - 0.04)  # 4% SL
                
                # Only update if entry high has increased
                if self.stock.entry_high is None or new_entry_high > self.stock.entry_high:
                    self.stock.entry_high = new_entry_high
                    self.stock.entry_sl = new_entry_sl
                    self.stock.entry_ready = True
                    logger.info(f"[{self.stock.symbol}] Strong Start entry updated - High: {self.stock.entry_high:.2f}, SL: {self.stock.entry_sl:.2f}")
        
        # Real-time low violation checking for both Strong Start and OOPS
        if self.stock.open_price is not None:
            # Check for low violation in real-time
            low_violation_pct = ((self.stock.open_price - self.stock.daily_low) / self.stock.open_price) * 100
            
            # Import constants from main module - FIXED: Use absolute import to avoid relative import error
            try:
                from src.trading.live_trading.reversal_stock_monitor import LOW_VIOLATION_PCT
            except ImportError:
                # Fallback to relative import if absolute doesn't work
                try:
                    from ..reversal_stock_monitor import LOW_VIOLATION_PCT
                except ImportError:
                    # Final fallback - use hardcoded value
                    LOW_VIOLATION_PCT = 0.01
            
            if low_violation_pct >= LOW_VIOLATION_PCT * 100:  # Convert to percentage
                if not self.stock.low_violation_checked:
                    self.stock.low_violation_checked = True
                    logger.info(f"[{self.stock.symbol}] Low violation detected: {low_violation_pct:.2f}% >= {LOW_VIOLATION_PCT*100:.1f}%")
                    
                    # Mark as rejected if this is a Strong Start stock
                    if self.stock.situation == 'reversal_s1':
                        self.stock.reject(f"Low violation: {low_violation_pct:.2f}% >= {LOW_VIOLATION_PCT*100:.1f}%")
    
    def _handle_entry_monitoring(self, price: float, timestamp: datetime, reversal_monitor=None):
        """
        Handle entry monitoring based on stock situation
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
            reversal_monitor: ReversalMonitor instance for trigger checks
        """
        # DEBUG: Add state validation logging
        logger.info(f"[{self.stock.symbol}] Entry monitoring - Current state: {self.stock.state.value}, Situation: {self.stock.situation}, Entry ready: {self.stock.entry_ready}, Entered: {self.stock.entered}")
        
        # Only process entries if stock is in correct state and ready
        if not self.stock.is_in_state('monitoring_entry'):
            logger.info(f"[{self.stock.symbol}] Skipping entry - not in monitoring_entry state (current: {self.stock.state.value})")
            return
        
        if not self.stock.entry_ready:
            logger.info(f"[{self.stock.symbol}] Skipping entry - not entry ready")
            return
            
        if self.stock.entered:
            logger.info(f"[{self.stock.symbol}] Skipping entry - already entered")
            return

        if self.stock.situation == 'reversal_s2':
            # OOPS entry logic - FIX: Simplified OOPS logic without external monitor
            self._check_oops_entry_simple(price, timestamp)
        
        elif self.stock.situation == 'reversal_s1':
            # Strong Start entry logic - FIX: Simplified Strong Start logic without external monitor
            self._check_strong_start_entry_simple(price, timestamp)
    
    def _check_oops_entry_simple(self, price: float, timestamp: datetime):
        """
        Check OOPS entry conditions using THIS stock's price (simplified version)
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        # Already triggered - don't re-enter
        if self.stock.oops_triggered or self.stock.entered:
            return
        
        # Need opening price data
        if self.stock.open_price is None or self.stock.previous_close is None:
            return
        
        # OOPS: Enter when price crosses above previous close
        if price >= self.stock.previous_close:
            self.stock.oops_triggered = True
            
            # Set entry_high and entry_sl when OOPS triggers
            self.stock.entry_high = price
            # Import constants from main module - FIXED: Use absolute import
            try:
                from src.trading.live_trading.reversal_stock_monitor import ENTRY_SL_PCT
            except ImportError:
                # Fallback to relative import
                try:
                    from ..reversal_stock_monitor import ENTRY_SL_PCT
                except ImportError:
                    # Final fallback - use hardcoded value
                    ENTRY_SL_PCT = 0.04
            
            self.stock.entry_sl = price * (1 - ENTRY_SL_PCT)  # 4% SL
            
            # Enter position
            self.stock.enter_position(price, timestamp)
            
            logger.info(f"[{self.stock.symbol}] OOPS TRIGGERED at {price:.2f} - Entered position")
    
    def _check_strong_start_entry_simple(self, price: float, timestamp: datetime):
        """
        Check Strong Start entry conditions using THIS stock's price (simplified version)
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        # Already triggered - don't re-enter
        if self.stock.strong_start_triggered or self.stock.entered:
            return
        
        # Need opening price data
        if self.stock.open_price is None or self.stock.previous_close is None:
            return
        
        # Strong Start: Enter when price crosses above current high
        if price >= self.stock.daily_high:
            self.stock.strong_start_triggered = True
            
            # Set entry_high and entry_sl when Strong Start triggers
            self.stock.entry_high = price
            # Import constants from main module - FIXED: Use absolute import
            try:
                from src.trading.live_trading.reversal_stock_monitor import ENTRY_SL_PCT
            except ImportError:
                # Fallback to relative import
                try:
                    from ..reversal_stock_monitor import ENTRY_SL_PCT
                except ImportError:
                    # Final fallback - use hardcoded value
                    ENTRY_SL_PCT = 0.04
            
            self.stock.entry_sl = price * (1 - ENTRY_SL_PCT)  # 4% SL
            
            # Enter position
            self.stock.enter_position(price, timestamp)
            
            logger.info(f"[{self.stock.symbol}] STRONG START TRIGGERED at {price:.2f} - Entered position")
    
    def _handle_exit_monitoring(self, price: float, timestamp: datetime):
        """
        Handle exit monitoring (trailing SL + exit signals)
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        if not self.stock.entered or self.stock.entry_price is None:
            return
        
        # Calculate current profit percentage
        profit_pct = (price - self.stock.entry_price) / self.stock.entry_price
        
        # Import constants from main module - FIXED: Use absolute import
        try:
            from src.trading.live_trading.reversal_stock_monitor import TRAILING_SL_THRESHOLD
        except ImportError:
            # Fallback to relative import
            try:
                from ..reversal_stock_monitor import TRAILING_SL_THRESHOLD
            except ImportError:
                # Final fallback - use hardcoded value
                TRAILING_SL_THRESHOLD = 0.05
        
        # Trailing SL: Move SL to entry when 5% profit
        if profit_pct >= TRAILING_SL_THRESHOLD and self.stock.entry_sl < self.stock.entry_price:
            old_sl = self.stock.entry_sl
            self.stock.entry_sl = self.stock.entry_price  # Move to breakeven
            logger.info(f"[{self.stock.symbol}] Trailing SL adjusted: Rs{old_sl:.2f} → Rs{self.stock.entry_sl:.2f} (5% profit reached)")
        
        # Check exit signal: SL hit
        if price <= self.stock.entry_sl:
            pnl = profit_pct * 100
            self.stock.exit_position(price, timestamp, "Stop Loss Hit")
            logger.info(f"[{self.stock.symbol}] EXIT at Rs{price:.2f}, PNL: {pnl:+.2f}%")
