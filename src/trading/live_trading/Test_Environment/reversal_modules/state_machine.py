"""
State Machine Module

Implements explicit state management for reversal trading stocks to replace boolean flags
and enable proper lifecycle management. This module provides the StockState enum and
state transition methods for the ReversalStockState class.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class StockState(Enum):
    """Explicit states for stock lifecycle management"""
    INITIALIZED = "initialized"
    WAITING_FOR_OPEN = "waiting_for_open"
    GAP_VALIDATED = "gap_validated"
    QUALIFIED = "qualified"
    SELECTED = "selected"
    MONITORING_ENTRY = "monitoring_entry"
    ENTERED = "entered"
    MONITORING_EXIT = "monitoring_exit"
    NOT_SELECTED = "not_selected"
    REJECTED = "rejected"
    UNSUBSCRIBED = "unsubscribed"
    EXITED = "exited"


class StateMachineMixin:
    """Mixin class to add state machine functionality to ReversalStockState"""
    
    def __init__(self):
        """Initialize state machine attributes"""
        self.state = StockState.INITIALIZED
        self.is_subscribed = True  # Track subscription status
    
    def _transition_to(self, new_state: StockState, reason: str = ""):
        """
        Safely transition to a new state with logging
        
        Args:
            new_state: The target state
            reason: Optional reason for the transition
        """
        old_state = self.state
        self.state = new_state
        
        log_msg = f"[{self.symbol}] State transition: {old_state.value} → {new_state.value}"
        if reason:
            log_msg += f" ({reason})"
        
        logger.info(log_msg)
    
    def _transition_to_monitoring_entry(self, reason: str = ""):
        """
        Transition to monitoring_entry state
        
        Args:
            reason: Optional reason for the transition
        """
        self._transition_to(StockState.MONITORING_ENTRY, reason)
    
    def validate_gap(self) -> bool:
        """
        Validate gap based on reversal situation and transition state
        
        Returns:
            True if gap is valid, False otherwise
        """
        if self.open_price is None:
            return False
        
        # Import constants from main module
        from ..reversal_stock_monitor import FLAT_GAP_THRESHOLD
        
        gap_pct = (self.open_price - self.previous_close) / self.previous_close
        
        # Check if gap is within flat range (reject)
        if abs(gap_pct) <= FLAT_GAP_THRESHOLD:
            self.reject(f"Gap too flat: {gap_pct:.1%} (within ±{FLAT_GAP_THRESHOLD:.1%} range)")
            return False
        
        # Situation-specific gap requirements
        if self.situation == 'reversal_s1':
            # Need gap up > flat threshold, but not too high
            if gap_pct <= FLAT_GAP_THRESHOLD:
                self.reject(f"Gap down or flat: {gap_pct:.1%} (need gap up > {FLAT_GAP_THRESHOLD:.1%} for {self.situation})")
                return False
            if gap_pct > 0.05:
                self.reject(f"Gap up too high: {gap_pct:.1%} > 5%")
                return False
        elif self.situation == 'reversal_s2':
            # Need gap down < -flat threshold (no lower limit)
            if gap_pct >= -FLAT_GAP_THRESHOLD:
                self.reject(f"Gap up or flat: {gap_pct:.1%} (need gap down < -{FLAT_GAP_THRESHOLD:.1%} for reversal_s2)")
                return False
        else:
            self.reject(f"Unknown situation: {self.situation}")
            return False
        
        # Gap validated - transition state
        self.gap_validated = True
        self._transition_to(StockState.GAP_VALIDATED, "gap validated")
        
        gap_type = "up" if gap_pct >= 0 else "down"
        logger.info(f"[{self.symbol}] Gap {gap_type} validated: {gap_pct:.1%} ({self.situation})")
        return True
    
    def check_low_violation(self) -> bool:
        """
        Check if low dropped below 1% of open price and transition state
        
        Returns:
            True if no violation, False if violation detected
        """
        if self.open_price is None:
            return False
        
        # Import constants from main module
        from ..reversal_stock_monitor import LOW_VIOLATION_PCT
        
        threshold = self.open_price * (1 - LOW_VIOLATION_PCT)
        
        if self.daily_low < threshold:
            self.reject(f"Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
            return False
        
        self.low_violation_checked = True
        self._transition_to(StockState.QUALIFIED, "low violation check passed")
        
        logger.info(f"[{self.symbol}] Low violation check passed")
        return True
    
    def reject(self, reason: str):
        """
        Mark stock as rejected and stop monitoring
        
        Args:
            reason: Reason for rejection
        """
        self.is_active = False
        self.is_subscribed = False
        self._transition_to(StockState.REJECTED, reason)
        self.rejection_reason = reason
        
        logger.info(f"[{self.symbol}] REJECTED: {reason}")
    
    def prepare_entry(self):
        """Called when stock is selected to set entry levels and transition state"""
        if not self.is_active:
            return
        
        # Set entry high as the high reached so far
        self.entry_high = self.daily_high
        
        # Set stop loss 4% below entry high
        # Import constants from main module
        from ..reversal_stock_monitor import ENTRY_SL_PCT
        self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)
        
        self.entry_ready = True
        self._transition_to_monitoring_entry("entry prepared")
        
        logger.info(f"[{self.symbol}] Entry prepared - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f}")
    
    def enter_position(self, price: float, timestamp: datetime):
        """
        Enter position at market and transition state
        
        Args:
            price: Entry price
            timestamp: Entry timestamp
        """
        self.entry_price = price
        self.entry_time = timestamp
        self.entered = True
        self._transition_to(StockState.MONITORING_EXIT, "position entered")
        
        logger.info(f"[{self.symbol}] ENTRY at {price:.2f} (target was {self.entry_high:.2f})")
    
    def exit_position(self, price: float, timestamp: datetime, reason: str):
        """
        Exit position and transition state
        
        Args:
            price: Exit price
            timestamp: Exit timestamp
            reason: Reason for exit
        """
        self.exit_price = price
        self.exit_time = timestamp
        self.is_subscribed = False
        self._transition_to(StockState.EXITED, reason)
        
        # Calculate P&L
        if self.entry_price:
            self.pnl = (price - self.entry_price) / self.entry_price * 100
        
        logger.info(f"[{self.symbol}] EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason}")
    
    def mark_not_selected(self):
        """Mark stock as not selected during selection phase"""
        self.is_active = False
        self.is_subscribed = False
        self._transition_to(StockState.NOT_SELECTED, "not selected (limited slots)")
        
        logger.info(f"[{self.symbol}] Not selected (limited slots)")
    
    def mark_selected(self):
        """Mark stock as selected during selection phase"""
        self._transition_to(StockState.SELECTED, "selected for trading")
        
        logger.info(f"[{self.symbol}] Selected for trading")
    
    def is_in_state(self, *states: StockState) -> bool:
        """
        Check if stock is in one of the specified states
        
        Args:
            states: One or more states to check against
            
        Returns:
            True if stock is in any of the specified states
        """
        # Handle both enum values and string values for backward compatibility
        state_values = []
        for state in states:
            if isinstance(state, StockState):
                state_values.append(state.value)
            else:
                state_values.append(state)
        
        return self.state.value in state_values
    
    def can_transition_to(self, target_state: StockState) -> bool:
        """
        Check if transition to target state is valid
        
        Args:
            target_state: The state to transition to
            
        Returns:
            True if transition is valid
        """
        # Define valid state transitions
        valid_transitions = {
            StockState.INITIALIZED: [StockState.WAITING_FOR_OPEN],
            StockState.WAITING_FOR_OPEN: [StockState.GAP_VALIDATED, StockState.REJECTED],
            StockState.GAP_VALIDATED: [StockState.QUALIFIED, StockState.REJECTED],
            StockState.QUALIFIED: [StockState.SELECTED, StockState.NOT_SELECTED, StockState.REJECTED],
            StockState.SELECTED: [StockState.MONITORING_ENTRY],
            StockState.MONITORING_ENTRY: [StockState.MONITORING_EXIT, StockState.REJECTED],
            StockState.MONITORING_EXIT: [StockState.EXITED, StockState.REJECTED],
            StockState.NOT_SELECTED: [StockState.UNSUBSCRIBED],
            StockState.REJECTED: [StockState.UNSUBSCRIBED],
            StockState.EXITED: [StockState.UNSUBSCRIBED],
            StockState.UNSUBSCRIBED: []  # Terminal state
        }
        
        current_transitions = valid_transitions.get(self.state, [])
        return target_state in current_transitions