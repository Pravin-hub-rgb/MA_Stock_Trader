#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Stock Monitor - Dedicated monitoring for reversal trading
Completely separate from continuation logic to avoid contamination

MODULAR ARCHITECTURE: Uses reversal_modules for state management, tick processing,
and subscription management to eliminate cross-contamination bugs.
"""

import sys
import os
from datetime import datetime, time, timedelta
import logging
from typing import Dict, Optional, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import specific config variables to avoid undefined variable errors
from config import (
    MARKET_OPEN,
    PREP_START,
    LOW_VIOLATION_PCT,
    ENTRY_SL_PCT,
    FLAT_GAP_THRESHOLD,
    TRAILING_SL_THRESHOLD
)

# Import modular architecture
from reversal_modules.state_machine import StateMachineMixin, StockState
from reversal_modules.tick_processor import ReversalTickProcessor

logger = logging.getLogger(__name__)


class ReversalStockState(StateMachineMixin):
    """Tracks the state of a single stock during reversal trading session
    
    MODULAR ARCHITECTURE: Uses StateMachineMixin for explicit state management
    and ReversalTickProcessor for self-contained tick processing.
    """

    def __init__(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'reversal_s2'):
        # Initialize state machine - FIXED: Call parent __init__ properly
        super().__init__()
        
        self.symbol = symbol
        self.instrument_key = instrument_key
        self.previous_close = previous_close
        self.situation = situation  # 'reversal_s1' (Strong Start), 'reversal_s2' (OOPS)

        # Market data
        self.open_price: Optional[float] = None
        self.current_price: Optional[float] = None
        self.daily_high: float = float('-inf')
        self.daily_low: float = float('inf')
        self.last_update: Optional[datetime] = None

        # Status flags (kept for backward compatibility during transition)
        self.is_active = True  # Still being monitored
        self.gap_validated = False
        self.low_violation_checked = False
        self.entry_ready = False
        self.entered = False

        # Reversal-specific flags (OOPS system)
        self.oops_triggered = False
        self.strong_start_triggered = False

        # Entry data (set dynamically for reversal)
        self.entry_high: Optional[float] = None  # High reached after entry time
        self.entry_sl: Optional[float] = None    # 4% below entry_high

        # Position data (when entered)
        self.entry_price: Optional[float] = None
        self.entry_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.exit_time: Optional[datetime] = None
        self.pnl: Optional[float] = None

        # Rejection reasons
        self.rejection_reason: Optional[str] = None

    def update_price(self, price: float, timestamp: datetime):
        """Update price and track high/low"""
        self.current_price = price
        self.daily_high = max(self.daily_high, price)
        self.daily_low = min(self.daily_low, price)
        self.last_update = timestamp

    def set_open_price(self, price: float):
        """Set the opening price from API"""
        self.open_price = price
        self.daily_high = price
        self.daily_low = price

    def validate_gap(self) -> bool:
        """Validate gap based on reversal situation"""
        if self.open_price is None:
            return False

        gap_pct = (self.open_price - self.previous_close) / self.previous_close

        # Check if gap is within flat range (reject)
        if abs(gap_pct) <= FLAT_GAP_THRESHOLD:
            self.reject(f"Gap too flat: {gap_pct:.1%} (within ±{FLAT_GAP_THRESHOLD:.1%} range)")
            return False

        # Situation-specific gap requirements
        if self.situation == 'reversal_s1':
            # Need gap up > flat threshold, but not too high
            if gap_pct <= 0:  # Fixed: Check if gap is down or flat (not <= flat threshold)
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

        # Update situation type based on actual gap direction
        if gap_pct > 0:  # Gap up
            self.situation = 'reversal_s1'  # Strong Start
            logger.info(f"[{self.symbol}] Gap direction update: Gap up → Strong Start ({self.situation})")
        else:  # Gap down
            self.situation = 'reversal_s2'  # OOPS
            logger.info(f"[{self.symbol}] Gap direction update: Gap down → OOPS ({self.situation})")

        # Transition to GAP_VALIDATED state
        self.gap_validated = True
        self._transition_to(StockState.GAP_VALIDATED, "gap validated")
        
        gap_type = "up" if gap_pct >= 0 else "down"
        logger.info(f"[{self.symbol}] Gap {gap_type} validated: {gap_pct:.1%} ({self.situation})")
        return True

    def get_candidate_type(self) -> str:
        """Get candidate type based on gap direction and situation"""
        if not self.gap_validated or self.open_price is None:
            return "UNKNOWN"
        
        gap_pct = (self.open_price - self.previous_close) / self.previous_close
        
        if self.situation == 'reversal_s1':
            # Gap up stocks are Strong Start candidates
            return "Strong Start" if gap_pct > 0 else "FLAT"
        else:  # reversal_s2
            # Gap down stocks are OOPS candidates
            return "OOPS" if gap_pct < 0 else "FLAT"
        
        return "UNKNOWN"

    def check_low_violation(self) -> bool:
        """Check if low dropped below 1% of open price"""
        if self.open_price is None:
            return False

        threshold = self.open_price * (1 - LOW_VIOLATION_PCT)

        if self.daily_low < threshold:
            self.reject(f"Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
            return False

        self.low_violation_checked = True
        # Transition to QUALIFIED state
        self._transition_to(StockState.QUALIFIED, "low violation check passed")
        
        # ✅ FIX: For OOPS stocks, set entry price and ready immediately when qualified
        if self.situation == 'reversal_s2':  # OOPS
            self.entry_price = self.previous_close  # Set entry to previous close
            self.entry_ready = True  # Mark as ready for entry
            logger.info(f"[{self.symbol}] OOPS qualified - Entry price set to previous close: {self.entry_price:.2f}")
        
        return True

    def prepare_entry_oops(self):
        """Prepare entry for OOPS stocks"""
        if not self.is_active:
            return

        # OOPS: No pre-set entry levels, entry happens on trigger
        # Entry and SL are set dynamically in tick processor when OOPS triggers
        self.entry_ready = True
        logger.info(f"[{self.symbol}] OOPS ready - waiting for trigger (prev close: {self.previous_close:.2f})")

    def prepare_entry_ss(self):
        """Prepare entry for Strong Start stocks"""
        if not self.is_active:
            return

        # Strong Start: Check low violation at entry time
        # Let ticks naturally update high/low during the window
        # Entry_high will be set when price crosses above high
        logger.info(f"[{self.symbol}] Strong Start: Checking low violation at entry time")
        
        # Check if low violated (gone below 1% from opening price)
        if self.daily_low < self.open_price * (1 - LOW_VIOLATION_PCT):
            self.reject(f"Low violation: {self.daily_low:.2f} < {self.open_price * (1 - LOW_VIOLATION_PCT):.2f}")
            return
        
        # If no low violation, keep monitoring - entry_high will be set when price crosses high
        self.entry_ready = True
        self._transition_to_monitoring_entry("Strong Start ready for entry")
        logger.info(f"[{self.symbol}] Strong Start ready - No low violation, monitoring for entry (current high: {self.daily_high:.2f})")
        
        # FIX: Call update_entry_levels() immediately after prepare_entry_ss() to set entry levels
        self.update_entry_levels()

    def prepare_entry(self):
        """Called when stock is qualified to set entry levels"""
        if not self.is_active:
            return

        # Transition to SELECTED state before preparing entry
        if self.state.value == 'qualified':
            self._transition_to(StockState.SELECTED, "preparing entry")
            logger.info(f"[{self.symbol}] Transitioned to SELECTED state for entry preparation")

        if self.situation == 'reversal_s1':
            self.prepare_entry_ss()
        elif self.situation == 'reversal_s2':
            self.prepare_entry_oops()
        else:
            logger.warning(f"[{self.symbol}] Unknown situation: {self.situation}")

    def update_entry_levels(self):
        """Update entry levels dynamically as price moves (for Strong Start)"""
        if not self.is_active:
            return
        
        if self.situation != 'reversal_s1':
            return

        # For Strong Start, update entry high as price moves higher
        if self.daily_high > self.open_price:
            new_entry_high = self.daily_high
            new_entry_sl = new_entry_high * (1 - ENTRY_SL_PCT)
            
            # Only update if entry high has increased
            if self.entry_high is None or new_entry_high > self.entry_high:
                self.entry_high = new_entry_high
                self.entry_sl = new_entry_sl
                self.entry_ready = True
                logger.info(f"[{self.symbol}] Strong Start entry updated - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f}")

    def check_entry_signal(self, price: float) -> bool:
        """Check if price has broken above the current high (Strong Start) or previous close (OOPS)"""
        if not self.entry_ready or not self.is_active:
            return False

        if self.situation == 'reversal_s1':
            # Strong Start: Enter when price crosses above current high
            return price >= self.daily_high
        elif self.situation == 'reversal_s2':
            # OOPS: Enter when price crosses above previous close
            return price >= self.previous_close
        
        return False

    def enter_position(self, price: float, timestamp: datetime):
        """Enter position at market"""
        self.entry_price = price
        self.entry_time = timestamp
        self.entered = True

        # Transition to ENTERED state
        self._transition_to(StockState.ENTERED, "position entered")

        # For Strong Start, set entry_high and entry_sl when entering
        if self.situation == 'reversal_s1':
            self.entry_high = self.daily_high  # Set to current high
            self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)  # 4% below high
            logger.info(f"[{self.symbol}] ENTRY at {price:.2f} - Strong Start (High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f})")
        else:
            logger.info(f"[{self.symbol}] ENTRY at {price:.2f} - OOPS trigger")

    def check_exit_signal(self, price: float) -> bool:
        """Check if stop loss hit"""
        if not self.entered or self.entry_sl is None:
            return False

        return price <= self.entry_sl

    def exit_position(self, price: float, timestamp: datetime, reason: str):
        """Exit position"""
        self.exit_price = price
        self.exit_time = timestamp

        # Calculate P&L
        if self.entry_price:
            self.pnl = (price - self.entry_price) / self.entry_price * 100

        logger.info(f"[{self.symbol}] EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason}")

    def reject(self, reason: str):
        """Mark stock as rejected - uses StateMachineMixin's reject method"""
        # Call the StateMachineMixin's reject method which properly sets state and handles unsubscription
        StateMachineMixin.reject(self, reason)

    def get_status(self) -> Dict:
        """Get current status for logging"""
        return {
            'symbol': self.symbol,
            'situation': self.situation,
            'is_active': self.is_active,
            'open_price': self.open_price,
            'current_price': self.current_price,
            'daily_high': self.daily_high,
            'daily_low': self.daily_low,
            'gap_validated': self.gap_validated,
            'entry_ready': self.entry_ready,
            'entry_high': self.entry_high,
            'entry_sl': self.entry_sl,
            'entered': self.entered,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'rejection_reason': self.rejection_reason
        }


