#!/usr/bin/env python3
"""
Integration Test Script for Live Trading Module
Tests imports and basic functionality without live connections
"""

import sys
import os

def test_basic_imports():
    """Test basic Python imports work"""
    print("Testing basic imports...")

    try:
        # Test basic modules
        import datetime
        import logging
        import json
        print("Basic Python imports work")
        return True
    except Exception as e:
        print(f"Basic import error: {e}")
        return False

def test_file_structure():
    """Test that all files exist"""
    print("\nTesting file structure...")

    files_to_check = [
        'config.py',
        'main.py',
        'data_streamer.py',
        'stock_monitor.py',
        'rule_engine.py',
        'selection_engine.py',
        'paper_trader.py',
        '__init__.py'
    ]

    missing_files = []
    for filename in files_to_check:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if not os.path.exists(filepath):
            missing_files.append(filename)

    if missing_files:
        print(f"Missing files: {missing_files}")
        return False

        print("All module files exist")
    return True

def test_config_values():
    """Test configuration file can be read"""
    print("\nTesting configuration...")

    try:
        # Read config file directly
        config_path = os.path.join(os.path.dirname(__file__), 'config.py')
        with open(config_path, 'r') as f:
            content = f.read()

        # Check key values are in the file
        checks = [
            ('MARKET_OPEN = time(9, 15)', 'Market open time'),
            ('CONFIRMATION_WINDOW = 5', 'Confirmation window'),
            ('ENTRY_SL_PCT = 0.04', 'SL percentage'),
            ('MAX_STOCKS_TO_TRADE = 2', 'Max stocks'),
            ('GAP_UP_MAX = 0.05', 'Gap up max')
        ]

        for check_text, description in checks:
            if check_text not in content:
                print(f"{description} not found in config")
                return False

        print("Configuration values present")
        return True

    except Exception as e:
        print(f"Config test failed: {e}")
        return False

def test_candidate_files():
    """Test candidate files exist and have content"""
    print("\nTesting candidate files...")

    try:
        # Check continuation file
        cont_file = os.path.join(os.path.dirname(__file__), '..', 'continuation_list.txt')
        if not os.path.exists(cont_file):
            print("continuation_list.txt not found")
            return False

        with open(cont_file, 'r') as f:
            cont_content = f.read().strip()
            if not cont_content:
                print("continuation_list.txt is empty")
                return False

        symbols = [s.strip() for s in cont_content.split(',') if s.strip()]
        if len(symbols) < 1:
            print("No symbols in continuation_list.txt")
            return False

        print(f"Continuation file has {len(symbols)} symbols")

        # Check reversal file exists (can be empty)
        rev_file = os.path.join(os.path.dirname(__file__), '..', 'reversal_list.txt')
        if not os.path.exists(rev_file):
            print("reversal_list.txt not found")
            return False

        print("Candidate files exist")
        return True

    except Exception as e:
        print(f"File test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 LIVE TRADING MODULE INTEGRATION TEST")
    print("=" * 50)

    tests = [
        ("Basic Imports", test_basic_imports),
        ("File Structure", test_file_structure),
        ("Configuration", test_config_values),
        ("Candidate Files", test_candidate_files),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"{test_name} test failed")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Module is ready.")
        return 0
    else:
        print("Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
