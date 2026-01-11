"""
Stock Monitor - Tracks per-stock state during live trading
Supports both continuation and reversal trading situations
"""

import sys
import os
from datetime import datetime, time
import logging
from typing import Dict, Optional, List
import random

from config import *
from reversal_monitor import ReversalMonitor

logger = logging.getLogger(__name__)


class StockState:
    """Tracks the state of a single stock during trading session"""

    def __init__(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'continuation'):
        self.symbol = symbol
        self.instrument_key = instrument_key
        self.previous_close = previous_close
        self.situation = situation  # 'continuation', 'reversal_s1', 'reversal_s2'

        # Market data
        self.open_price: Optional[float] = None
        self.current_price: Optional[float] = None
        self.daily_high: float = float('-inf')
        self.daily_low: float = float('inf')
        self.last_update: Optional[datetime] = None

        # Status flags
        self.is_active = True  # Still being monitored
        self.gap_validated = False  # Renamed from gap_up_validated for reversal
        self.low_violation_checked = False
        self.entry_ready = False
        self.entered = False

        # Reversal-specific flags
        self.climax_detected = False
        self.retracement_trigger: Optional[float] = None
        self.entry_attempts = 0
        self.max_entry_attempts = 3

        # Volume tracking (9:15-9:20)
        self.early_volume = 0.0  # Cumulative volume during monitoring window

        # Entry data (set at 9:20 or dynamically for reversal)
        self.entry_high: Optional[float] = None  # High reached by 9:20
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
        """Set the opening price at 9:15"""
        self.open_price = price
        self.daily_high = price
        self.daily_low = price

    def validate_gap(self) -> bool:
        """Validate gap based on trading situation"""
        if self.open_price is None:
            return False

        gap_pct = (self.open_price - self.previous_close) / self.previous_close

        if self.situation in ['continuation', 'reversal_s1']:
            # Gap up required (0-5%)
            if gap_pct < 0:
                self.reject(f"Gap down: {gap_pct:.1%} (need gap up for {self.situation})")
                return False
            if gap_pct > 0.05:
                self.reject(f"Gap up too high: {gap_pct:.1%} > 5%")
                return False
        elif self.situation == 'reversal_s2':
            # Gap down required (-5% to 0%)
            if gap_pct > 0:
                self.reject(f"Gap up: {gap_pct:.1%} (need gap down for reversal_s2)")
                return False
            if gap_pct < -0.05:
                self.reject(f"Gap down too low: {gap_pct:.1%} < -5%")
                return False
        else:
            self.reject(f"Unknown situation: {self.situation}")
            return False

        self.gap_validated = True
        gap_type = "up" if gap_pct >= 0 else "down"
        logger.info(f"[{self.symbol}] ✅ Gap {gap_type} validated: {gap_pct:.1%} ({self.situation})")
        return True

    def check_low_violation(self) -> bool:
        """Check if low dropped below 1% of open price"""
        if self.open_price is None:
            return False

        threshold = self.open_price * (1 - LOW_VIOLATION_PCT)

        if self.daily_low < threshold:
            self.reject(f"Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
            return False

        self.low_violation_checked = True
        return True

    def prepare_entry(self):
        """Called at 9:20 to set entry levels"""
        if not self.is_active:
            return

        # Set entry high as the high reached by 9:20
        self.entry_high = self.daily_high

        # Set stop loss 4% below entry high
        self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)

        self.entry_ready = True
        logger.info(f"[{self.symbol}] 🎯 Entry prepared - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f}")

    def check_entry_signal(self, price: float) -> bool:
        """Check if price has broken above the entry high"""
        if not self.entry_ready or self.entry_high is None:
            return False

        return price >= self.entry_high

    def enter_position(self, price: float, timestamp: datetime):
        """Enter position at market"""
        self.entry_price = price
        self.entry_time = timestamp
        self.entered = True

        logger.info(f"[{self.symbol}] 🚀 ENTRY at {price:.2f} (target was {self.entry_high:.2f})")

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

        logger.info(f"[{self.symbol}] 🚪 EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason}")

    def reject(self, reason: str):
        """Mark stock as rejected"""
        self.is_active = False
        self.rejection_reason = reason
        logger.info(f"[{self.symbol}] ❌ REJECTED: {reason}")

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


