#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strong Start Test Runner
Executes the Strong Start entry test
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Test_Environment.strong_start_test import run_strong_start_test


def main():
    """Main test runner"""
    print("🎯 STRONG START ENTRY TEST RUNNER")
    print("=" * 50)
    print()
    
    try:
        success = run_strong_start_test()
        
        print("\n" + "="*50)
        if success:
            print("🎉 STRONG START TEST COMPLETED SUCCESSFULLY!")
            print("The Strong Start entry logic is working correctly.")
        else:
            print("❌ STRONG START TEST FAILED!")
            print("There may be issues with the Strong Start entry logic.")
        print("="*50)
        
        return success
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)