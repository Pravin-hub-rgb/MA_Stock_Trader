#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realistic SVRO Testing - Tests the continuation bot with real-world conditions
Focuses on testing the actual SVRO logic with realistic volume, timing, and price action
"""

import sys
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.live_trading.continuation_stock_monitor import StockMonitor
from src.trading.live_trading.stock_scorer import stock_scorer
from src.utils.upstox_fetcher import UpstoxFetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('realistic_svro_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealisticSVROTest')


class RealisticSVROTest:
    """Tests SVRO continuation logic with realistic market conditions"""

    def __init__(self):
        self.monitor = StockMonitor()
        self.upstox_fetcher = UpstoxFetcher()
        self.test_stocks = {}
        self.is_running = False
        self.test_results = []

    def setup_realistic_test_stocks(self):
        """Setup test stocks with realistic parameters based on actual market data"""
        logger.info("Setting up realistic SVRO test stocks...")

        # Get real symbols and their data
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        test_configs = []

        for symbol in symbols:
            try:
                # Get real previous close
                data = self.upstox_fetcher.get_ltp_data(symbol)
                if data and 'cp' in data:
                    prev_close = float(data['cp'])
                    
                    # Get real volume baseline from cache
                    metadata = stock_scorer.stock_metadata.get(symbol, {})
                    volume_baseline = metadata.get('volume_baseline', 1000000)
                    
                    # Create realistic test scenarios
                    test_configs.append({
                        'symbol': symbol,
                        'instrument_key': f"{symbol}_KEY",
                        'previous_close': prev_close,
                        'volume_baseline': volume_baseline,
                        'situation': 'continuation'
                    })
                    
                    logger.info(f"Loaded {symbol}: Prev Close = {prev_close:.2f}, Volume Baseline = {volume_baseline:,}")
                else:
                    logger.warning(f"No data for {symbol}")
            except Exception as e:
                logger.error(f"Error loading {symbol}: {e}")

        # Create test stocks with different scenarios
        scenarios = [
            # Scenario 1: Easy pass - gap up 2%, volume 10%
            {
                'name': 'Easy Pass',
                'gap_pct': 0.02,
                'volume_ratio': 0.10,
                'price_pattern': 'steady_up'
            },
            # Scenario 2: Tough pass - gap up 0.4%, volume 7.6% (barely passes)
            {
                'name': 'Tough Pass',
                'gap_pct': 0.004,
                'volume_ratio': 0.076,
                'price_pattern': 'volatile'
            },
            # Scenario 3: Volume failure - gap up 3%, volume 5% (fails volume)
            {
                'name': 'Volume Failure',
                'gap_pct': 0.03,
                'volume_ratio': 0.05,
                'price_pattern': 'steady_up'
            },
            # Scenario 4: Low violation - gap up 2%, volume 10%, but low drops 1.5%
            {
                'name': 'Low Violation',
                'gap_pct': 0.02,
                'volume_ratio': 0.10,
                'price_pattern': 'low_violation'
            },
            # Scenario 5: Gap boundary - exactly 0.3% gap
            {
                'name': 'Gap Boundary',
                'gap_pct': 0.003,
                'volume_ratio': 0.08,
                'price_pattern': 'steady_up'
            }
        ]

        for i, config in enumerate(test_configs[:5]):
            scenario = scenarios[i]
            
            # Calculate opening price based on gap
            open_price = config['previous_close'] * (1 + scenario['gap_pct'])
            
            # Calculate volume parameters
            target_volume = config['volume_baseline'] * scenario['volume_ratio']
            
            test_stock = {
                'symbol': config['symbol'],
                'instrument_key': f"{config['symbol']}_TEST_{i}",
                'previous_close': config['previous_close'],
                'open_price': open_price,
                'volume_baseline': config['volume_baseline'],
                'target_cumulative_volume': target_volume,
                'scenario': scenario,
                'price_pattern': scenario['price_pattern']
            }
            
            self.test_stocks[test_stock['instrument_key']] = test_stock
            
            # Add to monitor
            self.monitor.add_stock(
                symbol=test_stock['symbol'],
                instrument_key=test_stock['instrument_key'],
                previous_close=test_stock['previous_close'],
                situation='continuation'
            )
            
            # Set opening price
            monitor_stock = self.monitor.stocks[test_stock['instrument_key']]
            monitor_stock.set_open_price(test_stock['open_price'])
            monitor_stock.volume_baseline = test_stock['volume_baseline']

        logger.info(f"Setup {len(self.test_stocks)} realistic test stocks")

    def generate_realistic_price_action(self, test_stock, tick_count):
        """Generate realistic price action based on scenario"""
        base_price = test_stock['open_price']
        
        if test_stock['price_pattern'] == 'steady_up':
            # Steady upward movement
            return base_price + (tick_count * 0.05)
            
        elif test_stock['price_pattern'] == 'volatile':
            # Volatile with some noise
            base_movement = tick_count * 0.03
            noise = (tick_count % 5) * 0.02  # Random-ish noise
            return base_price + base_movement + noise
            
        elif test_stock['price_pattern'] == 'low_violation':
            # Starts up but then drops below 1% threshold
            if tick_count < 10:
                return base_price + (tick_count * 0.05)
            else:
                # Drop below 1% threshold
                threshold = base_price * 0.99
                return threshold - (tick_count * 0.02)
                
        else:
            return base_price + (tick_count * 0.05)

    def generate_realistic_volume(self, test_stock, tick_count):
        """Generate realistic volume accumulation"""
        # Volume should accumulate realistically
        if tick_count == 0:
            return 0
        
        # Base volume increment
        base_increment = test_stock['target_cumulative_volume'] / 100  # Spread over 100 ticks
        
        # Add some randomness to volume
        import random
        volume_noise = random.uniform(0.5, 1.5)
        
        return base_increment * volume_noise

    def run_realistic_test(self):
        """Run the realistic SVRO test"""
        print("🧪 Starting Realistic SVRO Test")
        print("=" * 60)
        print("Testing: Real-world SVRO conditions with actual market data")
        print("Focus: Volume tracking, timing, and price action validation")
        print()

        # Setup test stocks
        self.setup_realistic_test_stocks()

        if not self.test_stocks:
            logger.error("No test stocks loaded - cannot run test")
            return False

        # Run test simulation
        self.is_running = True
        tick_count = 0
        max_ticks = 200  # Simulate 200 ticks (about 3-4 minutes)

        logger.info("Starting realistic SVRO test simulation...")

        while self.is_running and tick_count < max_ticks:
            try:
                self._simulate_tick(tick_count)
                tick_count += 1
                time.sleep(0.1)  # 100ms per tick
                
                # Log progress every 50 ticks
                if tick_count % 50 == 0:
                    logger.info(f"Simulation tick {tick_count}/{max_ticks}")
                    
            except Exception as e:
                logger.error(f"Error in simulation tick {tick_count}: {e}")
                break

        # Analyze results
        self._analyze_results()
        
        return True

    def _simulate_tick(self, tick_count):
        """Simulate a single tick for all test stocks"""
        timestamp = datetime.now()

        for instrument_key, test_stock in self.test_stocks.items():
            # Generate realistic price
            price = self.generate_realistic_price_action(test_stock, tick_count)
            
            # Generate realistic volume
            volume_increment = self.generate_realistic_volume(test_stock, tick_count)
            
            # Update cumulative volume
            monitor_stock = self.monitor.stocks[instrument_key]
            monitor_stock.early_volume += volume_increment

            # Process tick through monitor
            self.monitor.process_tick(instrument_key, test_stock['symbol'], price, timestamp)

            # Simulate state progression
            self._simulate_state_progression(monitor_stock, test_stock, price, timestamp)

            # Check for entry triggers
            self._check_entry_triggers(monitor_stock, test_stock, price, timestamp)

    def _simulate_state_progression(self, monitor_stock, test_stock, price, timestamp):
        """Simulate the realistic state progression"""
        
        # Step 1: Gap validation (should pass based on setup)
        if not monitor_stock.gap_validated:
            monitor_stock.validate_gap()

        # Step 2: Low violation check (timing-based)
        if monitor_stock.gap_validated and not monitor_stock.low_violation_checked:
            monitor_stock.check_low_violation()

        # Step 3: Volume validation (critical for SVRO)
        if (monitor_stock.low_violation_checked and 
            not monitor_stock.volume_validated and 
            monitor_stock.early_volume > 0):
            
            # Check if we have enough volume for validation
            required_volume = test_stock['volume_baseline'] * 0.075
            if monitor_stock.early_volume >= required_volume:
                monitor_stock.validate_volume(test_stock['volume_baseline'])

        # Step 4: Entry preparation (at 9:20 equivalent)
        if (monitor_stock.volume_validated and 
            not monitor_stock.entry_ready and 
            monitor_stock.daily_high > 0):
            monitor_stock.prepare_entry()

    def _check_entry_triggers(self, monitor_stock, test_stock, price, timestamp):
        """Check for entry triggers and log results"""
        if monitor_stock.entered:
            # Log entry details
            entry_info = {
                'symbol': test_stock['symbol'],
                'scenario': test_stock['scenario']['name'],
                'gap_pct': test_stock['scenario']['gap_pct'],
                'volume_ratio': test_stock['scenario']['volume_ratio'],
                'entry_price': monitor_stock.entry_price,
                'entry_time': timestamp,
                'triggered': True,
                'reason': 'Entry triggered successfully'
            }
            
            self.test_results.append(entry_info)
            logger.info(f"🎯 ENTRY TRIGGERED: {test_stock['symbol']} ({test_stock['scenario']['name']})")
            logger.info(f"   Entry Price: {monitor_stock.entry_price:.2f}")
            logger.info(f"   Gap: {test_stock['scenario']['gap_pct']*100:.1f}%")
            logger.info(f"   Volume Ratio: {test_stock['scenario']['volume_ratio']*100:.1f}%")

    def _analyze_results(self):
        """Analyze and print test results"""
        print("\n" + "="*60)
        print("REALISTIC SVRO TEST RESULTS")
        print("="*60)

        # Count results by scenario
        scenario_results = {}
        for result in self.test_results:
            scenario = result['scenario']
            if scenario not in scenario_results:
                scenario_results[scenario] = []
            scenario_results[scenario].append(result)

        # Print detailed results
        for scenario_name, results in scenario_results.items():
            print(f"\n{scenario_name} Scenario:")
            print(f"  Expected: {'PASS' if 'Pass' in scenario_name else 'FAIL'}")
            print(f"  Actual: {'PASS' if results else 'FAIL'}")
            print(f"  Entries: {len(results)}")
            
            for result in results:
                print(f"    {result['symbol']}: Entry at {result['entry_price']:.2f}")

        # Summary
        total_expected_pass = sum(1 for s in ['Easy Pass', 'Tough Pass', 'Gap Boundary'] if s in scenario_results)
        total_expected_fail = sum(1 for s in ['Volume Failure', 'Low Violation'] if s in scenario_results)
        
        print(f"\nSUMMARY:")
        print(f"  Total Test Stocks: {len(self.test_stocks)}")
        print(f"  Expected to Pass: {total_expected_pass}")
        print(f"  Expected to Fail: {total_expected_fail}")
        print(f"  Actual Entries: {len(self.test_results)}")

        # Validation
        success = True
        if len(self.test_results) != total_expected_pass:
            success = False
            print(f"  ❌ TEST FAILED: Expected {total_expected_pass} entries, got {len(self.test_results)}")
        else:
            print(f"  ✅ TEST PASSED: All expected scenarios behaved correctly")

        # Detailed scenario validation
        print(f"\nSCENARIO VALIDATION:")
        
        # Easy Pass should work
        if 'Easy Pass' in scenario_results:
            print(f"  ✅ Easy Pass: WORKED (gap 2%, volume 10%)")
        else:
            print(f"  ❌ Easy Pass: FAILED (should have worked)")
            success = False

        # Tough Pass should work (barely)
        if 'Tough Pass' in scenario_results:
            print(f"  ✅ Tough Pass: WORKED (gap 0.4%, volume 7.6%)")
        else:
            print(f"  ❌ Tough Pass: FAILED (should have barely worked)")
            success = False

        # Volume Failure should not work
        if 'Volume Failure' not in scenario_results:
            print(f"  ✅ Volume Failure: CORRECTLY REJECTED (volume 5% < 7.5%)")
        else:
            print(f"  ❌ Volume Failure: INCORRECTLY ACCEPTED")
            success = False

        # Low Violation should not work
        if 'Low Violation' not in scenario_results:
            print(f"  ✅ Low Violation: CORRECTLY REJECTED (price dropped below 1%)")
        else:
            print(f"  ❌ Low Violation: INCORRECTLY ACCEPTED")
            success = False

        # Gap Boundary should work
        if 'Gap Boundary' in scenario_results:
            print(f"  ✅ Gap Boundary: WORKED (exactly 0.3% gap)")
        else:
            print(f"  ❌ Gap Boundary: FAILED (should have worked at boundary)")
            success = False

        print("\n" + "="*60)
        
        if success:
            print("🎉 ALL REALISTIC SVRO TESTS PASSED!")
            print("The continuation bot correctly handles:")
            print("  - Volume validation (7.5% threshold)")
            print("  - Gap validation (0.3% minimum)")
            print("  - Low violation monitoring (1% threshold)")
            print("  - Realistic price action patterns")
        else:
            print("❌ SOME REALISTIC SVRO TESTS FAILED!")
            print("Check the SVRO logic for issues with:")
            print("  - Volume accumulation and validation")
            print("  - Gap boundary conditions")
            print("  - Low violation detection")

        return success


def main():
    """Main test runner"""
    test = RealisticSVROTest()
    success = test.run_realistic_test()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)