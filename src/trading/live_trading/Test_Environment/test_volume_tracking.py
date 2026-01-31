#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Volume Tracking Test - Tests the 7.5% cumulative volume requirement for SVRO
Focuses specifically on volume accumulation and validation during market open
"""

import sys
import os
import time
from datetime import datetime, time, timedelta
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
        logging.FileHandler('volume_tracking_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VolumeTrackingTest')


class VolumeTrackingTest:
    """Tests volume tracking and validation for SVRO system"""

    def __init__(self):
        self.monitor = StockMonitor()
        self.upstox_fetcher = UpstoxFetcher()
        self.test_stock = None
        self.volume_baseline = 1000000  # Default baseline for testing
        self.test_results = []

    def setup_volume_test_stock(self):
        """Setup a test stock specifically for volume tracking"""
        logger.info("Setting up volume tracking test stock...")
        
        # Try to get real data first
        try:
            data = self.upstox_fetcher.get_ltp_data('RELIANCE')
            if data and 'cp' in data:
                prev_close = float(data['cp'])
                logger.info(f"Using RELIANCE: Previous close = {prev_close:.2f}")
            else:
                prev_close = 2500.0  # Fallback
                logger.info(f"Using fallback: Previous close = {prev_close:.2f}")
        except Exception as e:
            prev_close = 2500.0
            logger.warning(f"Could not get real data: {e}")

        # Get real volume baseline if available
        metadata = stock_scorer.stock_metadata.get('RELIANCE', {})
        if metadata.get('volume_baseline', 0) > 0:
            self.volume_baseline = metadata['volume_baseline']
            logger.info(f"Using real volume baseline: {self.volume_baseline:,}")
        else:
            logger.info(f"Using default volume baseline: {self.volume_baseline:,}")

        # Create test stock
        self.test_stock = {
            'symbol': 'RELIANCE',
            'instrument_key': 'RELIANCE_VOLUME_TEST',
            'previous_close': prev_close,
            'open_price': prev_close * 1.02,  # 2% gap up
            'volume_baseline': self.volume_baseline
        }

        # Add to monitor
        self.monitor.add_stock(
            symbol=self.test_stock['symbol'],
            instrument_key=self.test_stock['instrument_key'],
            previous_close=self.test_stock['previous_close'],
            situation='continuation'
        )

        # Set opening price and volume baseline
        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        monitor_stock.set_open_price(self.test_stock['open_price'])
        monitor_stock.volume_baseline = self.test_stock['volume_baseline']
        monitor_stock.initial_volume = 0  # Start with 0 initial volume

        logger.info(f"Volume test stock setup complete:")
        logger.info(f"  Symbol: {self.test_stock['symbol']}")
        logger.info(f"  Previous Close: {self.test_stock['previous_close']:.2f}")
        logger.info(f"  Open Price: {self.test_stock['open_price']:.2f}")
        logger.info(f"  Volume Baseline: {self.volume_baseline:,}")
        logger.info(f"  Required Volume (7.5%): {self.volume_baseline * 0.075:,.0f}")

    def test_volume_accumulation(self):
        """Test volume accumulation over time"""
        print("🧪 Testing Volume Accumulation")
        print("=" * 50)
        print("Testing: Cumulative volume tracking during market open window")
        print("Focus: 7.5% of mean volume baseline requirement")
        print()

        if not self.test_stock:
            self.setup_volume_test_stock()

        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        
        # Test scenarios
        test_scenarios = [
            {
                'name': 'Volume Too Low',
                'target_volume': self.volume_baseline * 0.05,  # 5% - should fail
                'expected_valid': False,
                'reason': 'Volume below 7.5% threshold'
            },
            {
                'name': 'Volume At Threshold',
                'target_volume': self.volume_baseline * 0.075,  # 7.5% - should pass
                'expected_valid': True,
                'reason': 'Volume exactly at 7.5% threshold'
            },
            {
                'name': 'Volume Above Threshold',
                'target_volume': self.volume_baseline * 0.10,  # 10% - should pass
                'expected_valid': True,
                'reason': 'Volume above 7.5% threshold'
            },
            {
                'name': 'Volume Much Higher',
                'target_volume': self.volume_baseline * 0.25,  # 25% - should pass
                'expected_valid': True,
                'reason': 'Volume well above 7.5% threshold'
            }
        ]

        results = []

        for scenario in test_scenarios:
            logger.info(f"\n--- Testing {scenario['name']} ---")
            logger.info(f"Target Volume: {scenario['target_volume']:,.0f}")
            logger.info(f"Expected: {'PASS' if scenario['expected_valid'] else 'FAIL'}")

            # Reset stock state
            monitor_stock.early_volume = 0
            monitor_stock.volume_validated = False
            monitor_stock.rejection_reason = None

            # Simulate volume accumulation over time
            ticks_needed = 100  # Simulate 100 ticks
            volume_per_tick = scenario['target_volume'] / ticks_needed

            for tick in range(ticks_needed):
                # Add volume increment
                monitor_stock.early_volume += volume_per_tick
                
                # Check volume validation periodically
                if tick % 10 == 0:  # Check every 10 ticks
                    current_ratio = monitor_stock.early_volume / self.volume_baseline
                    logger.debug(f"  Tick {tick}: Volume = {monitor_stock.early_volume:,.0f}, Ratio = {current_ratio:.1%}")

                # Try to validate volume
                if not monitor_stock.volume_validated:
                    is_valid = monitor_stock.validate_volume(self.volume_baseline)
                    if is_valid:
                        logger.info(f"  ✅ Volume validation PASSED at tick {tick}")
                        logger.info(f"     Final Volume: {monitor_stock.early_volume:,.0f}")
                        logger.info(f"     Volume Ratio: {monitor_stock.early_volume/self.volume_baseline:.1%}")
                        break

            # Check final result
            final_valid = monitor_stock.volume_validated
            passed = final_valid == scenario['expected_valid']

            result = {
                'scenario': scenario['name'],
                'target_volume': scenario['target_volume'],
                'final_volume': monitor_stock.early_volume,
                'final_ratio': monitor_stock.early_volume / self.volume_baseline,
                'expected_valid': scenario['expected_valid'],
                'actual_valid': final_valid,
                'passed': passed,
                'rejection_reason': monitor_stock.rejection_reason
            }

            results.append(result)

            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {status} {scenario['name']}: Expected {scenario['expected_valid']}, Got {final_valid}")
            if not passed:
                logger.info(f"       Rejection: {monitor_stock.rejection_reason}")

        return results

    def test_volume_timing(self):
        """Test volume accumulation timing during market open window"""
        print("\n🧪 Testing Volume Timing")
        print("=" * 50)
        print("Testing: Volume accumulation during 9:15-9:20 window")
        print("Focus: Realistic volume patterns during market open")
        print()

        if not self.test_stock:
            self.setup_volume_test_stock()

        monitor_stock = self.monitor.stocks[self.test_stock['instrument_key']]
        
        # Simulate market open timing
        market_open = time(9, 15)
        entry_time = time(9, 20)
        
        logger.info(f"Simulating market timing: {market_open} to {entry_time}")

        # Test realistic volume patterns
        volume_patterns = [
            {
                'name': 'Slow Start',
                'description': 'Volume builds slowly then accelerates',
                'pattern': lambda t: t * 0.5 if t < 50 else 50 * 0.5 + (t - 50) * 2.0
            },
            {
                'name': 'Fast Start',
                'description': 'Volume spikes early then stabilizes',
                'pattern': lambda t: t * 3.0 if t < 20 else 20 * 3.0 + (t - 20) * 0.5
            },
            {
                'name': 'Steady Growth',
                'description': 'Volume grows steadily throughout',
                'pattern': lambda t: t * 1.5
            },
            {
                'name': 'Late Surge',
                'description': 'Volume stays low then surges at end',
                'pattern': lambda t: 5 if t < 80 else 5 + (t - 80) * 5.0
            }
        ]

        timing_results = []

        for pattern in volume_patterns:
            logger.info(f"\n--- Testing {pattern['name']} Pattern ---")
            logger.info(f"Description: {pattern['description']}")

            # Reset stock state
            monitor_stock.early_volume = 0
            monitor_stock.volume_validated = False
            monitor_stock.rejection_reason = None

            # Simulate 100 ticks (representing the 5-minute window)
            total_ticks = 100
            validation_times = []

            for tick in range(total_ticks):
                # Apply volume pattern
                volume_increment = pattern['pattern'](tick)
                monitor_stock.early_volume += volume_increment

                # Check volume validation
                if not monitor_stock.volume_validated:
                    current_ratio = monitor_stock.early_volume / self.volume_baseline
                    if current_ratio >= 0.075:
                        monitor_stock.validate_volume(self.volume_baseline)
                        if monitor_stock.volume_validated:
                            validation_times.append(tick)
                            logger.info(f"  ✅ Volume validation PASSED at tick {tick}")
                            logger.info(f"     Volume: {monitor_stock.early_volume:,.0f}")
                            logger.info(f"     Ratio: {current_ratio:.1%}")

            # Analyze timing
            if validation_times:
                first_validation = min(validation_times)
                logger.info(f"  First validation at tick {first_validation}/{total_ticks}")
                
                # Convert to time (assuming 100 ticks = 5 minutes)
                validation_seconds = (first_validation / total_ticks) * 300  # 5 minutes = 300 seconds
                validation_time = market_open + timedelta(seconds=validation_seconds)
                
                logger.info(f"  Validation time: {validation_time.strftime('%H:%M:%S')}")
                
                timing_result = {
                    'pattern': pattern['name'],
                    'validation_tick': first_validation,
                    'validation_time': validation_time,
                    'final_volume': monitor_stock.early_volume,
                    'final_ratio': monitor_stock.early_volume / self.volume_baseline,
                    'validated': True
                }
            else:
                logger.info(f"  ❌ Volume validation NEVER PASSED")
                timing_result = {
                    'pattern': pattern['name'],
                    'validation_tick': None,
                    'validation_time': None,
                    'final_volume': monitor_stock.early_volume,
                    'final_ratio': monitor_stock.early_volume / self.volume_baseline,
                    'validated': False
                }

            timing_results.append(timing_result)

        return timing_results

    def run_comprehensive_volume_test(self):
        """Run comprehensive volume tracking tests"""
        print("🧪 Starting Comprehensive Volume Tracking Test")
        print("=" * 60)
        print("Testing: All aspects of volume tracking for SVRO system")
        print("Focus: 7.5% threshold, timing, and realistic patterns")
        print()

        # Setup test stock
        self.setup_volume_test_stock()

        # Run volume accumulation tests
        accumulation_results = self.test_volume_accumulation()

        # Run volume timing tests
        timing_results = self.test_volume_timing()

        # Analyze and print comprehensive results
        self._print_comprehensive_results(accumulation_results, timing_results)

        return accumulation_results, timing_results

    def _print_comprehensive_results(self, accumulation_results, timing_results):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("COMPREHENSIVE VOLUME TRACKING TEST RESULTS")
        print("="*60)

        # Accumulation test results
        print("\n📊 VOLUME ACCUMULATION TESTS:")
        accumulation_passed = 0
        for result in accumulation_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {status} {result['scenario']}")
            print(f"     Target: {result['target_volume']:,.0f}")
            print(f"     Final: {result['final_volume']:,.0f}")
            print(f"     Ratio: {result['final_ratio']:.1%}")
            print(f"     Expected: {'PASS' if result['expected_valid'] else 'FAIL'}")
            print(f"     Actual: {'PASS' if result['actual_valid'] else 'FAIL'}")
            if not result['passed']:
                print(f"     Reason: {result['rejection_reason']}")
            if result['passed']:
                accumulation_passed += 1
            print()

        # Timing test results
        print("\n⏰ VOLUME TIMING TESTS:")
        timing_passed = 0
        for result in timing_results:
            status = "✅ PASS" if result['validated'] else "❌ FAIL"
            print(f"  {status} {result['pattern']}")
            if result['validation_time']:
                print(f"     Validation Time: {result['validation_time'].strftime('%H:%M:%S')}")
                print(f"     Validation Tick: {result['validation_tick']}")
            print(f"     Final Volume: {result['final_volume']:,.0f}")
            print(f"     Final Ratio: {result['final_ratio']:.1%}")
            if result['validated']:
                timing_passed += 1
            print()

        # Summary
        total_tests = len(accumulation_results) + len(timing_results)
        total_passed = accumulation_passed + timing_passed
        
        print(f"\nSUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_tests - total_passed}")
        print(f"  Success Rate: {total_passed/total_tests*100:.1f}%")

        # Volume threshold validation
        print(f"\n🎯 VOLUME THRESHOLD VALIDATION:")
        threshold_tests = [r for r in accumulation_results if 'Threshold' in r['scenario']]
        if threshold_tests:
            threshold_result = threshold_tests[0]
            if threshold_result['passed']:
                print(f"  ✅ 7.5% threshold correctly validated")
            else:
                print(f"  ❌ 7.5% threshold validation FAILED")
                print(f"     Reason: {threshold_result['rejection_reason']}")

        # Volume timing validation
        print(f"\n⏱️  VOLUME TIMING VALIDATION:")
        valid_timing = [r for r in timing_results if r['validated']]
        if valid_timing:
            print(f"  ✅ Volume validation works with realistic timing patterns")
            print(f"  Average validation time: {sum(r['validation_tick'] for r in valid_timing)/len(valid_timing):.1f} ticks")
        else:
            print(f"  ❌ Volume validation failed with all timing patterns")

        # Final assessment
        success = (accumulation_passed == len(accumulation_results) and 
                  timing_passed >= len(timing_results) // 2)  # At least half timing tests should pass

        print("\n" + "="*60)
        if success:
            print("🎉 COMPREHENSIVE VOLUME TRACKING TESTS PASSED!")
            print("The SVRO volume validation system correctly:")
            print("  - Validates 7.5% volume threshold")
            print("  - Handles different volume accumulation patterns")
            print("  - Works with realistic market timing")
            print("  - Rejects insufficient volume scenarios")
        else:
            print("❌ SOME VOLUME TRACKING TESTS FAILED!")
            print("Issues detected with:")
            if accumulation_passed < len(accumulation_results):
                print("  - Volume threshold validation")
            if timing_passed < len(timing_results) // 2:
                print("  - Volume timing and accumulation patterns")

        return success


def main():
    """Main test runner"""
    test = VolumeTrackingTest()
    accumulation_results, timing_results = test.run_comprehensive_volume_test()
    return accumulation_results, timing_results


if __name__ == "__main__":
    results = main()
    sys.exit(0)