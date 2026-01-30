#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test runner for OOPS entry testing
Quick way to verify the reversal bot entry logic is working
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def main():
    """Run the OOPS entry test"""
    print("🎯 OOPS Entry Test Runner")
    print("=" * 50)
    print()
    
    try:
        # Import the test module
        from src.trading.live_trading.testing_section.dummy_tick_streamer import run_oops_entry_test
        
        # Run the test
        print("Running OOPS entry test...")
        print("This will simulate a stock with:")
        print("- Previous Close: 100.00")
        print("- Open Price: 95.00 (gap down)")
        print("- Expected Entry: When price crosses 100.00")
        print()
        
        results = run_oops_entry_test()
        
        # Check results
        if results['triggered_entries'] > 0:
            print("\n✅ OOPS ENTRY TEST PASSED!")
            print("The reversal bot correctly triggered entry when price crossed previous close.")
        else:
            print("\n❌ OOPS ENTRY TEST FAILED!")
            print("No entries were triggered. Check the entry logic.")
            
        return results['triggered_entries'] > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required modules are available")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)