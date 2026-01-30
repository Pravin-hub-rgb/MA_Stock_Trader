#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVRO Test Runner - Monolithic Continuation Bot Testing
Uses the exact continuation bot architecture with simulated SVRO data
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

# Import continuation bot components (exact same as live trading)
from src.trading.live_trading.continuation_stock_monitor import StockMonitor
from src.trading.live_trading.rule_engine import RuleEngine
from src.trading.live_trading.selection_engine import SelectionEngine
from src.trading.live_trading.paper_trader import PaperTrader
from src.trading.live_trading.volume_profile import volume_profile_calculator
from src.trading.live_trading.continuation_modules.continuation_timing_module import ContinuationTimingManager
from config import MARKET_OPEN, ENTRY_TIME, PREP_START

# Import our SVRO dummy tick streamer
from Test_Environment.dummy_svro_tick_streamer import DummySVROTickStreamer

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('svro_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('SVROTest')


class SVROTest:
    """SVRO test runner using exact continuation bot architecture"""

    def __init__(self):
        self.logger = logger
        self.monitor = None
        self.rule_engine = RuleEngine()
        self.selection_engine = SelectionEngine()
        self.paper_trader = PaperTrader()
        self.streamer = None
        self.is_running = False
        self.test_results = []
        self.test_start_time = None

        self.logger.info("SVRO Test Environment initialized")

    def setup_test_environment(self):
        """Setup the SVRO test environment with exact continuation bot architecture"""
        self.logger.info("Setting up SVRO test environment with exact continuation bot architecture...")

        # Create SVRO dummy tick streamer - this handles both streaming and monitoring
        self.streamer = DummySVROTickStreamer(
            tick_interval=0.1,  # Fast ticks for testing
            price_step=0.1,     # Small price steps
            volume_step=5000.0  # Volume steps for SVRO testing
        )

        # Add SVRO test stocks to streamer (this also adds them to the monitor)
        self.streamer.add_test_stock(
            symbol="TEST_SVRO",
            instrument_key="TEST_SVRO_KEY",
            previous_close=100.0,
            open_price=102.0,  # Gap up 2% - SVRO requirement
            situation="continuation",
            volume_baseline=1000000.0  # 1M volume baseline
        )

        self.streamer.add_test_stock(
            symbol="TEST_SVRO2",
            instrument_key="TEST_SVRO2_KEY",
            previous_close=50.0,
            open_price=51.0,  # Gap up 2%
            situation="continuation",
            volume_baseline=500000.0  # 500K volume baseline
        )

        # Get the monitor from the streamer (exact continuation bot architecture)
        self.monitor = self.streamer.monitor

        # Setup SVRO state progression simulation
        self._setup_svro_state_progression()

        self.logger.info("SVRO test environment setup complete")

    def _setup_svro_state_progression(self):
        """Setup proper SVRO state progression simulation"""
        # Simulate the exact sequence that happens in real continuation bot
        
        # Step 1: Validate gaps for both stocks (SVRO requires gap up)
        for stock in self.monitor.stocks.values():
            if not stock.gap_validated:
                stock.validate_gap()
        
        # Step 2: Check low violations (SVRO requirement)
        for stock in self.monitor.stocks.values():
            if stock.gap_validated and not stock.low_violation_checked:
                stock.check_low_violation()
        
        # Step 3: Check volume validations (SVRO specific - 7.5% threshold)
        for stock in self.monitor.stocks.values():
            if stock.low_violation_checked and not stock.volume_validated:
                # Simulate volume buildup to meet SVRO threshold
                required_volume = stock.volume_baseline * 0.075
                stock.early_volume = required_volume + 10000  # Just above threshold
                stock.volume_validated = True
                self.logger.info(f"[{stock.symbol}] SVRO Volume validated: {stock.early_volume/stock.volume_baseline*100:.1f}% >= 7.5%")
        
        # Step 4: Prepare entries (set entry high and SL)
        self.monitor.prepare_entries()
        
        # Step 5: Mark stocks as ready for SVRO testing
        for stock in self.monitor.stocks.values():
            if stock.volume_validated and stock.gap_validated and stock.low_violation_checked:
                stock.entry_ready = True
                self.logger.info(f"[{stock.symbol}] SVRO Entry ready - High: {stock.entry_high:.2f}, SL: {stock.entry_sl:.2f}")

    def start_test(self):
        """Start the SVRO test"""
        if self.is_running:
            self.logger.warning("SVRO test already running")
            return
            
        self.is_running = True
        self.test_start_time = time.time()
        
        # Start the SVRO dummy tick streamer
        self.streamer.start_streaming()
        
        # Start monitoring for SVRO entries
        self._start_monitoring()
        
        self.logger.info("SVRO test started")

    def stop_test(self):
        """Stop the test"""
        self.is_running = False
        
        if self.streamer:
            self.streamer.stop_streaming()
        
        self.logger.info("SVRO test stopped")

    def _start_monitoring(self):
        """Start monitoring for SVRO entries using real continuation bot logic"""
        def monitor_loop():
            while self.is_running:
                try:
                    # Check for SVRO entries using real continuation bot logic
                    self._check_svro_entries()
                    time.sleep(0.1)  # Check every 100ms
                except Exception as e:
                    self.logger.error(f"Error in SVRO monitoring loop: {e}")
                    time.sleep(1)

        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

    def _check_svro_entries(self):
        """Check for SVRO entries using real continuation bot logic"""
        # Check for entry signals using continuation bot logic
        entry_signals = self.monitor.check_entry_signals()
        
        # Process any entry signals
        for stock in entry_signals:
            if not any(r['symbol'] == stock.symbol for r in self.test_results):
                # Trigger entry using continuation bot logic
                stock.enter_position(stock.current_price, datetime.now())
                
                # Record SVRO entry
                result = {
                    'symbol': stock.symbol,
                    'situation': stock.situation,
                    'entry_price': stock.entry_price,
                    'entry_time': stock.entry_time,
                    'entry_high': stock.entry_high,
                    'entry_sl': stock.entry_sl,
                    'trigger_price': stock.current_price,
                    'ticks_to_trigger': self.streamer.test_stocks[stock.instrument_key].tick_count if stock.instrument_key in self.streamer.test_stocks else 0,
                    'test_duration': time.time() - self.test_start_time,
                    'gap_pct': ((stock.open_price - stock.previous_close) / stock.previous_close * 100),
                    'volume_pct': (stock.early_volume / stock.volume_baseline * 100)
                }
                
                self.test_results.append(result)
                
                self.logger.info(f"🎯 SVRO ENTRY TRIGGERED: {stock.symbol}")
                self.logger.info(f"   Situation: {stock.situation}")
                self.logger.info(f"   Entry Price: {stock.entry_price:.2f}")
                self.logger.info(f"   Trigger Price: {stock.current_price:.2f}")
                self.logger.info(f"   Entry High: {stock.entry_high:.2f}")
                self.logger.info(f"   Entry SL: {stock.entry_sl:.2f}")
                self.logger.info(f"   Gap: {result['gap_pct']:+.1f}%")
                self.logger.info(f"   Volume: {result['volume_pct']:.1f}% of baseline")
                self.logger.info(f"   Ticks to trigger: {result['ticks_to_trigger']}")
                self.logger.info(f"   Test duration: {result['test_duration']:.1f}s")

    def run_test(self):
        """Run the complete SVRO test"""
        print("🚀 Starting SVRO Test")
        print("Testing: Exact continuation bot architecture with SVRO entry system")
        print("Setup: SVRO stocks with gap up, volume validation, and entry triggers")
        print()
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Start test
            self.start_test()
            
            # Wait for entries
            print("Monitoring for SVRO entries...")
            start_time = time.time()
            max_test_duration = 120  # 2 minutes max
            
            while self.is_running and (time.time() - start_time) < max_test_duration:
                # Check if we have entries for both stocks
                if len(self.test_results) >= 2:
                    self.logger.info("Both SVRO test stocks have entered - stopping test")
                    break
                
                time.sleep(0.5)
            
            # Stop test
            self.stop_test()
            
            # Print results
            self._print_results()
            
            return len(self.test_results) >= 2
            
        except Exception as e:
            self.logger.error(f"SVRO test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _print_results(self):
        """Print SVRO test results"""
        print("\n" + "="*60)
        print("SVRO TEST RESULTS")
        print("="*60)
        
        if not self.test_results:
            print("❌ No SVRO entries triggered")
            
            # Print current stock status for debugging
            print("\nCurrent Stock Status:")
            for stock in self.monitor.stocks.values():
                print(f"  {stock.symbol} ({stock.situation}):")
                print(f"    Gap Validated: {stock.gap_validated}")
                print(f"    Low Violation Checked: {stock.low_violation_checked}")
                print(f"    Volume Validated: {stock.volume_validated}")
                print(f"    Entry Ready: {stock.entry_ready}")
                print(f"    Entered: {stock.entered}")
                print(f"    Current Price: {stock.current_price}")
                print(f"    Open Price: {stock.open_price}")
                print(f"    Previous Close: {stock.previous_close}")
                print(f"    Entry High: {stock.entry_high}")
                print(f"    Entry SL: {stock.entry_sl}")
                print(f"    Volume: {stock.early_volume:,.0f} ({stock.early_volume/stock.volume_baseline*100:.1f}%)")
                print(f"    Volume Baseline: {stock.volume_baseline:,.0f}")
            return
        
        for result in self.test_results:
            print(f"\n{result['symbol']} ({result['situation']}) - ✅ SVRO TRIGGERED")
            print(f"  Entry Price: {result['entry_price']:.2f}")
            print(f"  Entry High: {result['entry_high']:.2f}")
            print(f"  Entry SL: {result['entry_sl']:.2f}")
            print(f"  Gap: {result['gap_pct']:+.1f}%")
            print(f"  Volume: {result['volume_pct']:.1f}% of baseline")
            print(f"  Ticks to trigger: {result['ticks_to_trigger']}")
            print(f"  Test duration: {result['test_duration']:.1f}s")
            
            # Calculate price movement
            # Find the stock by instrument_key instead of symbol
            stock = None
            for key, s in self.monitor.stocks.items():
                if s.symbol == result['symbol']:
                    stock = s
                    break
            
            if stock:
                open_price = stock.open_price
                price_movement = result['entry_price'] - open_price
                movement_pct = (price_movement / open_price) * 100
                print(f"  Price movement: {price_movement:+.2f} ({movement_pct:+.2f}%)")
            else:
                print(f"  Price movement: Unable to calculate (stock not found)")
        
        print(f"\nTotal SVRO Entries: {len(self.test_results)}/2")
        
        if len(self.test_results) >= 2:
            print("🎉 SVRO TEST PASSED!")
            print("Both SVRO stocks entered successfully with proper gap and volume validation")
        else:
            print("❌ SVRO TEST FAILED!")
            print("Not all expected SVRO entries were triggered")

    def get_test_summary(self):
        """Get SVRO test summary"""
        return {
            'total_stocks': len(self.monitor.stocks),
            'qualified_stocks': len([s for s in self.monitor.stocks.values() if s.gap_validated and s.low_violation_checked and s.volume_validated]),
            'selected_stocks': len(self.test_results),
            'entered_positions': len([s for s in self.monitor.stocks.values() if s.entered]),
            'test_duration': time.time() - self.test_start_time if self.test_start_time else 0
        }


def main():
    """Main SVRO test runner"""
    test = SVROTest()
    success = test.run_test()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)