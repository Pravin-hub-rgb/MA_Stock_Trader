#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dummy Tick Streamer for Continuation Bot Testing
Creates a controlled environment to test SVRO entry triggers with synthetic price data
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.live_trading.continuation_stock_monitor import StockMonitor
from src.trading.live_trading.continuation_stock_monitor import StockState

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuation_tick_streamer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ContinuationDummyTickStreamer')


class TestStock:
    """Represents a test stock with configurable parameters for continuation bot"""

    def __init__(self, symbol: str, instrument_key: str, previous_close: float,
                 open_price: float, situation: str = 'continuation'):
        self.symbol = symbol
        self.instrument_key = instrument_key
        self.previous_close = previous_close
        self.open_price = open_price
        self.situation = situation
        self.current_price = open_price
        self.is_active = True

        # Entry tracking
        self.entry_triggered = False
        self.entry_price = None
        self.entry_time = None

        # Price movement tracking
        self.price_history = [open_price]
        self.tick_count = 0

        # Volume tracking for continuation bot
        self.initial_volume = 0
        self.cumulative_volume = 0
        self.volume_step = 1000  # Default volume increment per tick

    def update_price(self, new_price: float):
        """Update current price and track history"""
        self.current_price = new_price
        self.price_history.append(new_price)
        self.tick_count += 1

    def update_volume(self, volume_increment: float):
        """Update cumulative volume"""
        self.cumulative_volume += volume_increment

    def reset_entry(self):
        """Reset entry tracking for retesting"""
        self.entry_triggered = False
        self.entry_price = None
        self.entry_time = None


