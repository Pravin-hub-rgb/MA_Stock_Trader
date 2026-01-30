#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dummy SVRO Tick Streamer for Testing Continuation Bot
Creates a controlled environment to test SVRO entry triggers with synthetic price and volume data
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

from src.trading.live_trading.continuation_stock_monitor import StockMonitor, StockState

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('svro_tick_streamer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DummySVROTickStreamer')


class SVROTestStock:
    """Represents a test stock with SVRO-specific parameters"""
    
    def __init__(self, symbol: str, instrument_key: str, previous_close: float, 
                 open_price: float, situation: str = 'continuation'):
        self.symbol = symbol
        self.instrument_key = instrument_key
        self.previous_close = previous_close
        self.open_price = open_price
        self.situation = situation
        self.current_price = open_price
        self.is_active = True
        
        # SVRO-specific tracking
        self.entry_triggered = False
        self.entry_price = None
        self.entry_time = None
        self.entry_high = None
        self.entry_sl = None
        
        # Volume tracking for SVRO
        self.early_volume = 0.0
        self.initial_volume = 0.0
        self.volume_baseline = 1000000.0  # Default baseline for testing
        
        # Price movement tracking
        self.price_history = [open_price]
        self.tick_count = 0
        self.daily_high = open_price
        self.daily_low = open_price
        
    def update_price(self, new_price: float):
        """Update current price and track history"""
        self.current_price = new_price
        self.price_history.append(new_price)
        self.tick_count += 1
        self.daily_high = max(self.daily_high, new_price)
        self.daily_low = min(self.daily_low, new_price)
        
    def update_volume(self, new_volume: float):
        """Update volume tracking"""
        self.early_volume = new_volume
        
    def reset_entry(self):
        """Reset entry tracking for retesting"""
        self.entry_triggered = False
        self.entry_price = None
        self.entry_time = None
        self.entry_high = None
        self.entry_sl = None


