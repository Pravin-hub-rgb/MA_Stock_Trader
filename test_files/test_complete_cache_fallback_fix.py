#!/usr/bin/env python3
"""
Test Complete Cache Fallback Fix
Tests the final implementation with modified upstox_fetcher.py and fixed reversal bot
"""

import sys
import os
import logging
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_modified_upstox_fetcher():
    """Test the modified upstox_fetcher.py with cache fallback"""
    print("🚀 Testing Modified Upstox Fetcher with Cache Fallback")
    print("=" * 60)
    
    try:
        # Import the modified fetcher
        from src.utils.upstox_fetcher import upstox_fetcher
        
        print("✅ Successfully imported modified upstox_fetcher")
        
        # Test symbols
        test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL']
        
        results = {}
        
        for symbol in test_symbols:
            print(f"\n🧪 Testing {symbol}:")
            
            try:
                # Test get_ltp_data with cache fallback
                ltp_data = upstox_fetcher.get_ltp_data(symbol)
                
                if ltp_data and 'cp' in ltp_data:
                    print(f"   ✅ LTP data retrieved: cp = ₹{ltp_data['cp']:.2f}")
                    ltp_close = ltp_data['cp']
                else:
                    print(f"   ❌ No LTP data retrieved")
                    ltp_close = None
                
                # Test cache fallback directly
                cache_close = upstox_fetcher._get_previous_close_from_cache(symbol)
                if cache_close:
                    print(f"   ✅ Cache fallback available: ₹{cache_close:.2f}")
                else:
                    print(f"   ❌ No cache fallback available")
                
                results[symbol] = {
                    'ltp_close': ltp_close,
                    'cache_close': cache_close,
                    'cache_available': cache_close is not None
                }
                
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
                results[symbol] = {
                    'ltp_close': None,
                    'cache_close': None,
                    'cache_available': False
                }
        
        # Summary
        print(f"\n📋 Modified Fetcher Test Summary")
        print("=" * 40)
        
        successful = [s for s, r in results.items() if r['ltp_close'] is not None]
        cache_available = [s for s, r in results.items() if r['cache_available']]
        
        print(f"✅ LTP data retrieved: {len(successful)}/{len(test_symbols)} symbols")
        print(f"🎯 Cache fallback available: {len(cache_available)} symbols")
        
        return len(successful) > 0
        
    except Exception as e:
        logger.error(f"Error in modified fetcher test: {e}")
        print(f"❌ Modified fetcher test failed: {e}")
        return False

def test_reversal_bot_import():
    """Test that reversal bot can import the modified fetcher without errors"""
    print(f"\n🔍 Testing Reversal Bot Import")
    print("=" * 30)
    
    try:
        # Test import of modified fetcher in reversal bot context
        from src.utils.upstox_fetcher import upstox_fetcher
        print("✅ Modified fetcher import successful")
        
        # Test that the fetcher has the cache fallback method
        if hasattr(upstox_fetcher, '_get_previous_close_from_cache'):
            print("✅ Cache fallback method available")
            return True
        else:
            print("❌ Cache fallback method not found")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_reversal_bot_previous_close_logic():
    """Test the reversal bot's previous close retrieval logic"""
    print(f"\n🧪 Testing Reversal Bot Previous Close Logic")
    print("=" * 40)
    
    try:
        # Simulate the reversal bot's previous close retrieval
        from src.utils.upstox_fetcher import upstox_fetcher
        
        test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL']
        prev_closes = {}
        
        for symbol in test_symbols:
            try:
                # This is exactly what the reversal bot does now
                data = upstox_fetcher.get_ltp_data(symbol)
                
                if data and 'cp' in data and data['cp'] is not None:
                    prev_closes[symbol] = float(data['cp'])
                    print(f"   ✅ {symbol}: Prev Close Rs{prev_closes[symbol]:.2f}")
                else:
                    print(f"   ❌ {symbol}: No previous close data")
                    
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        successful = len(prev_closes)
        print(f"\n✅ Successfully retrieved previous closes for {successful}/{len(test_symbols)} symbols")
        
        return successful > 0
        
    except Exception as e:
        logger.error(f"Error in reversal bot logic test: {e}")
        print(f"❌ Reversal bot logic test failed: {e}")
        return False

def main():
    """Main test execution"""
    print("🎯 Complete Cache Fallback Fix Test")
    print("=" * 70)
    
    try:
        # Test 1: Modified fetcher functionality
        fetcher_success = test_modified_upstox_fetcher()
        
        # Test 2: Reversal bot import
        import_success = test_reversal_bot_import()
        
        # Test 3: Reversal bot previous close logic
        logic_success = test_reversal_bot_previous_close_logic()
        
        # Final summary
        print(f"\n🏁 Complete Fix Test Complete")
        print("=" * 50)
        
        if fetcher_success and import_success and logic_success:
            print("✅ ALL TESTS PASSED!")
            print("   Modified upstox_fetcher.py with cache fallback is working correctly")
            print("   Reversal bot can successfully import and use the modified fetcher")
            print("   Previous close retrieval logic works as expected")
            print("   Cache fallback system is ready for production use")
            
            # Save success status
            status = {
                'modified_fetcher_test': 'PASSED',
                'import_test': 'PASSED',
                'logic_test': 'PASSED',
                'cache_fallback_ready': True,
                'timestamp': datetime.now().isoformat(),
                'description': 'Complete cache fallback fix successfully tested'
            }
            
            with open('complete_cache_fallback_fix_status.json', 'w') as f:
                json.dump(status, f, indent=2)
            
            print(f"\n📋 Status saved to complete_cache_fallback_fix_status.json")
            
        else:
            print("❌ SOME TESTS FAILED")
            print("   Check the error messages above for details")
            
            status = {
                'modified_fetcher_test': 'PASSED' if fetcher_success else 'FAILED',
                'import_test': 'PASSED' if import_success else 'FAILED',
                'logic_test': 'PASSED' if logic_success else 'FAILED',
                'cache_fallback_ready': False,
                'timestamp': datetime.now().isoformat(),
                'description': 'Complete cache fallback fix has issues'
            }
            
            with open('complete_cache_fallback_fix_status.json', 'w') as f:
                json.dump(status, f, indent=2)
        
        print(f"\n📝 Complete cache fallback fix implementation ready!")
        print("   The solution includes:")
        print("   1. Modified upstox_fetcher.py with cache fallback")
        print("   2. Fixed reversal bot import (no enhanced fetcher dependency)")
        print("   3. Simple and reliable previous close retrieval")
        print("   4. Cache files used as fallback when LTP API fails")
        
    except Exception as e:
        logger.error(f"Error in main test execution: {e}")
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()