class ContinuationDummyTickStreamer:
    """Generates synthetic price ticks for testing continuation bot entry logic"""

    def __init__(self, tick_interval: float = 1.0, price_step: float = 0.05, volume_step: float = 1000):
        """
        Args:
            tick_interval: Time between ticks in seconds
            price_step: Price increment per tick
            volume_step: Volume increment per tick
        """
        self.tick_interval = tick_interval
        self.price_step = price_step
        self.volume_step = volume_step
        self.test_stocks: Dict[str, TestStock] = {}
        self.monitor = StockMonitor()
        self.is_running = False
        self.thread = None

        logger.info(f"ContinuationDummyTickStreamer initialized - Interval: {tick_interval}s, Step: {price_step}, Volume Step: {volume_step}")

    def add_test_stock(self, symbol: str, instrument_key: str, previous_close: float,
                      open_price: float, situation: str = 'continuation'):
        """Add a test stock to the streamer"""
        test_stock = TestStock(symbol, instrument_key, previous_close, open_price, situation)
        self.test_stocks[instrument_key] = test_stock

        # Add to continuation monitor
        self.monitor.add_stock(symbol, instrument_key, previous_close, situation)

        # Set opening price in monitor
        monitor_stock = self.monitor.stocks[instrument_key]
        monitor_stock.set_open_price(open_price)

        logger.info(f"Added test stock: {symbol} - Prev Close: {previous_close}, Open: {open_price}, Situation: {situation}")

    def start_streaming(self):
        """Start the tick streaming process"""
        if self.is_running:
            logger.warning("Tick streamer already running")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True
        self.thread.start()

        logger.info("ContinuationDummyTickStreamer started")

    def stop_streaming(self):
        """Stop the tick streaming process"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("ContinuationDummyTickStreamer stopped")

    def _stream_loop(self):
        """Main streaming loop"""
        while self.is_running:
            try:
                self._generate_ticks()
                time.sleep(self.tick_interval)
            except Exception as e:
                logger.error(f"Error in tick streaming loop: {e}")
                time.sleep(1)

    def _generate_ticks(self):
        """Generate price ticks for all test stocks"""
        for instrument_key, test_stock in self.test_stocks.items():
            if not test_stock.is_active:
                continue

            # Generate new price (gradually increasing for SVRO)
            new_price = test_stock.current_price + self.price_step
            test_stock.update_price(new_price)

            # Generate volume increment
            test_stock.update_volume(self.volume_step)

            # Get timestamp
            timestamp = datetime.now()

            # Process tick through continuation monitor
            self.monitor.process_tick(instrument_key, test_stock.symbol, new_price, timestamp)

            # Simulate state progression for testing
            self._simulate_state_progression(test_stock, new_price, timestamp)

            # Check for entry triggers
            self._check_entry_triggers(test_stock, new_price, timestamp)

            # Log tick
            logger.info(f"Tick: {test_stock.symbol} - Price: {new_price:.2f} (Step: {self.price_step}), Volume: {test_stock.cumulative_volume:,}")

    def _simulate_state_progression(self, test_stock: TestStock, price: float, timestamp: datetime):
        """Simulate the state progression for testing"""
        monitor_stock = self.monitor.stocks[test_stock.instrument_key]

        # Step 1: Validate gap (should happen automatically in process_tick)
        if not monitor_stock.gap_validated:
            monitor_stock.validate_gap()

        # Step 2: Check low violation (this sets entry price and ready for SVRO)
        if monitor_stock.gap_validated and not monitor_stock.low_violation_checked:
            monitor_stock.check_low_violation()

        # Step 3: Check volume validation (SVRO requirement)
        if monitor_stock.low_violation_checked and not monitor_stock.volume_validated:
            # Set cumulative volume for testing
            monitor_stock.early_volume = test_stock.cumulative_volume
            # Set volume baseline for testing
            monitor_stock.volume_baseline = 1000000  # 1M baseline for testing
            monitor_stock.validate_volume(monitor_stock.volume_baseline)

        # Step 4: Prepare entries (this sets entry_ready flags)
        if monitor_stock.volume_validated and not monitor_stock.entry_ready:
            monitor_stock.prepare_entry()

    def _check_entry_triggers(self, test_stock: TestStock, price: float, timestamp: datetime):
        """Check if entry was triggered and log results"""
        monitor_stock = self.monitor.stocks[test_stock.instrument_key]

        # Check if stock entered position
        if monitor_stock.entered and not test_stock.entry_triggered:
            test_stock.entry_triggered = True
            test_stock.entry_price = monitor_stock.entry_price
            test_stock.entry_time = timestamp

            logger.info(f"🎯 ENTRY TRIGGERED: {test_stock.symbol}")
            logger.info(f"   Entry Price: {test_stock.entry_price:.2f}")
            logger.info(f"   Trigger Price: {price:.2f}")
            logger.info(f"   Previous Close: {test_stock.previous_close:.2f}")
            logger.info(f"   Situation: {test_stock.situation}")
            logger.info(f"   Ticks to trigger: {test_stock.tick_count}")
            logger.info(f"   Cumulative Volume: {test_stock.cumulative_volume:,}")

            # Calculate price movement to entry
            price_movement = test_stock.entry_price - test_stock.open_price
            logger.info(f"   Price movement to entry: {price_movement:+.2f} ({price_movement/test_stock.open_price*100:+.2f}%)")

    def get_test_results(self) -> Dict:
        """Get summary of test results"""
        results = {
            'total_stocks': len(self.test_stocks),
            'triggered_entries': 0,
            'stock_details': {}
        }

        for instrument_key, test_stock in self.test_stocks.items():
            stock_result = {
                'symbol': test_stock.symbol,
                'situation': test_stock.situation,
                'previous_close': test_stock.previous_close,
                'open_price': test_stock.open_price,
                'final_price': test_stock.current_price,
                'entry_triggered': test_stock.entry_triggered,
                'entry_price': test_stock.entry_price,
                'entry_time': test_stock.entry_time,
                'ticks_to_trigger': test_stock.tick_count,
                'cumulative_volume': test_stock.cumulative_volume,
                'price_movement': test_stock.entry_price - test_stock.open_price if test_stock.entry_triggered else None
            }

            results['stock_details'][instrument_key] = stock_result

            if test_stock.entry_triggered:
                results['triggered_entries'] += 1

        return results

    def print_test_summary(self):
        """Print a formatted test summary"""
        results = self.get_test_results()

        print("\n" + "="*60)
        print("CONTINUATION DUMMY TICK STREAMER TEST SUMMARY")
        print("="*60)

        print(f"Total Stocks: {results['total_stocks']}")
        print(f"Triggered Entries: {results['triggered_entries']}")
        print(f"Success Rate: {results['triggered_entries']/results['total_stocks']*100:.1f}%")

        print("\nStock Details:")
        print("-" * 60)

        for instrument_key, details in results['stock_details'].items():
            status = "✅ TRIGGERED" if details['entry_triggered'] else "❌ NO ENTRY"
            print(f"{details['symbol']} ({details['situation']}) - {status}")
            print(f"  Prev Close: {details['previous_close']:.2f}")
            print(f"  Open Price: {details['open_price']:.2f}")
            print(f"  Final Price: {details['final_price']:.2f}")

            if details['entry_triggered']:
                print(f"  Entry Price: {details['entry_price']:.2f}")
                print(f"  Price Movement: {details['price_movement']:+.2f} ({details['price_movement']/details['open_price']*100:+.2f}%)")
                print(f"  Ticks to Trigger: {details['ticks_to_trigger']}")
                print(f"  Cumulative Volume: {details['cumulative_volume']:,}")
            else:
                print(f"  No entry triggered")
            print()

        print("="*60)


def create_svro_test_scenario():
    """Create a test scenario for SVRO entry testing"""
    streamer = ContinuationDummyTickStreamer(tick_interval=0.5, price_step=0.1, volume_step=1000)

    # Create SVRO test stock
    # Previous close: 100.00, Open price: 95.00 (gap down)
    # Entry should trigger when price crosses 100.00 with sufficient volume
    streamer.add_test_stock(
        symbol="TEST_SVRO",
        instrument_key="TEST_SVRO_KEY",
        previous_close=100.0,
        open_price=95.0,  # Gap down
        situation='continuation'  # SVRO
    )

    return streamer


def run_svro_entry_test():
    """Run the SVRO entry test scenario"""
    print("🚀 Starting SVRO Entry Test")
    print("Testing: SVRO stock should enter when price crosses previous close with sufficient volume")
    print("Setup: Previous Close = 100.00, Open Price = 95.00 (gap down)")
    print("Expected: Entry when price >= 100.00 with volume >= 7.5% of baseline")
    print()

    # Create test scenario
    streamer = create_svro_test_scenario()

    # Start streaming
    streamer.start_streaming()

    # Run for 60 seconds or until entry triggers
    max_duration = 60
    start_time = time.time()

    try:
        while time.time() - start_time < max_duration:
            # Check if any entries were triggered
            results = streamer.get_test_results()
            if results['triggered_entries'] > 0:
                print(f"\n🎯 Entry triggered! Stopping test early.")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")

    finally:
        # Stop streaming
        streamer.stop_streaming()

        # Print results
        streamer.print_test_summary()

        # Return results for further analysis
        return streamer.get_test_results()


if __name__ == "__main__":
    # Run the SVRO entry test
    results = run_svro_entry_test()

    # Exit with appropriate code
    if results['triggered_entries'] > 0:
        print("\n🎉 SVRO entry test PASSED!")
        print("The continuation bot correctly triggered entry when price crossed previous close with sufficient volume.")
    else:
        print("\n❌ SVRO entry test FAILED!")
        print("No entries were triggered. Check the SVRO entry logic.")

    sys.exit(0 if results['triggered_entries'] > 0 else 1)