class DummySVROTickStreamer:
    """Generates synthetic price and volume ticks for testing SVRO continuation bot"""
    
    def __init__(self, tick_interval: float = 1.0, price_step: float = 0.05, volume_step: float = 1000.0):
        """
        Args:
            tick_interval: Time between ticks in seconds
            price_step: Price increment per tick
            volume_step: Volume increment per tick
        """
        self.tick_interval = tick_interval
        self.price_step = price_step
        self.volume_step = volume_step
        self.test_stocks: Dict[str, SVROTestStock] = {}
        self.monitor = StockMonitor()
        self.is_running = False
        self.thread = None
        
        logger.info(f"DummySVROTickStreamer initialized - Interval: {tick_interval}s, Price Step: {price_step}, Volume Step: {volume_step}")
    
    def add_test_stock(self, symbol: str, instrument_key: str, previous_close: float,
                      open_price: float, situation: str = 'continuation', volume_baseline: float = 1000000.0):
        """Add a test stock to the streamer"""
        test_stock = SVROTestStock(symbol, instrument_key, previous_close, open_price, situation)
        test_stock.volume_baseline = volume_baseline
        self.test_stocks[instrument_key] = test_stock
        
        # Add to continuation monitor
        self.monitor.add_stock(symbol, instrument_key, previous_close, situation)
        
        # Set opening price in monitor
        monitor_stock = self.monitor.stocks[instrument_key]
        monitor_stock.set_open_price(open_price)
        monitor_stock.volume_baseline = volume_baseline
        
        logger.info(f"Added SVRO test stock: {symbol} - Prev Close: {previous_close}, Open: {open_price}, Situation: {situation}, Volume Baseline: {volume_baseline:,}")
        
    def start_streaming(self):
        """Start the tick streaming process"""
        if self.is_running:
            logger.warning("SVRO tick streamer already running")
            return
            
        self.is_running = True
        self.thread = threading.Thread(target=self._stream_loop)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("DummySVROTickStreamer started")
        
    def stop_streaming(self):
        """Stop the tick streaming process"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("DummySVROTickStreamer stopped")
    
    def _stream_loop(self):
        """Main streaming loop"""
        while self.is_running:
            try:
                self._generate_ticks()
                time.sleep(self.tick_interval)
            except Exception as e:
                logger.error(f"Error in SVRO tick streaming loop: {e}")
                time.sleep(1)
    
    def _generate_ticks(self):
        """Generate price and volume ticks for all test stocks"""
        for instrument_key, test_stock in self.test_stocks.items():
            if not test_stock.is_active:
                continue
                
            # Generate new price (gradually increasing for SVRO success scenario)
            new_price = test_stock.current_price + self.price_step
            test_stock.update_price(new_price)
            
            # Generate new volume (gradually increasing to simulate volume buildup)
            new_volume = test_stock.early_volume + self.volume_step
            test_stock.update_volume(new_volume)
            
            # Get timestamp
            timestamp = datetime.now()
            
            # Process tick through continuation monitor
            self.monitor.process_tick(instrument_key, test_stock.symbol, new_price, timestamp)
            
            # Update volume tracking in monitor
            monitor_stock = self.monitor.stocks[instrument_key]
            monitor_stock.early_volume = new_volume
            monitor_stock.daily_high = test_stock.daily_high
            monitor_stock.daily_low = test_stock.daily_low
            
            # Simulate SVRO state progression
            self._simulate_svro_state_progression(test_stock, new_price, new_volume, timestamp)
            
            # Check for SVRO entry triggers
            self._check_svro_entry_triggers(test_stock, new_price, timestamp)
            
            # Log tick
            volume_pct = (new_volume / test_stock.volume_baseline * 100) if test_stock.volume_baseline > 0 else 0
            logger.info(f"SVRO Tick: {test_stock.symbol} - Price: {new_price:.2f}, Volume: {new_volume:,.0f} ({volume_pct:.1f}%), Step: {self.price_step}")
    
    def _simulate_svro_state_progression(self, test_stock: SVROTestStock, price: float, volume: float, timestamp: datetime):
        """Simulate the SVRO state progression for testing"""
        monitor_stock = self.monitor.stocks[test_stock.instrument_key]
        
        # Step 1: Validate gap (should happen automatically in process_tick)
        if not monitor_stock.gap_validated:
            monitor_stock.validate_gap()
        
        # Step 2: Check low violation (this sets entry price and ready for SVRO)
        if monitor_stock.gap_validated and not monitor_stock.low_violation_checked:
            monitor_stock.check_low_violation()
        
        # Step 3: Check volume validation (SVRO specific - 7.5% of baseline)
        if monitor_stock.low_violation_checked and not monitor_stock.volume_validated:
            volume_ratio = volume / monitor_stock.volume_baseline
            if volume_ratio >= 0.075:  # 7.5% threshold for SVRO
                monitor_stock.volume_validated = True
                logger.info(f"[{test_stock.symbol}] SVRO Volume validated: {volume_ratio:.1%} >= 7.5%")
        
        # Step 4: Prepare entry (set entry high and SL)
        if (monitor_stock.volume_validated and not monitor_stock.entry_ready and 
            monitor_stock.gap_validated and monitor_stock.low_violation_checked):
            
            # Set entry high as current high (simulating 9:20 preparation)
            monitor_stock.entry_high = monitor_stock.daily_high
            monitor_stock.entry_sl = monitor_stock.entry_high * 0.96  # 4% below entry high
            monitor_stock.entry_ready = True
            
            logger.info(f"[{test_stock.symbol}] SVRO Entry prepared - High: {monitor_stock.entry_high:.2f}, SL: {monitor_stock.entry_sl:.2f}")
    
    def _check_svro_entry_triggers(self, test_stock: SVROTestStock, price: float, timestamp: datetime):
        """Check if SVRO entry was triggered and log results"""
        monitor_stock = self.monitor.stocks[test_stock.instrument_key]
        
        # Check if stock entered position
        if monitor_stock.entered and not test_stock.entry_triggered:
            test_stock.entry_triggered = True
            test_stock.entry_price = monitor_stock.entry_price
            test_stock.entry_time = timestamp
            test_stock.entry_high = monitor_stock.entry_high
            test_stock.entry_sl = monitor_stock.entry_sl
            
            logger.info(f"🎯 SVRO ENTRY TRIGGERED: {test_stock.symbol}")
            logger.info(f"   Entry Price: {test_stock.entry_price:.2f}")
            logger.info(f"   Trigger Price: {price:.2f}")
            logger.info(f"   Entry High: {test_stock.entry_high:.2f}")
            logger.info(f"   Entry SL: {test_stock.entry_sl:.2f}")
            logger.info(f"   Previous Close: {test_stock.previous_close:.2f}")
            logger.info(f"   Situation: {test_stock.situation}")
            logger.info(f"   Ticks to trigger: {test_stock.tick_count}")
            
            # Calculate price movement to entry
            price_movement = test_stock.entry_price - test_stock.open_price
            logger.info(f"   Price movement to entry: {price_movement:+.2f} ({price_movement/test_stock.open_price*100:+.2f}%)")
            
            # Calculate volume percentage
            volume_pct = (test_stock.early_volume / test_stock.volume_baseline * 100)
            logger.info(f"   Volume percentage: {volume_pct:.1f}% of baseline")
    
    def get_test_results(self) -> Dict:
        """Get summary of SVRO test results"""
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
                'final_volume': test_stock.early_volume,
                'volume_baseline': test_stock.volume_baseline,
                'volume_percentage': (test_stock.early_volume / test_stock.volume_baseline * 100) if test_stock.volume_baseline > 0 else 0,
                'price_movement': test_stock.entry_price - test_stock.open_price if test_stock.entry_triggered else None
            }
            
            results['stock_details'][instrument_key] = stock_result
            
            if test_stock.entry_triggered:
                results['triggered_entries'] += 1
        
        return results
    
    def print_test_summary(self):
        """Print a formatted SVRO test summary"""
        results = self.get_test_results()
        
        print("\n" + "="*60)
        print("DUMMY SVRO TICK STREAMER TEST SUMMARY")
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
            print(f"  Volume: {details['final_volume']:,.0f} ({details['volume_percentage']:.1f}%)")
            print(f"  Volume Baseline: {details['volume_baseline']:,.0f}")
            
            if details['entry_triggered']:
                print(f"  Entry Price: {details['entry_price']:.2f}")
                print(f"  Price Movement: {details['price_movement']:+.2f} ({details['price_movement']/details['open_price']*100:+.2f}%)")
                print(f"  Ticks to Trigger: {details['ticks_to_trigger']}")
            else:
                print(f"  No entry triggered")
            print()
        
        print("="*60)


def create_svro_success_scenario():
    """Create a test scenario for SVRO success testing"""
    streamer = DummySVROTickStreamer(
        tick_interval=0.5, 
        price_step=0.1,
        volume_step=5000.0  # Higher volume step for SVRO testing
    )
    
    # Create SVRO test stock
    # Previous close: 100.00, Open price: 102.00 (gap up 2%)
    # Volume baseline: 1,000,000
    # Entry should trigger when price crosses entry high with sufficient volume
    streamer.add_test_stock(
        symbol="TEST_SVRO",
        instrument_key="TEST_SVRO_KEY", 
        previous_close=100.0,
        open_price=102.0,  # Gap up 2%
        situation='continuation',
        volume_baseline=1000000.0
    )
    
    return streamer


def create_svro_volume_test_scenario():
    """Create a test scenario for SVRO volume validation testing"""
    streamer = DummySVROTickStreamer(
        tick_interval=0.5, 
        price_step=0.05,
        volume_step=2000.0  # Lower volume step to test volume threshold
    )
    
    # Create SVRO test stock with lower volume to test threshold
    streamer.add_test_stock(
        symbol="TEST_SVRO_LOWVOL",
        instrument_key="TEST_SVRO_LOWVOL_KEY", 
        previous_close=100.0,
        open_price=101.5,  # Gap up 1.5%
        situation='continuation',
        volume_baseline=1000000.0
    )
    
    return streamer


def run_svro_success_test():
    """Run the SVRO success test scenario"""
    print("🚀 Starting SVRO Success Test")
    print("Testing: SVRO stock should enter when price crosses entry high with sufficient volume")
    print("Setup: Previous Close = 100.00, Open Price = 102.00 (gap up 2%)")
    print("Expected: Entry when price >= entry high with volume >= 7.5% of baseline")
    print()
    
    # Create test scenario
    streamer = create_svro_success_scenario()
    
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
                print(f"\n🎯 SVRO Entry triggered! Stopping test early.")
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
    # Run the SVRO success test
    results = run_svro_success_test()
    
    # Exit with appropriate code
    if results['triggered_entries'] > 0:
        print("\n🎉 SVRO success test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SVRO success test FAILED!")
        sys.exit(1)