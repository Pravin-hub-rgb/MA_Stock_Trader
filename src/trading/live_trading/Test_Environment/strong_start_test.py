#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strong Start Entry Test
Tests Strong Start entry logic without real-time dependencies
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

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strong_start_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('StrongStartTest')


class StrongStartTestStock:
    """Represents a Strong Start test stock"""
    
    def __init__(self, symbol: str, instrument_key: str, previous_close: float, 
                 open_price: float):
        self.symbol = symbol
        self.instrument_key = instrument_key
        self.previous_close = previous_close
        self.open_price = open_price
        self.situation = 'reversal_s1'  # Strong Start
        self.current_price = open_price
        self.is_active = True
        
        # Entry tracking
        self.entry_triggered = False
        self.entry_price = None
        self.entry_time = None
        
        # Price movement tracking
        self.price_history = [open_price]
        self.tick_count = 0
        
        # Strong Start specific tracking
        self.daily_high = open_price
        self.daily_low = open_price
        self.entry_high = None
        self.entry_sl = None
        self.entry_ready = False
        self.low_violation_checked = False
        self.monitoring_period_complete = False
        
    def update_price(self, new_price: float):
        """Update current price and track high/low"""
        self.current_price = new_price
        self.price_history.append(new_price)
        self.tick_count += 1
        
        # Update daily high/low
        self.daily_high = max(self.daily_high, new_price)
        self.daily_low = min(self.daily_low, new_price)
        
    def check_low_violation(self) -> bool:
        """Check if low dropped below 1% of open price"""
        if self.open_price is None:
            return False

        threshold = self.open_price * (1 - 0.01)  # 1% below open

        if self.daily_low < threshold:
            logger.info(f"[{self.symbol}] Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
            return False

        self.low_violation_checked = True
        logger.info(f"[{self.symbol}] Low violation check passed - No violation detected")
        return True
        
    def set_entry_levels(self):
        """Set entry levels at entry time"""
        if self.low_violation_checked and not self.monitoring_period_complete:
            self.entry_high = self.daily_high
            self.entry_sl = self.entry_high * (1 - 0.04)  # 4% SL
            self.entry_ready = True
            self.monitoring_period_complete = True
            
            logger.info(f"[{self.symbol}] Entry levels set - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f}")
            return True
        
        return False
        
    def check_entry_signal(self, price: float) -> bool:
        """Check if price has broken above the current high"""
        if not self.entry_ready or self.entry_triggered:
            return False

        # Strong Start: Enter when price crosses above current high
        return price >= self.entry_high
        
    def enter_position(self, price: float, timestamp: datetime):
        """Enter position at market"""
        self.entry_price = price
        self.entry_time = timestamp
        self.entry_triggered = True

        logger.info(f"[{self.symbol}] STRONG START ENTRY at {price:.2f} - Triggered by price crossing high {self.entry_high:.2f}")


class StrongStartTestRunner:
    """Runs Strong Start entry test"""
    
    def __init__(self, tick_interval: float = 0.5, price_step: float = 0.1):
        self.tick_interval = tick_interval
        self.price_step = price_step
        self.test_stock = None
        self.is_running = False
        self.thread = None
        self.monitoring_ticks = 0
        self.max_monitoring_ticks = 60  # Simulate 60 ticks of monitoring
        
        logger.info(f"Strong Start Test initialized - Interval: {tick_interval}s, Step: {price_step}")
    
    def setup_test_stock(self):
        """Setup Strong Start test stock"""
        self.test_stock = StrongStartTestStock(
            symbol="TEST_SS",
            instrument_key="TEST_SS_KEY", 
            previous_close=100.0,
            open_price=102.0  # Gap up setup
        )
        
        logger.info(f"Setup Strong Start stock: {self.test_stock.symbol}")
        logger.info(f"  Previous Close: {self.test_stock.previous_close}")
        logger.info(f"  Open Price: {self.test_stock.open_price} (Gap up: +{((102.0-100.0)/100.0)*100:.1f}%)")
        logger.info(f"  Situation: {self.test_stock.situation}")
    
    def start_test(self):
        """Start the Strong Start test"""
        if self.is_running:
            logger.warning("Test already running")
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._test_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Strong Start test started")
        
    def stop_test(self):
        """Stop the test"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Strong Start test stopped")
    
    def _test_loop(self):
        """Main test loop"""
        while self.is_running:
            try:
                self._simulate_tick()
                time.sleep(self.tick_interval)
            except Exception as e:
                logger.error(f"Error in test loop: {e}")
                time.sleep(1)
    
    def _simulate_tick(self):
        """Simulate a single tick"""
        if not self.test_stock:
            return
            
        # Phase 1: Monitoring Period (build daily high)
        if self.monitoring_ticks < self.max_monitoring_ticks:
            self._simulate_monitoring_tick()
        # Phase 2: Entry Time (set entry levels)
        elif self.monitoring_ticks == self.max_monitoring_ticks:
            self._simulate_entry_time()
        # Phase 3: Entry Trigger (wait for price to cross high)
        else:
            self._simulate_entry_trigger_tick()
            
        self.monitoring_ticks += 1
    
    def _simulate_monitoring_tick(self):
        """Simulate tick during monitoring period"""
        # Create price movement that builds a daily high
        # Pattern: gradual up, small pullback, new high, consolidation
        
        base_movement = self.monitoring_ticks * 0.05  # Gradual upward drift
        
        # Add some volatility
        if self.monitoring_ticks % 10 == 0:
            # Every 10 ticks, add a small pullback
            price_change = -0.1
        elif self.monitoring_ticks % 15 == 0:
            # Every 15 ticks, add a bigger move up
            price_change = 0.3
        else:
            price_change = 0.05
            
        new_price = self.test_stock.current_price + price_change
        self.test_stock.update_price(new_price)
        
        # Check low violation during monitoring
        if not self.test_stock.low_violation_checked:
            self.test_stock.check_low_violation()
        
        logger.info(f"Monitoring Tick {self.monitoring_ticks+1:2d}: Price {new_price:6.2f} | High: {self.test_stock.daily_high:6.2f} | Low: {self.test_stock.daily_low:6.2f}")
    
    def _simulate_entry_time(self):
        """Simulate entry time logic"""
        logger.info("=" * 60)
        logger.info("ENTRY TIME - Setting entry levels")
        logger.info("=" * 60)
        
        # Set entry levels
        self.test_stock.set_entry_levels()
        
        # Verify no low violation
        if self.test_stock.low_violation_checked:
            logger.info(f"[{self.test_stock.symbol}] ✅ No low violation detected")
        else:
            logger.info(f"[{self.test_stock.symbol}] ❌ Low violation detected - would not enter")
        
        logger.info(f"Daily High reached: {self.test_stock.daily_high:.2f}")
        logger.info(f"Entry High set to: {self.test_stock.entry_high:.2f}")
        logger.info(f"Entry SL set to: {self.test_stock.entry_sl:.2f}")
        logger.info(f"Entry Ready: {self.test_stock.entry_ready}")
    
    def _simulate_entry_trigger_tick(self):
        """Simulate ticks waiting for entry trigger"""
        # Continue price movement above the high to trigger entry
        new_price = self.test_stock.current_price + self.price_step
        self.test_stock.update_price(new_price)
        
        # Check entry signal
        if self.test_stock.check_entry_signal(new_price):
            self.test_stock.enter_position(new_price, datetime.now())
            logger.info(f"🎯 STRONG START ENTRY TRIGGERED!")
            logger.info(f"   Entry Price: {self.test_stock.entry_price:.2f}")
            logger.info(f"   Trigger Price: {new_price:.2f}")
            logger.info(f"   Entry High: {self.test_stock.entry_high:.2f}")
            logger.info(f"   Ticks to trigger: {self.monitoring_ticks + 1}")
            
            # Stop test after entry
            self.is_running = False
        else:
            logger.info(f"Entry Tick {self.monitoring_ticks-self.max_monitoring_ticks:2d}: Price {new_price:6.2f} | Need: {self.test_stock.entry_high:6.2f} | Waiting...")


def run_strong_start_test():
    """Run the Strong Start entry test"""
    print("🚀 Starting Strong Start Entry Test")
    print("Testing: Strong Start stock should enter when price crosses daily high")
    print("Setup: Previous Close = 100.00, Open Price = 102.00 (gap up)")
    print("Expected: Entry when price >= daily high (built during monitoring)")
    print()
    
    # Create test runner
    test_runner = StrongStartTestRunner(tick_interval=0.1, price_step=0.1)
    
    # Setup and run test
    test_runner.setup_test_stock()
    test_runner.start_test()
    
    # Wait for completion
    try:
        while test_runner.is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    finally:
        test_runner.stop_test()
    
    # Print results
    print("\n" + "="*60)
    print("STRONG START TEST RESULTS")
    print("="*60)
    
    if test_runner.test_stock.entry_triggered:
        print("✅ STRONG START TEST PASSED!")
        print(f"   Entry Price: {test_runner.test_stock.entry_price:.2f}")
        print(f"   Daily High: {test_runner.test_stock.entry_high:.2f}")
        print(f"   Entry SL: {test_runner.test_stock.entry_sl:.2f}")
        print(f"   Ticks to trigger: {test_runner.monitoring_ticks}")
        
        price_movement = test_runner.test_stock.entry_price - test_runner.test_stock.open_price
        movement_pct = (price_movement / test_runner.test_stock.open_price) * 100
        print(f"   Price movement: {price_movement:+.2f} ({movement_pct:+.2f}%)")
    else:
        print("❌ STRONG START TEST FAILED!")
        print("   No entry was triggered")
    
    return test_runner.test_stock.entry_triggered


if __name__ == "__main__":
    success = run_strong_start_test()
    sys.exit(0 if success else 1)