class StockMonitor:
    """Manages monitoring of multiple stocks"""

    def __init__(self):
        self.stocks: Dict[str, StockState] = {}  # instrument_key -> StockState
        self.session_start_time = None

    def add_stock(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'continuation'):
        """Add a stock to monitor"""
        if instrument_key in self.stocks:
            logger.warning(f"Stock {symbol} already being monitored")
            return

        self.stocks[instrument_key] = StockState(symbol, instrument_key, previous_close, situation)
        logger.info(f"📊 Added {symbol} ({situation}) to monitor (prev close: {previous_close:.2f})")

    def remove_stock(self, instrument_key: str):
        """Remove a stock from monitoring"""
        if instrument_key in self.stocks:
            symbol = self.stocks[instrument_key].symbol
            del self.stocks[instrument_key]
            logger.info(f"🗑️ Removed {symbol} from monitor")

    def get_active_stocks(self) -> List[StockState]:
        """Get list of currently active stocks"""
        return [stock for stock in self.stocks.values() if stock.is_active]

    def get_qualified_stocks(self) -> List[StockState]:
        """Get stocks that passed all checks and are ready for selection"""
        qualified = []
        rejected = []

        for stock in self.stocks.values():
            if stock.is_active and stock.gap_validated and stock.low_violation_checked:
                qualified.append(stock)
            else:
                rejected.append(stock)

        # Log qualified stocks
        if qualified:
            logger.info(f"✅ QUALIFIED STOCKS ({len(qualified)}):")
            for stock in qualified:
                gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) if stock.open_price and stock.previous_close else 0
                entry_high = stock.entry_high if stock.entry_high else 0
                entry_sl = stock.entry_sl if stock.entry_sl else 0
                logger.info(f"   {stock.symbol}: Gap {gap_pct:+.1f}%, Entry: ₹{entry_high:.2f}, SL: ₹{entry_sl:.2f}")

        # Log ALL stocks with detailed status (including rejected)
        logger.info(f"📊 STOCK QUALIFICATION STATUS ({len(self.stocks)} total):")
        for stock in self.stocks.values():
            status_parts = []

            # Opening price status
            if stock.open_price is None:
                status_parts.append("❌ No opening price")
            else:
                gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close * 100) if stock.previous_close else 0
                status_parts.append(f"📈 Open: ₹{stock.open_price:.2f} ({gap_pct:+.1f}%)")

            # Gap validation status
            if stock.gap_validated:
                status_parts.append("✅ Gap validated")
            elif stock.rejection_reason and "Gap" in stock.rejection_reason:
                status_parts.append(f"❌ {stock.rejection_reason}")
            else:
                status_parts.append("❓ Gap not validated")

            # Low violation status
            if stock.low_violation_checked:
                status_parts.append("✅ Low violation checked")
            elif stock.rejection_reason and "Low violation" in stock.rejection_reason:
                status_parts.append(f"❌ {stock.rejection_reason}")
            else:
                status_parts.append("❓ Low not checked")

            # Overall status
            if stock.is_active and stock.gap_validated and stock.low_violation_checked:
                overall = "✅ QUALIFIED"
            else:
                overall = "❌ REJECTED"

            logger.info(f"   {stock.symbol}: {overall}")
            for part in status_parts:
                logger.info(f"      {part}")

        logger.info(f"📊 SUMMARY: {len(qualified)} qualified, {len(rejected)} rejected")
        return qualified

    def process_candle_data(self, instrument_key: str, symbol: str, ohlc_list: list):
        """Process 1-minute candle data to set reliable opening price"""
        if instrument_key not in self.stocks:
            return

        stock = self.stocks[instrument_key]

        # Debug: Log OHLC data received
        if ohlc_list:
            logger.info(f"[{symbol}] 📊 Received {len(ohlc_list)} OHLC candles")
            for i, candle_data in enumerate(ohlc_list[:3]):  # Log first 3 candles
                if isinstance(candle_data, dict):
                    logger.info(f"[{symbol}] Candle {i}: {candle_data}")

        # Look for 1-minute candles - use the FIRST valid one we receive
        for candle_data in ohlc_list:
            if isinstance(candle_data, dict) and candle_data.get('interval') == 'I1':
                # Get candle timestamp
                ts_ms = int(candle_data.get('ts', 0))
                candle_time = datetime.fromtimestamp(ts_ms / 1000)

                # Debug: Log candle processing
                open_price = float(candle_data.get('open', 0))
                logger.info(f"[{symbol}] 📈 Processing I1 candle: time={candle_time.strftime('%H:%M:%S')}, open={open_price:.2f}")

                # Use the first valid 1-minute candle we receive for this stock
                # In live trading, this will be the market open candle
                if stock.open_price is None and open_price > 0:
                    stock.set_open_price(open_price)
                    logger.info(f"[{symbol}] ✅ OPEN PRICE SET: {open_price:.2f} (prev close: {stock.previous_close:.2f})")

                    # Validate gap once we have the reliable opening price
                    stock.validate_gap()
                    break

    def process_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: list = None):
        """Process a price tick for a stock"""
        if instrument_key not in self.stocks:
            return

        stock = self.stocks[instrument_key]

        # Process OHLC data first (for reliable opening price)
        if ohlc_list:
            self.process_candle_data(instrument_key, symbol, ohlc_list)

        # Update price tracking (for high/low and current price)
        stock.update_price(price, timestamp)

        # Set session start if this is the first tick
        if self.session_start_time is None:
            self.session_start_time = timestamp

    def check_violations(self):
        """Check for low violations during confirmation window"""
        current_time = datetime.now().time()

        if not (MARKET_OPEN <= current_time <= ENTRY_DECISION_TIME):
            return

        for stock in self.get_active_stocks():
            if stock.gap_validated and not stock.low_violation_checked:
                stock.check_low_violation()

    def accumulate_volume(self, instrument_key: str, volume: float):
        """Accumulate volume during 9:15-9:20 monitoring window"""
        if instrument_key not in self.stocks:
            return

        stock = self.stocks[instrument_key]

        # Only accumulate during monitoring window
        current_time = datetime.now().time()
        if MARKET_OPEN <= current_time <= ENTRY_DECISION_TIME:
            stock.early_volume += volume

    def prepare_entries(self):
        """Called at 9:20 to prepare entry levels"""
        for stock in self.get_qualified_stocks():
            stock.prepare_entry()

    def check_entry_signals(self) -> List[StockState]:
        """Check for entry signals on all qualified stocks"""
        entry_signals = []

        for stock in self.get_qualified_stocks():
            if stock.entry_ready and not stock.entered and stock.check_entry_signal(stock.current_price):
                entry_signals.append(stock)

        return entry_signals

    def check_exit_signals(self) -> List[StockState]:
        """Check for exit signals on entered positions"""
        exit_signals = []

        for stock in self.stocks.values():
            if stock.entered and stock.check_exit_signal(stock.current_price):
                exit_signals.append(stock)

        return exit_signals

    def simulate_opening_prices(self):
        """Simulate opening prices for test mode"""
        if not TEST_MODE or not SIMULATE_OPENING_PRICES:
            return

        logger.info("🧪 TEST MODE: Simulating opening prices for all stocks")

        for stock in self.stocks.values():
            # Generate realistic opening prices based on previous close
            # Create some with gaps (0-5%), some without
            gap_pct = random.uniform(-0.02, 0.08)  # -2% to +8% gap
            open_price = stock.previous_close * (1 + gap_pct)

            # Ensure reasonable price range
            open_price = max(open_price, stock.previous_close * 0.95)  # Min 5% below
            open_price = min(open_price, stock.previous_close * 1.10)  # Max 10% above

            stock.set_open_price(open_price)
            stock.validate_gap()

            logger.info(f"🧪 {stock.symbol}: Simulated open ₹{open_price:.2f} (gap: {gap_pct:+.1%})")

    def generate_test_ticks(self):
        """Generate fake tick data for testing qualification logic"""
        if not TEST_MODE:
            return

        logger.info("🧪 TEST MODE: Generating simulated tick data")

        # Generate some ticks for each stock to simulate market activity
        for instrument_key, stock in self.stocks.items():
            if stock.open_price:
                # Generate a few random ticks around the opening price
                base_price = stock.open_price
                for i in range(3):
                    # Small random movement
                    change = random.uniform(-0.005, 0.005)  # -0.5% to +0.5%
                    tick_price = base_price * (1 + change)

                    # Simulate timestamp
                    timestamp = datetime.now()

                    # Process the simulated tick
                    self.process_tick(instrument_key, stock.symbol, tick_price, timestamp)

                    logger.debug(f"🧪 {stock.symbol}: Simulated tick ₹{tick_price:.2f}")

    def run_test_sequence(self):
        """Run complete test sequence for qualification testing"""
        if not TEST_MODE:
            return

        logger.info("🧪 TEST MODE: Running qualification test sequence")

        # Step 1: Simulate market open
        self.simulate_opening_prices()

        # Step 2: Generate some activity
        self.generate_test_ticks()

        # Step 3: Check violations (simulate confirmation window)
        import time
        time.sleep(1)  # Brief pause

        # Simulate being in confirmation window
        for stock in self.get_active_stocks():
            if stock.gap_validated and not stock.low_violation_checked:
                stock.check_low_violation()

        # Step 4: Prepare entries
        self.prepare_entries()

        logger.info("🧪 TEST MODE: Qualification sequence complete")

    def get_summary(self) -> Dict:
        """Get summary of all stocks"""
        return {
            'total_stocks': len(self.stocks),
            'active_stocks': len(self.get_active_stocks()),
            'qualified_stocks': len(self.get_qualified_stocks()),
            'entered_positions': len([s for s in self.stocks.values() if s.entered]),
            'stock_details': {k: v.get_status() for k, v in self.stocks.items()}
        }
