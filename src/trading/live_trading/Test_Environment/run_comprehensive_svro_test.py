#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive SVRO Test Runner
Executes all SVRO testing modules and provides a unified test report
"""

import sys
import os
import time
from datetime import datetime
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import test modules
from test_realistic_svro_conditions import RealisticSVROTest
from test_volume_tracking import VolumeTrackingTest
from test_open_range_monitoring import OpenRangeMonitoringTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_svro_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ComprehensiveSVROTest')


class ComprehensiveSVROTestRunner:
    """Runs all SVRO tests and provides comprehensive reporting"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self):
        """Run all SVRO tests and collect results"""
        print("🧪 Starting Comprehensive SVRO Test Suite")
        print("=" * 70)
        print("Testing: Complete SVRO continuation system with realistic conditions")
        print("Modules: Volume tracking, open range monitoring, realistic scenarios")
        print()

        self.start_time = datetime.now()

        # Test 1: Realistic SVRO Conditions
        print("📋 Running Test 1: Realistic SVRO Conditions")
        print("-" * 50)
        try:
            realistic_test = RealisticSVROTest()
            realistic_success = realistic_test.run_realistic_test()
            self.test_results['realistic_conditions'] = {
                'success': realistic_success,
                'module': 'RealisticSVROTest',
                'description': 'Real-world SVRO conditions with actual market data'
            }
        except Exception as e:
            logger.error(f"Realistic SVRO test failed: {e}")
            self.test_results['realistic_conditions'] = {
                'success': False,
                'module': 'RealisticSVROTest',
                'description': 'Real-world SVRO conditions with actual market data',
                'error': str(e)
            }

        print("\n" + "="*70)

        # Test 2: Volume Tracking
        print("📋 Running Test 2: Volume Tracking")
        print("-" * 50)
        try:
            volume_test = VolumeTrackingTest()
            accumulation_results, timing_results = volume_test.run_comprehensive_volume_test()
            
            # Determine success based on results
            accumulation_passed = sum(1 for r in accumulation_results if r['passed'])
            timing_passed = sum(1 for r in timing_results if r['validated'])
            
            volume_success = (accumulation_passed == len(accumulation_results) and 
                             timing_passed >= len(timing_results) // 2)
            
            self.test_results['volume_tracking'] = {
                'success': volume_success,
                'module': 'VolumeTrackingTest',
                'description': '7.5% cumulative volume requirement validation',
                'accumulation_passed': accumulation_passed,
                'accumulation_total': len(accumulation_results),
                'timing_passed': timing_passed,
                'timing_total': len(timing_results)
            }
        except Exception as e:
            logger.error(f"Volume tracking test failed: {e}")
            self.test_results['volume_tracking'] = {
                'success': False,
                'module': 'VolumeTrackingTest',
                'description': '7.5% cumulative volume requirement validation',
                'error': str(e)
            }

        print("\n" + "="*70)

        # Test 3: Open Range Monitoring
        print("📋 Running Test 3: Open Range Monitoring")
        print("-" * 50)
        try:
            open_range_test = OpenRangeMonitoringTest()
            low_violation_results, high_tracking_results, entry_signal_results = open_range_test.run_comprehensive_open_range_test()
            
            # Determine success based on results
            low_violation_passed = sum(1 for r in low_violation_results if r['passed'])
            high_tracking_passed = sum(1 for r in high_tracking_results if r['passed'])
            entry_signal_passed = sum(1 for r in entry_signal_results if r['passed'])
            
            open_range_success = (low_violation_passed == len(low_violation_results) and 
                                 high_tracking_passed == len(high_tracking_results) and
                                 entry_signal_passed == len(entry_signal_results))
            
            self.test_results['open_range_monitoring'] = {
                'success': open_range_success,
                'module': 'OpenRangeMonitoringTest',
                'description': 'High tracking and low violation detection',
                'low_violation_passed': low_violation_passed,
                'low_violation_total': len(low_violation_results),
                'high_tracking_passed': high_tracking_passed,
                'high_tracking_total': len(high_tracking_results),
                'entry_signal_passed': entry_signal_passed,
                'entry_signal_total': len(entry_signal_results)
            }
        except Exception as e:
            logger.error(f"Open range monitoring test failed: {e}")
            self.test_results['open_range_monitoring'] = {
                'success': False,
                'module': 'OpenRangeMonitoringTest',
                'description': 'High tracking and low violation detection',
                'error': str(e)
            }

        self.end_time = datetime.now()
        self._print_comprehensive_report()

    def _print_comprehensive_report(self):
        """Print comprehensive test report"""
        print("\n" + "="*70)
        print("COMPREHENSIVE SVRO TEST SUITE RESULTS")
        print("="*70)

        # Test execution summary
        print(f"\n⏱️  TEST EXECUTION SUMMARY:")
        print(f"  Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Duration: {(self.end_time - self.start_time).total_seconds():.2f} seconds")

        # Module results
        print(f"\n📊 MODULE TEST RESULTS:")
        total_modules = len(self.test_results)
        passed_modules = sum(1 for result in self.test_results.values() if result['success'])
        
        for module, result in self.test_results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} {result['module']}")
            print(f"     Description: {result['description']}")
            print(f"     Result: {'SUCCESS' if result['success'] else 'FAILED'}")
            
            if 'error' in result:
                print(f"     Error: {result['error']}")
            
            # Detailed results for specific modules
            if module == 'volume_tracking':
                print(f"     Volume Accumulation: {result['accumulation_passed']}/{result['accumulation_total']} passed")
                print(f"     Volume Timing: {result['timing_passed']}/{result['timing_total']} passed")
            elif module == 'open_range_monitoring':
                print(f"     Low Violation: {result['low_violation_passed']}/{result['low_violation_total']} passed")
                print(f"     High Tracking: {result['high_tracking_passed']}/{result['high_tracking_total']} passed")
                print(f"     Entry Signal: {result['entry_signal_passed']}/{result['entry_signal_total']} passed")
            print()

        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"  Total Modules: {total_modules}")
        print(f"  Passed Modules: {passed_modules}")
        print(f"  Failed Modules: {total_modules - passed_modules}")
        print(f"  Success Rate: {passed_modules/total_modules*100:.1f}%")

        # Critical functionality validation
        print(f"\n🔍 CRITICAL SVRO FUNCTIONALITY VALIDATION:")

        # Volume validation (7.5% requirement)
        volume_result = self.test_results.get('volume_tracking', {})
        if volume_result.get('success', False):
            print(f"  ✅ Volume validation (7.5% requirement) - WORKING")
        else:
            print(f"  ❌ Volume validation (7.5% requirement) - FAILED")

        # Gap validation (0.3% minimum)
        realistic_result = self.test_results.get('realistic_conditions', {})
        if realistic_result.get('success', False):
            print(f"  ✅ Gap validation (0.3% minimum) - WORKING")
        else:
            print(f"  ❌ Gap validation (0.3% minimum) - FAILED")

        # Low violation detection (1% threshold)
        open_range_result = self.test_results.get('open_range_monitoring', {})
        if open_range_result.get('success', False):
            print(f"  ✅ Low violation detection (1% threshold) - WORKING")
        else:
            print(f"  ❌ Low violation detection (1% threshold) - FAILED")

        # Entry signal generation
        if open_range_result.get('success', False):
            print(f"  ✅ Entry signal generation - WORKING")
        else:
            print(f"  ❌ Entry signal generation - FAILED")

        # Final verdict
        overall_success = passed_modules == total_modules
        
        print("\n" + "="*70)
        if overall_success:
            print("🎉 COMPREHENSIVE SVRO TEST SUITE PASSED!")
            print("All SVRO continuation system components are working correctly:")
            print("  ✅ Volume tracking and 7.5% validation")
            print("  ✅ Gap validation (0.3% minimum)")
            print("  ✅ Low violation detection (1% threshold)")
            print("  ✅ High tracking during monitoring window")
            print("  ✅ Entry signal generation")
            print("  ✅ Realistic market condition handling")
            print("\nThe SVRO system is ready for live trading!")
        else:
            print("❌ SOME SVRO TESTS FAILED!")
            print("Issues detected that need to be addressed before live trading:")
            
            failed_modules = [module for module, result in self.test_results.items() if not result['success']]
            for module in failed_modules:
                print(f"  - {self.test_results[module]['module']}: {self.test_results[module]['description']}")
            
            print("\nPlease review the failed tests and fix the issues before proceeding.")

        print("\n" + "="*70)
        print("Test logs saved to:")
        print("  - comprehensive_svro_test.log")
        print("  - realistic_svro_test.log")
        print("  - volume_tracking_test.log")
        print("  - open_range_test.log")

        return overall_success


def main():
    """Main test runner"""
    runner = ComprehensiveSVROTestRunner()
    success = runner.run_all_tests()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)