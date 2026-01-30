#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive SVRO Test Runner
Runs all SVRO test scenarios to validate the continuation bot architecture
"""

import sys
import os
import time
from datetime import datetime
from typing import Dict, List
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import test scenarios
from test_scenarios.svro_gap_validation import test_svro_gap_validation
from test_scenarios.svro_volume_validation import test_svro_volume_validation
from test_scenarios.svro_entry_trigger import test_svro_entry_trigger
from run_svro_test import SVROTest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ComprehensiveSVROTest')


def run_comprehensive_svro_test():
    """Run all SVRO test scenarios"""
    print("🚀 Starting Comprehensive SVRO Test Suite")
    print("=" * 60)
    print("Testing: Complete SVRO continuation bot architecture")
    print("Components: Gap validation, Volume validation, Entry triggers, Full workflow")
    print()
    
    test_results = []
    
    # Test 1: SVRO Gap Validation
    print("📋 Test 1: SVRO Gap Validation")
    print("-" * 40)
    try:
        gap_success = test_svro_gap_validation()
        test_results.append({
            'test': 'Gap Validation',
            'success': gap_success,
            'description': 'Tests SVRO gap up requirements (0.3% to 5%)'
        })
    except Exception as e:
        logger.error(f"Gap validation test failed: {e}")
        test_results.append({
            'test': 'Gap Validation',
            'success': False,
            'description': 'Tests SVRO gap up requirements (0.3% to 5%)',
            'error': str(e)
        })
    
    print()
    
    # Test 2: SVRO Volume Validation
    print("📋 Test 2: SVRO Volume Validation")
    print("-" * 40)
    try:
        volume_success = test_svro_volume_validation()
        test_results.append({
            'test': 'Volume Validation',
            'success': volume_success,
            'description': 'Tests SVRO volume threshold (7.5% of baseline)'
        })
    except Exception as e:
        logger.error(f"Volume validation test failed: {e}")
        test_results.append({
            'test': 'Volume Validation',
            'success': False,
            'description': 'Tests SVRO volume threshold (7.5% of baseline)',
            'error': str(e)
        })
    
    print()
    
    # Test 3: SVRO Entry Trigger
    print("📋 Test 3: SVRO Entry Trigger")
    print("-" * 40)
    try:
        trigger_success = test_svro_entry_trigger()
        test_results.append({
            'test': 'Entry Trigger',
            'success': trigger_success,
            'description': 'Tests SVRO entry trigger logic (price breaking entry high)'
        })
    except Exception as e:
        logger.error(f"Entry trigger test failed: {e}")
        test_results.append({
            'test': 'Entry Trigger',
            'success': False,
            'description': 'Tests SVRO entry trigger logic (price breaking entry high)',
            'error': str(e)
        })
    
    print()
    
    # Test 4: Full SVRO Workflow
    print("📋 Test 4: Full SVRO Workflow")
    print("-" * 40)
    try:
        workflow_test = SVROTest()
        workflow_success = workflow_test.run_test()
        test_results.append({
            'test': 'Full Workflow',
            'success': workflow_success,
            'description': 'Tests complete SVRO workflow with simulated data'
        })
    except Exception as e:
        logger.error(f"Full workflow test failed: {e}")
        test_results.append({
            'test': 'Full Workflow',
            'success': False,
            'description': 'Tests complete SVRO workflow with simulated data',
            'error': str(e)
        })
    
    # Print comprehensive results
    print("\n" + "="*60)
    print("COMPREHENSIVE SVRO TEST RESULTS")
    print("="*60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{i}. {status} {result['test']}")
        print(f"   {result['description']}")
        if not result['success'] and 'error' in result:
            print(f"   Error: {result['error']}")
        if result['success']:
            passed_tests += 1
        print()
    
    print(f"Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL SVRO TESTS PASSED!")
        print("✅ SVRO continuation bot architecture is working correctly")
        print("✅ Gap validation, volume validation, and entry triggers all functional")
        return True
    else:
        print("❌ SOME SVRO TESTS FAILED!")
        print(f"⚠️  {total_tests - passed_tests} test(s) need attention")
        return False


def main():
    """Main comprehensive SVRO test runner"""
    start_time = time.time()
    
    try:
        success = run_comprehensive_svro_test()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️  Test suite completed in {duration:.2f} seconds")
        
        return success
        
    except Exception as e:
        logger.error(f"Comprehensive SVRO test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)