class ReversalStockMonitor:
    """Manages monitoring of multiple stocks for reversal trading"""

    def __init__(self):
        self.stocks: Dict[str, ReversalStockState] = {}  # instrument_key -> ReversalStockState
        self.session_start_time = None

    def add_stock(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'reversal_s2'):
        """Add a stock to monitor for reversal trading"""
        if instrument_key in self.stocks:
            logger.warning(f"Stock {symbol} already being monitored")
            return

        self.stocks[instrument_key] = ReversalStockState(symbol, instrument_key, previous_close, situation)
        logger.info(f"Added {symbol} ({situation}) to reversal monitor (prev close: {previous_close:.2f})")

    def remove_stock(self, instrument_key: str):
        """Remove a stock from monitoring"""
        if instrument_key in self.stocks:
            symbol = self.stocks[instrument_key].symbol
            del self.stocks[instrument_key]
            logger.info(f"Removed {symbol} from reversal monitor")

    def get_active_stocks(self) -> List[ReversalStockState]:
        """Get list of currently active stocks"""
        return [stock for stock in self.stocks.values() if stock.is_active]

    def get_qualified_stocks(self) -> List[ReversalStockState]:
        """Get stocks that passed gap and low violation checks"""
        qualified = []
        rejected = []

        logger.info("=== QUALIFICATION CHECK START ===")
        
        for stock in self.stocks.values():
            # For OOPS (reversal_s2): only gap validation needed
            if stock.situation == 'reversal_s2' and stock.is_active and stock.gap_validated:
                qualified.append(stock)
                logger.info(f"[{stock.symbol}] QUALIFIED: OOPS - Gap validated")
            # For Strong Start (reversal_s1): gap validation AND low violation check needed
            elif stock.situation == 'reversal_s1' and stock.is_active and stock.gap_validated and stock.low_violation_checked:
                qualified.append(stock)
                logger.info(f"[{stock.symbol}] QUALIFIED: Strong Start - Gap validated and low violation checked")
            else:
                rejected.append(stock)
                logger.info(f"[{stock.symbol}] REJECTED: Missing checks")

        # Log qualified stocks (clean output for reversal)
        if qualified:
            logger.info(f"QUALIFIED REVERSAL STOCKS ({len(qualified)}):")
            for stock in qualified:
                gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) if stock.open_price and stock.previous_close else 0
                candidate_type = stock.get_candidate_type()
                logger.info(f"   {stock.symbol}: {candidate_type} - Gap: {gap_pct:+.1f}%")

        # ✅ FIXED: Only show actively monitored stocks (not rejected ones)
        active_stocks = self.get_active_stocks()
        logger.info(f"REVERSAL STOCK STATUS ({len(active_stocks)} actively monitored):")
        for stock in active_stocks:
            if stock.open_price is None:
                logger.info(f"   {stock.symbol}: Waiting for opening price")
            else:
                gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close * 100) if stock.previous_close else 0
                status = "QUALIFIED" if (stock.gap_validated and stock.low_violation_checked) else "PENDING"
                logger.info(f"   {stock.symbol}: {status} - Open: Rs{stock.open_price:.2f} ({gap_pct:+.1f}%)")

        logger.info(f"SUMMARY: {len(qualified)} qualified, {len(rejected)} rejected")
        logger.info("=== QUALIFICATION CHECK END ===")
        return qualified

    def process_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: list = None):
        """Process a price tick for a stock using modular architecture"""
        if instrument_key not in self.stocks:
            return

        stock = self.stocks[instrument_key]

        # Delegate to stock's own tick processor (modular architecture)
        # This handles state-based routing and all entry/exit logic
        from reversal_modules.tick_processor import ReversalTickProcessor
        tick_processor = ReversalTickProcessor(stock)
        tick_processor.process_tick(price, timestamp)

        # Set session start if this is the first tick
        if self.session_start_time is None:
            self.session_start_time = timestamp

    def check_violations(self):
        """Check for low violations for opened stocks that haven't been checked yet"""
        for stock in self.get_active_stocks():
            if stock.gap_validated and not stock.low_violation_checked and stock.open_price:
                stock.check_low_violation()

    def prepare_entries(self):
        """Called when stocks are qualified to prepare entry levels"""
        logger.info("=== PREPARE ENTRIES START ===")
        
        # FIX: Check low violations BEFORE qualification to ensure Strong Start stocks aren't dropped
        logger.info("=== PREPARE ENTRIES: Checking low violations before qualification ===")
        self.check_violations()
        
        qualified_stocks = self.get_qualified_stocks()
        logger.info(f"Preparing entries for {len(qualified_stocks)} qualified stocks")
        
        for stock in qualified_stocks:
            logger.info(f"[{stock.symbol}] Calling prepare_entry() for {stock.situation}")
            
            if stock.situation == 'reversal_s1':
                # Only Strong Start stocks need entry_high/entry_sl processing
                stock.prepare_entry()
                logger.info(f"[{stock.symbol}] After prepare_entry() - entry_high={stock.entry_high}, entry_sl={stock.entry_sl}")
            elif stock.situation == 'reversal_s2':
                # OOPS stocks don't need entry_high/entry_sl - they trigger on previous_close
                stock.entry_ready = True
                stock._transition_to_monitoring_entry("OOPS ready for entry")
                logger.info(f"[{stock.symbol}] OOPS ready - waiting for trigger (prev close: {stock.previous_close:.2f})")
            else:
                logger.warning(f"[{stock.symbol}] Unknown situation: {stock.situation}")
        
        logger.info("=== PREPARE ENTRIES END ===")

    def check_entry_signals(self) -> List[ReversalStockState]:
        """Check for entry signals on all qualified stocks"""
        entry_signals = []

        for stock in self.get_qualified_stocks():
            if stock.entry_ready and not stock.entered and stock.check_entry_signal(stock.current_price):
                entry_signals.append(stock)

        return entry_signals

    def check_exit_signals(self) -> List[ReversalStockState]:
        """Check for exit signals on entered positions"""
        exit_signals = []

        for stock in self.stocks.values():
            if stock.entered and stock.check_exit_signal(stock.current_price):
                exit_signals.append(stock)

        return exit_signals

    def get_subscribed_symbols(self) -> List[str]:
        """Get list of symbols that are actively subscribed"""
        return [stock.symbol for stock in self.get_active_stocks()]

    def get_low_violation_stocks(self) -> List[ReversalStockState]:
        """Get stocks that have violated their low price threshold"""
        return [stock for stock in self.get_active_stocks() 
                if stock.state == 'LOW_VIOLATION']

    def get_summary(self) -> Dict:
        """Get summary of all stocks"""
        return {
            'total_stocks': len(self.stocks),
            'active_stocks': len(self.get_active_stocks()),
            'qualified_stocks': len(self.get_qualified_stocks()),
            'entered_positions': len([s for s in self.stocks.values() if s.entered]),
            'stock_details': {k: v.get_status() for k, v in self.stocks.items()}
        }
