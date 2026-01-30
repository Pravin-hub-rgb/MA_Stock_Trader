#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Reversal Bot Test
Tests the exact reversal bot architecture with proper state progression simulation
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the exact reversal bot modules
from Test_Environment.reversal_stock_monitor import ReversalStockMonitor
from Test_Environment.reversal_modules.state_machine import StockState
from Test_Environment.reversal_modules.tick_processor import ReversalTickProcessor
from Test_Environment.dummy_tick_streamer import DummyTickStreamer


def setup_logging():
    """Setup logging for the comprehensive test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('comprehensive_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('ComprehensiveTest')


class ComprehensiveReversalTest:
    """Comprehensive test using exact reversal bot architecture with proper simulation"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.monitor = None
        self.streamer = None
        self.is_running = False
        self.test_results = []
        self.test_start_time = None
        
        self.logger.info("Comprehensive Reversal Test initialized")
    
    def setup_test_environment(self):
        """Setup the exact reversal bot architecture with proper test simulation"""
        self.logger.info("Setting up comprehensive reversal bot test...")
        
        # Create dummy tick streamer (simulation only) - this will handle both streaming and monitoring
        self.streamer = DummyTickStreamer(
            tick_interval=0.1,
            price_step=0.1
        )
        
        # Add test stocks to streamer (this also adds them to the monitor)
        self.streamer.add_test_stock(
            symbol="TEST_OOPS",
            instrument_key="TEST_OOPS_KEY",
            previous_close=100.0,
            open_price=95.0,  # Gap down
            situation="reversal_s2"  # OOPS
        )
        
        self.streamer.add_test_stock(
            symbol="TEST_SS",
            instrument_key="TEST_SS_KEY",
            previous_close=100.0,
            open_price=102.0,  # Gap up
            situation="reversal_s1"  # Strong Start
        )
        
        # Get the monitor from the streamer
        self.monitor = self.streamer.monitor
        
        # Setup proper state progression simulation
        self._setup_state_progression()
        
        self.logger.info("Comprehensive test setup complete")
    
    def _add_test_stocks(self):
        """Add test stocks to the reversal monitor"""
        # OOPS stock (gap down)
        self.monitor.add_stock(
            symbol="TEST_OOPS",
            instrument_key="TEST_OOPS_KEY",
            previous_close=100.0,
            situation="reversal_s2"  # OOPS
        )
        
        # Strong Start stock (gap up)
        self.monitor.add_stock(
            symbol="TEST_SS",
            instrument_key="TEST_SS_KEY",
            previous_close=100.0,
            situation="reversal_s1"  # Strong Start
        )
        
        # Set opening prices manually for testing
        if "TEST_OOPS_KEY" in self.monitor.stocks:
            self.monitor.stocks["TEST_OOPS_KEY"].set_open_price(95.0)  # Gap down
        if "TEST_SS_KEY" in self.monitor.stocks:
            self.monitor.stocks["TEST_SS_KEY"].set_open_price(102.0)  # Gap up
        
        self.logger.info("Added test stocks: TEST_OOPS (OOPS), TEST_SS (Strong Start)")
    
    def _setup_state_progression(self):
        """Setup proper state progression simulation"""
        # Simulate the exact sequence that happens in real reversal bot
        
        # Step 1: Validate gaps for both stocks
        for stock in self.monitor.stocks.values():
            if not stock.gap_validated:
                stock.validate_gap()
        
        # Step 2: Check low violations (this sets entry prices for OOPS)
        for stock in self.monitor.stocks.values():
            if stock.gap_validated and not stock.low_violation_checked:
                stock.check_low_violation()
        
        # Step 3: Prepare entries (this sets entry_ready flags)
        self.monitor.prepare_entries()
        
        # Step 4: Transition to monitoring_entry state
        for stock in self.monitor.stocks.values():
            if stock.low_violation_checked and not stock.entered:
                if not stock.is_in_state('monitoring_entry'):
                    stock._transition_to(StockState.MONITORING_ENTRY, "test setup - ready for entry")
                    self.logger.info(f"[{stock.symbol}] Transitioned to MONITORING_ENTRY")
    
    def start_test(self):
        """Start the comprehensive test"""
        if self.is_running:
            self.logger.warning("Test already running")
            return
            
        self.is_running = True
        self.test_start_time = time.time()
        
        # Start the dummy tick streamer
        self.streamer.start_streaming()
        
        # Start monitoring for entries
        self._start_monitoring()
        
        self.logger.info("Comprehensive reversal test started")
    
    def stop_test(self):
        """Stop the test"""
        self.is_running = False
        
        if self.streamer:
            self.streamer.stop_streaming()
        
        self.logger.info("Comprehensive reversal test stopped")
    
    def _start_monitoring(self):
        """Start monitoring for entries using real reversal bot logic"""
        def monitor_loop():
            while self.is_running:
                try:
                    # Check for entries using real reversal bot logic
                    self._check_for_entries()
                    time.sleep(0.1)  # Check every 100ms
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
    
    def _check_for_entries(self):
        """Check for entries using real reversal bot logic"""
        # Get current stock states from monitor
        for stock_symbol in ['TEST_OOPS', 'TEST_SS']:
            if stock_symbol in self.monitor.stocks:
                stock = self.monitor.stocks[stock_symbol]
                
                # Check if stock has entered
                if stock.entered and not any(r['symbol'] == stock_symbol for r in self.test_results):
                    # Record entry
                    result = {
                        'symbol': stock_symbol,
                        'situation': stock.situation,
                        'entry_price': stock.entry_price,
                        'entry_time': stock.entry_time,
                        'entry_high': stock.entry_high,
                        'entry_sl': stock.entry_sl,
                        'trigger_price': stock.entry_price,
                        'ticks_to_trigger': len(self.streamer.price_history.get(stock_symbol, [])),
                        'test_duration': time.time() - self.test_start_time
                    }
                    
                    self.test_results.append(result)
                    
                    self.logger.info(f"🎯 ENTRY TRIGGERED: {stock_symbol}")
                    self.logger.info(f"   Situation: {stock.situation}")
                    self.logger.info(f"   Entry Price: {stock.entry_price:.2f}")
                    self.logger.info(f"   Entry High: {stock.entry_high:.2f}")
                    self.logger.info(f"   Entry SL: {stock.entry_sl:.2f}")
                    self.logger.info(f"   Ticks to trigger: {result['ticks_to_trigger']}")
                    self.logger.info(f"   Test duration: {result['test_duration']:.1f}s")
    
    def run_test(self):
        """Run the complete comprehensive test"""
        print("🚀 Starting Comprehensive Reversal Test")
        print("Testing: Real reversal bot architecture with proper state progression")
        print("Setup: OOPS and Strong Start stocks with exact bot logic")
        print()
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Start test
            self.start_test()
            
            # Wait for entries
            print("Monitoring for entries...")
            start_time = time.time()
            max_test_duration = 180  # 3 minutes max
            
            while self.is_running and (time.time() - start_time) < max_test_duration:
                # Check if we have entries for both stocks
                if len(self.test_results) >= 2:
                    self.logger.info("Both test stocks have entered - stopping test")
                    break
                
                time.sleep(0.5)
            
            # Stop test
            self.stop_test()
            
            # Print results
            self._print_results()
            
            return len(self.test_results) >= 2
            
        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _print_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("COMPREHENSIVE REVERSAL TEST RESULTS")
        print("="*60)
        
        if not self.test_results:
            print("❌ No entries triggered")
            
            # Print current stock status for debugging
            print("\nCurrent Stock Status:")
            for stock in self.monitor.stocks.values():
                print(f"  {stock.symbol} ({stock.situation}):")
                print(f"    State: {stock.state.value}")
                print(f"    Gap Validated: {stock.gap_validated}")
                print(f"    Low Violation Checked: {stock.low_violation_checked}")
                print(f"    Entry Ready: {stock.entry_ready}")
                print(f"    Entered: {stock.entered}")
                print(f"    Current Price: {stock.current_price}")
                print(f"    Open Price: {stock.open_price}")
                print(f"    Previous Close: {stock.previous_close}")
                if stock.situation == 'reversal_s2':
                    print(f"    OOPS Trigger Price: {stock.previous_close}")
                else:
                    print(f"    Strong Start High: {stock.daily_high}")
            return
        
        for result in self.test_results:
            print(f"\n{result['symbol']} ({result['situation']}) - ✅ TRIGGERED")
            print(f"  Entry Price: {result['entry_price']:.2f}")
            print(f"  Entry High: {result['entry_high']:.2f}")
            print(f"  Entry SL: {result['entry_sl']:.2f}")
            print(f"  Ticks to trigger: {result['ticks_to_trigger']}")
            print(f"  Test duration: {result['test_duration']:.1f}s")
            
            if result['situation'] == 'reversal_s2':  # OOPS
                price_movement = result['entry_price'] - 95.0  # OOPS open price
                movement_pct = (price_movement / 95.0) * 100
                print(f"  Price movement: {price_movement:+.2f} ({movement_pct:+.2f}%)")
            else:  # Strong Start
                price_movement = result['entry_price'] - 102.0  # SS open price
                movement_pct = (price_movement / 102.0) * 100
                print(f"  Price movement: {price_movement:+.2f} ({movement_pct:+.2f}%)")
        
        print(f"\nTotal Entries: {len(self.test_results)}/2")
        
        if len(self.test_results) >= 2:
            print("🎉 COMPREHENSIVE REVERSAL TEST PASSED!")
            print("Both OOPS and Strong Start entries triggered correctly")
        else:
            print("❌ COMPREHENSIVE REVERSAL TEST FAILED!")
            print("Not all expected entries were triggered")


def main():
    """Main test runner"""
    test = ComprehensiveReversalTest()
    success = test.run_test()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)