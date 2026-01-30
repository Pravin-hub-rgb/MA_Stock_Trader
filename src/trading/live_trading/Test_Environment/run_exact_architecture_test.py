#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exact Architecture Test Runner
Uses the real reversal bot files with simulated data streamer
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
from Test_Environment.reversal_modules.subscription_manager import SubscriptionManager
from Test_Environment.dummy_tick_streamer import DummyTickStreamer


def setup_logging():
    """Setup logging for the exact architecture test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('exact_architecture_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('ExactArchitectureTest')


class ExactArchitectureTest:
    """Test runner using exact reversal bot architecture"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.monitor = None
        self.streamer = None
        self.is_running = False
        self.test_results = []
        
        self.logger.info("Exact Architecture Test initialized")
    
    def setup_test_environment(self):
        """Setup the exact reversal bot architecture"""
        self.logger.info("Setting up exact reversal bot architecture...")
        
        # Create reversal stock monitor (exact same as real bot)
        self.monitor = ReversalStockMonitor()
        
        # Create dummy tick streamer (simulation only)
        self.streamer = DummyTickStreamer(
            tick_interval=0.1,
            price_step=0.1
        )
        
        # Add test stocks to monitor
        self._add_test_stocks()
        
        self.logger.info("Exact architecture setup complete")
    
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
    
    def start_test(self):
        """Start the exact architecture test"""
        if self.is_running:
            self.logger.warning("Test already running")
            return
            
        self.is_running = True
        
        # Start the dummy tick streamer
        self.streamer.start_streaming()
        
        # Start monitoring for entries
        self._start_monitoring()
        
        self.logger.info("Exact architecture test started")
    
    def stop_test(self):
        """Stop the test"""
        self.is_running = False
        
        if self.streamer:
            self.streamer.stop_streaming()
        
        self.logger.info("Exact architecture test stopped")
    
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
                        'trigger_price': stock.entry_price,  # For this test
                        'ticks_to_trigger': len(self.streamer.price_history.get(stock_symbol, []))
                    }
                    
                    self.test_results.append(result)
                    
                    self.logger.info(f"🎯 ENTRY TRIGGERED: {stock_symbol}")
                    self.logger.info(f"   Situation: {stock.situation}")
                    self.logger.info(f"   Entry Price: {stock.entry_price:.2f}")
                    self.logger.info(f"   Entry High: {stock.entry_high:.2f}")
                    self.logger.info(f"   Entry SL: {stock.entry_sl:.2f}")
                    self.logger.info(f"   Ticks to trigger: {result['ticks_to_trigger']}")
    
    def run_test(self):
        """Run the complete exact architecture test"""
        print("🚀 Starting Exact Architecture Test")
        print("Testing: Real reversal bot architecture with simulated data")
        print("Setup: OOPS and Strong Start stocks with real bot logic")
        print()
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Start test
            self.start_test()
            
            # Wait for entries
            print("Monitoring for entries...")
            start_time = time.time()
            max_test_duration = 120  # 2 minutes max
            
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
        """Print test results"""
        print("\n" + "="*60)
        print("EXACT ARCHITECTURE TEST RESULTS")
        print("="*60)
        
        if not self.test_results:
            print("❌ No entries triggered")
            return
        
        for result in self.test_results:
            print(f"\n{result['symbol']} ({result['situation']}) - ✅ TRIGGERED")
            print(f"  Entry Price: {result['entry_price']:.2f}")
            print(f"  Entry High: {result['entry_high']:.2f}")
            print(f"  Entry SL: {result['entry_sl']:.2f}")
            print(f"  Ticks to trigger: {result['ticks_to_trigger']}")
            
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
            print("🎉 EXACT ARCHITECTURE TEST PASSED!")
            print("Both OOPS and Strong Start entries triggered correctly")
        else:
            print("❌ EXACT ARCHITECTURE TEST FAILED!")
            print("Not all expected entries were triggered")


def main():
    """Main test runner"""
    test = ExactArchitectureTest()
    success = test.run_test()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)