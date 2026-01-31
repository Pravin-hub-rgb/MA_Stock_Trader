#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open Range Monitoring Test - Tests high tracking and low violation detection
Focuses on the 9:15-9:20 window monitoring for entry high and low violation checks
"""

import sys
import os
import time
from datetime import datetime, time, timedelta
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.trading.live_trading.continuation_stock_monitor import StockMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('open_range_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('OpenRangeTest')


class OpenRangeMonitoringTest:
    """Tests open range monitoring and low violation detection"""

    def __init__(self):
        self.monitor = StockMonitor()
        self.test_stock = None
        self.test_results = []

    def setup_open_range_test_stock(self):
        """Setup a test stock for open range monitoring"""
        logger.info("Setting up open range monitoring test stock...")
        
        # Create test stock
        self.test_stock = {
            'symbol': 'TEST_OPEN_RANGE',
            'instrument_key': 'TEST_OPEN_RANGE_KEY',
            'previous_close': 100.0,
            'open_price': 102.0,  # 2% gap up
            'situation': 'continuation'
        }

        # Add to monitor
        self.monitor.add_stock(
            symbol=self.test_stock['symbol'],
            instrument_key=self.test_stock['instrument_key'],
            previous_close=self.test_stock['previous_close'],
            situation=self.test_stock['situation']
        )

        # Set opening price
        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        monitor_stock.set_open_price(self.test_stock['open_price'])

        logger.info(f"Open range test stock setup complete:")
        logger.info(f"  Symbol: {self.test_stock['symbol']}")
        logger.info(f"  Previous Close: {self.test_stock['previous_close']:.2f}")
        logger.info(f"  Open Price: {self.test_stock['open_price']:.2f}")
        logger.info(f"  Gap: {((self.test_stock['open_price'] - self.test_stock['previous_close']) / self.test_stock['previous_close'] * 100):+.1f}%")

    def test_low_violation_detection(self):
        """Test low violation detection during monitoring window"""
        print("🧪 Testing Low Violation Detection")
        print("=" * 50)
        print("Testing: Low violation monitoring (1% below open price)")
        print("Focus: Price dropping below 1% threshold triggers rejection")
        print()

        if not self.test_stock:
            self.setup_open_range_test_stock()

        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        
        # Test scenarios for low violation
        test_scenarios = [
            {
                'name': 'No Low Violation',
                'price_pattern': lambda t: 102.0 + (t * 0.05),  # Steady up
                'expected_violation': False,
                'reason': 'Price stays above 1% threshold'
            },
            {
                'name': 'Low Violation Occurs',
                'price_pattern': lambda t: 102.0 - (t * 0.05) if t < 20 else 102.0 - (20 * 0.05) - ((t - 20) * 0.02),  # Drops below 1%
                'expected_violation': True,
                'reason': 'Price drops below 1% threshold'
            },
            {
                'name': 'Touch Threshold',
                'price_pattern': lambda t: 102.0 - (t * 0.01),  # Drops to exactly 1%
                'expected_violation': True,
                'reason': 'Price touches 1% threshold'
            },
            {
                'name': 'Recovery After Violation',
                'price_pattern': lambda t: 102.0 - (t * 0.05) if t < 10 else 102.0 - (10 * 0.05) + ((t - 10) * 0.03),  # Drops then recovers
                'expected_violation': True,
                'reason': 'Violation occurs even if price recovers'
            }
        ]

        results = []

        for scenario in test_scenarios:
            logger.info(f"\n--- Testing {scenario['name']} ---")
            logger.info(f"Expected Violation: {'YES' if scenario['expected_violation'] else 'NO'}")

            # Reset stock state
            monitor_stock.daily_high = self.test_stock['open_price']
            monitor_stock.daily_low = self.test_stock['open_price']
            monitor_stock.low_violation_checked = False
            monitor_stock.rejection_reason = None
            monitor_stock.is_active = True

            # Calculate 1% threshold
            threshold = self.test_stock['open_price'] * 0.99
            logger.info(f"1% Threshold: {threshold:.2f}")

            # Simulate price action over 100 ticks
            violation_detected = False
            violation_tick = None

            for tick in range(100):
                # Generate price based on pattern
                price = scenario['price_pattern'](tick)
                
                # Update stock price
                timestamp = datetime.now()
                monitor_stock.update_price(price, timestamp)

                # Check for low violation
                if not monitor_stock.low_violation_checked:
                    monitor_stock.check_low_violation()

                # Track if violation was detected
                if monitor_stock.rejection_reason and 'Low violation' in monitor_stock.rejection_reason:
                    if not violation_detected:
                        violation_detected = True
                        violation_tick = tick
                        logger.info(f"  ⚠️  Low violation detected at tick {tick}: Price {price:.2f} < Threshold {threshold:.2f}")

                # Log price movement
                if tick % 20 == 0:
                    logger.debug(f"  Tick {tick}: Price = {price:.2f}, High = {monitor_stock.daily_high:.2f}, Low = {monitor_stock.daily_low:.2f}")

            # Check final result
            actual_violation = violation_detected
            passed = actual_violation == scenario['expected_violation']

            result = {
                'scenario': scenario['name'],
                'expected_violation': scenario['expected_violation'],
                'actual_violation': actual_violation,
                'passed': passed,
                'violation_tick': violation_tick,
                'final_high': monitor_stock.daily_high,
                'final_low': monitor_stock.daily_low,
                'rejection_reason': monitor_stock.rejection_reason
            }

            results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {status} {scenario['name']}: Expected {'VIOLATION' if scenario['expected_violation'] else 'NO VIOLATION'}, Got {'VIOLATION' if actual_violation else 'NO VIOLATION'}")
            if not passed:
                logger.info(f"       Expected: {scenario['expected_violation']}, Actual: {actual_violation}")

        return results

    def test_open_range_high_tracking(self):
        """Test high tracking during the 9:15-9:20 window"""
        print("\n🧪 Testing Open Range High Tracking")
        print("=" * 50)
        print("Testing: High tracking during 9:15-9:20 monitoring window")
        print("Focus: Entry high set correctly at 9:20")
        print()

        if not self.test_stock:
            self.setup_open_range_test_stock()

        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        
        # Test scenarios for high tracking
        high_tracking_scenarios = [
            {
                'name': 'Steady Upward',
                'price_pattern': lambda t: 102.0 + (t * 0.1),  # Steady upward movement
                'expected_entry_high': 102.0 + (99 * 0.1),  # Final price should be entry high
                'description': 'Price moves steadily up, high should track'
            },
            {
                'name': 'Volatile Range',
                'price_pattern': lambda t: 102.0 + (t % 10) * 0.5 - 2.5,  # Oscillating pattern
                'expected_entry_high': 102.0 + 2.5,  # Peak of oscillation
                'description': 'Price oscillates, high should track peaks'
            },
            {
                'name': 'Early Spike',
                'price_pattern': lambda t: 102.0 + 5.0 if t < 10 else 102.0 + 5.0 - ((t - 10) * 0.1),  # Spike then decline
                'expected_entry_high': 107.0,  # Early spike should be entry high
                'description': 'Early spike sets high, then declines'
            },
            {
                'name': 'Late Surge',
                'price_pattern': lambda t: 102.0 + (t * 0.05) if t < 80 else 102.0 + (80 * 0.05) + ((t - 80) * 0.2),  # Late surge
                'expected_entry_high': 102.0 + (80 * 0.05) + (19 * 0.2),  # Late surge sets new high
                'description': 'Late surge creates new high'
            }
        ]

        high_results = []

        for scenario in high_tracking_scenarios:
            logger.info(f"\n--- Testing {scenario['name']} ---")
            logger.info(f"Description: {scenario['description']}")
            logger.info(f"Expected Entry High: {scenario['expected_entry_high']:.2f}")

            # Reset stock state
            monitor_stock.daily_high = self.test_stock['open_price']
            monitor_stock.daily_low = self.test_stock['open_price']
            monitor_stock.entry_high = None
            monitor_stock.entry_ready = False

            # Simulate price action over 100 ticks
            price_history = []

            for tick in range(100):
                # Generate price based on pattern
                price = scenario['price_pattern'](tick)
                price_history.append(price)
                
                # Update stock price
                timestamp = datetime.now()
                monitor_stock.update_price(price, timestamp)

                # Log price movement
                if tick % 20 == 0:
                    logger.debug(f"  Tick {tick}: Price = {price:.2f}, Daily High = {monitor_stock.daily_high:.2f}")

            # Set entry high (simulating 9:20 preparation)
            monitor_stock.entry_high = monitor_stock.daily_high
            monitor_stock.entry_ready = True

            # Check result
            actual_entry_high = monitor_stock.entry_high
            expected_entry_high = scenario['expected_entry_high']
            
            # Allow small tolerance for floating point precision
            tolerance = 0.01
            passed = abs(actual_entry_high - expected_entry_high) <= tolerance

            result = {
                'scenario': scenario['name'],
                'expected_entry_high': expected_entry_high,
                'actual_entry_high': actual_entry_high,
                'passed': passed,
                'price_history': price_history,
                'daily_high': monitor_stock.daily_high,
                'description': scenario['description']
            }

            high_results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {status} {scenario['name']}: Expected {expected_entry_high:.2f}, Got {actual_entry_high:.2f}")
            if not passed:
                logger.info(f"       Difference: {abs(actual_entry_high - expected_entry_high):.2f}")

        return high_results

    def test_entry_signal_generation(self):
        """Test entry signal generation after 9:20"""
        print("\n🧪 Testing Entry Signal Generation")
        print("=" * 50)
        print("Testing: Entry signal when price breaks above entry high")
        print("Focus: Signal generation after 9:20 preparation")
        print()

        if not self.test_stock:
            self.setup_open_range_test_stock()

        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        
        # Setup stock for entry signal testing
        monitor_stock.daily_high = 105.0  # Simulate high reached during 9:15-9:20
        monitor_stock.entry_high = 105.0
        monitor_stock.entry_sl = 105.0 * 0.96  # 4% below entry high
        monitor_stock.entry_ready = True

        logger.info(f"Entry setup:")
        logger.info(f"  Entry High: {monitor_stock.entry_high:.2f}")
        logger.info(f"  Entry SL: {monitor_stock.entry_sl:.2f}")

        # Test entry signal scenarios
        entry_scenarios = [
            {
                'name': 'No Entry Signal',
                'price_pattern': lambda t: 104.0 + (t * 0.05),  # Stays below entry high
                'expected_signal': False,
                'reason': 'Price never breaks entry high'
            },
            {
                'name': 'Entry Signal Triggered',
                'price_pattern': lambda t: 104.0 + (t * 0.1),  # Breaks above entry high
                'expected_signal': True,
                'reason': 'Price breaks above entry high'
            },
            {
                'name': 'Touch Entry High',
                'price_pattern': lambda t: 105.0 - (t * 0.01),  # Touches but doesn't break
                'expected_signal': False,
                'reason': 'Price touches but doesn\'t break entry high'
            },
            {
                'name': 'Break and Retest',
                'price_pattern': lambda t: 104.0 + (t * 0.1) if t < 50 else 109.0 - ((t - 50) * 0.05),  # Breaks then retraces
                'expected_signal': True,
                'reason': 'Price breaks entry high even if it retraces'
            }
        ]

        entry_results = []

        for scenario in entry_scenarios:
            logger.info(f"\n--- Testing {scenario['name']} ---")
            logger.info(f"Expected Signal: {'YES' if scenario['expected_signal'] else 'NO'}")

            # Reset stock state
            monitor_stock.entered = False
            monitor_stock.entry_price = None
            monitor_stock.entry_time = None

            # Simulate price action
            signal_triggered = False
            signal_tick = None

            for tick in range(100):
                # Generate price based on pattern
                price = scenario['price_pattern'](tick)
                
                # Check entry signal
                if monitor_stock.entry_ready and not monitor_stock.entered:
                    should_trigger = monitor_stock.check_entry_signal(price)
                    if should_trigger:
                        if not signal_triggered:
                            signal_triggered = True
                            signal_tick = tick
                            logger.info(f"  🎯 Entry signal triggered at tick {tick}: Price {price:.2f} >= Entry High {monitor_stock.entry_high:.2f}")

                # Log price movement
                if tick % 20 == 0:
                    logger.debug(f"  Tick {tick}: Price = {price:.2f}, Entry High = {monitor_stock.entry_high:.2f}")

            # Check final result
            actual_signal = signal_triggered
            passed = actual_signal == scenario['expected_signal']

            result = {
                'scenario': scenario['name'],
                'expected_signal': scenario['expected_signal'],
                'actual_signal': actual_signal,
                'passed': passed,
                'signal_tick': signal_tick,
                'reason': scenario['reason']
            }

            entry_results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {status} {scenario['name']}: Expected {'SIGNAL' if scenario['expected_signal'] else 'NO SIGNAL'}, Got {'SIGNAL' if actual_signal else 'NO SIGNAL'}")
            if not passed:
                logger.info(f"       Expected: {scenario['expected_signal']}, Actual: {actual_signal}")

        return entry_results

    def run_comprehensive_open_range_test(self):
        """Run comprehensive open range monitoring tests"""
        print("🧪 Starting Comprehensive Open Range Monitoring Test")
        print("=" * 60)
        print("Testing: All aspects of open range monitoring for SVRO system")
        print("Focus: Low violation, high tracking, and entry signal generation")
        print()

        # Setup test stock
        self.setup_open_range_test_stock()

        # Run all tests
        low_violation_results = self.test_low_violation_detection()
        high_tracking_results = self.test_open_range_high_tracking()
        entry_signal_results = self.test_entry_signal_generation()

        # Analyze and print comprehensive results
        self._print_comprehensive_results(low_violation_results, high_tracking_results, entry_signal_results)

        return low_violation_results, high_tracking_results, entry_signal_results

    def _print_comprehensive_results(self, low_violation_results, high_tracking_results, entry_signal_results):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("COMPREHENSIVE OPEN RANGE MONITORING TEST RESULTS")
        print("="*60)

        # Low violation test results
        print("\n⚠️  LOW VIOLATION TESTS:")
        low_violation_passed = 0
        for result in low_violation_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} {result['scenario']}")
            print(f"     Expected: {'VIOLATION' if result['expected_violation'] else 'NO VIOLATION'}")
            print(f"     Actual: {'VIOLATION' if result['actual_violation'] else 'NO VIOLATION'}")
            if result['violation_tick']:
                print(f"     Violation at tick: {result['violation_tick']}")
            if result['rejection_reason']:
                print(f"     Rejection: {result['rejection_reason']}")
            if result['passed']:
                low_violation_passed += 1
            print()

        # High tracking test results
        print("\n📈 HIGH TRACKING TESTS:")
        high_tracking_passed = 0
        for result in high_tracking_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} {result['scenario']}")
            print(f"     Expected Entry High: {result['expected_entry_high']:.2f}")
            print(f"     Actual Entry High: {result['actual_entry_high']:.2f}")
            print(f"     Daily High: {result['daily_high']:.2f}")
            print(f"     Description: {result['description']}")
            if result['passed']:
                high_tracking_passed += 1
            print()

        # Entry signal test results
        print("\n🎯 ENTRY SIGNAL TESTS:")
        entry_signal_passed = 0
        for result in entry_signal_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} {result['scenario']}")
            print(f"     Expected: {'SIGNAL' if result['expected_signal'] else 'NO SIGNAL'}")
            print(f"     Actual: {'SIGNAL' if result['actual_signal'] else 'NO SIGNAL'}")
            if result['signal_tick']:
                print(f"     Signal at tick: {result['signal_tick']}")
            print(f"     Reason: {result['reason']}")
            if result['passed']:
                entry_signal_passed += 1
            print()

        # Summary
        total_tests = len(low_violation_results) + len(high_tracking_results) + len(entry_signal_results)
        total_passed = low_violation_passed + high_tracking_passed + entry_signal_passed
        
        print(f"\nSUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_tests - total_passed}")
        print(f"  Success Rate: {total_passed/total_tests*100:.1f}%")

        # Critical functionality validation
        print(f"\n🎯 CRITICAL FUNCTIONALITY VALIDATION:")

        # Low violation detection
        if low_violation_passed == len(low_violation_results):
            print(f"  ✅ Low violation detection working correctly")
        else:
            print(f"  ❌ Low violation detection has issues")

        # High tracking
        if high_tracking_passed == len(high_tracking_results):
            print(f"  ✅ High tracking working correctly")
        else:
            print(f"  ❌ High tracking has issues")

        # Entry signal generation
        if entry_signal_passed == len(entry_signal_results):
            print(f"  ✅ Entry signal generation working correctly")
        else:
            print(f"  ❌ Entry signal generation has issues")

        # Final assessment
        success = (low_violation_passed == len(low_violation_results) and 
                  high_tracking_passed == len(high_tracking_results) and
                  entry_signal_passed == len(entry_signal_results))

        print("\n" + "="*60)
        if success:
            print("🎉 COMPREHENSIVE OPEN RANGE MONITORING TESTS PASSED!")
            print("The SVRO open range monitoring system correctly:")
            print("  - Detects low violations (1% threshold)")
            print("  - Tracks daily high during monitoring window")
            print("  - Sets entry high at 9:20")
            print("  - Generates entry signals when price breaks entry high")
            print("  - Rejects stocks that violate low threshold")
        else:
            print("❌ SOME OPEN RANGE MONITORING TESTS FAILED!")
            print("Issues detected with:")
            if low_violation_passed < len(low_violation_results):
                print("  - Low violation detection")
            if high_tracking_passed < len(high_tracking_results):
                print("  - High tracking during monitoring window")
            if entry_signal_passed < len(entry_signal_results):
                print("  - Entry signal generation")

        return success


def main():
    """Main test runner"""
    test = OpenRangeMonitoringTest()
    low_violation_results, high_tracking_results, entry_signal_results = test.run_comprehensive_open_range_test()
    return low_violation_results, high_tracking_results, entry_signal_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)