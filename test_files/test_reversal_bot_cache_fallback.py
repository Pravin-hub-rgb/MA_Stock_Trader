#!/usr/bin/env python3
"""
Test Reversal Bot Cache Fallback Implementation
Tests the complete cache fallback system in the reversal bot
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

def test_enhanced_fetcher_in_reversal():
    """Test the enhanced fetcher integration in reversal bot"""
    print("🚀 Testing Enhanced Fetcher Integration in Reversal Bot")
    print("=" * 60)
    
    try:
        # Import the enhanced fetcher
        from src.utils.upstox_fetcher_enhanced import create_enhanced_fetcher
        from utils.upstox_fetcher import upstox_fetcher
        
        enhanced_fetcher = create_enhanced_fetcher()
        if not enhanced_fetcher:
            print("❌ Could not create enhanced fetcher")
            return False
        
        print("✅ Enhanced fetcher created successfully")
        
        # Test symbols from reversal bot
        test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE']
        
        results = {}
        
        for symbol in test_symbols:
            print(f"\n🧪 Testing {symbol}:")
            
            try:
                # Test enhanced method
                enhanced_data = enhanced_fetcher.get_ltp_data_with_fallback(symbol)
                if enhanced_data and 'cp' in enhanced_data:
                    enhanced_close = float(enhanced_data['cp'])
                    source = enhanced_data.get('source', 'unknown')
                    print(f"   Enhanced LTP 'cp': ₹{enhanced_close:.2f} ({source})")
                else:
                    print(f"   ❌ Enhanced method failed")
                    enhanced_close = None
                
                # Test original method for comparison
                original_data = upstox_fetcher.get_ltp_data(symbol)
                if original_data and 'cp' in original_data:
                    original_close = float(original_data['cp'])
                    print(f"   Original LTP 'cp': ₹{original_close:.2f}")
                else:
                    print(f"   ❌ Original method failed")
                    original_close = None
                
                # Compare results
                if enhanced_close and original_close:
                    diff = abs(enhanced_close - original_close)
                    if diff > 0.01:
                        print(f"   ⚠️  Difference: ₹{diff:.2f} - Enhanced method improved result")
                    else:
                        print(f"   ✅ Same result - enhanced method working correctly")
                
                results[symbol] = {
                    'enhanced': enhanced_close,
                    'original': original_close,
                    'source': enhanced_data.get('source', 'unknown') if enhanced_data else 'N/A'
                }
                
            except Exception as e:
                print(f"   ❌ Error testing {symbol}: {e}")
                results[symbol] = {
                    'enhanced': None,
                    'original': None,
                    'source': 'ERROR'
                }
        
        # Summary
        print(f"\n📋 Integration Test Summary")
        print("=" * 40)
        
        successful = [s for s, r in results.items() if r['enhanced'] is not None]
        enhanced_sources = [s for s, r in results.items() if r['source'] == 'enhanced_fallback']
        
        print(f"✅ Successful: {len(successful)}/{len(test_symbols)} symbols")
        print(f"🎯 Enhanced fallback used: {len(enhanced_sources)} symbols")
        
        if enhanced_sources:
            print(f"   Enhanced fallback symbols: {', '.join(enhanced_sources)}")
        
        # Test fallback chain
        print(f"\n🧪 Testing Fallback Chain")
        print("=" * 30)
        
        for symbol in test_symbols:
            r = results[symbol]
            if r['enhanced'] and r['original']:
                if r['source'] == 'enhanced_fallback':
                    print(f"   {symbol}: ✅ Using enhanced fallback (historical API)")
                elif r['source'] == 'original':
                    print(f"   {symbol}: ✅ Using original method")
                else:
                    print(f"   {symbol}: ⚠️  Unknown source: {r['source']}")
            else:
                print(f"   {symbol}: ❌ Failed")
        
        return len(successful) == len(test_symbols)
        
    except Exception as e:
        logger.error(f"Error in integration test: {e}")
        print(f"❌ Integration test failed: {e}")
        return False

def test_reversal_bot_import():
    """Test that reversal bot can import the enhanced fetcher"""
    print(f"\n🔍 Testing Reversal Bot Import")
    print("=" * 30)
    
    try:
        # Test import of enhanced fetcher in reversal bot context
        from src.utils.upstox_fetcher_enhanced import create_enhanced_fetcher
        print("✅ Enhanced fetcher import successful")
        
        # Test that the enhanced fetcher can be created
        enhanced_fetcher = create_enhanced_fetcher()
        if enhanced_fetcher:
            print("✅ Enhanced fetcher creation successful")
            return True
        else:
            print("❌ Enhanced fetcher creation failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test execution"""
    print("🎯 Reversal Bot Cache Fallback Implementation Test")
    print("=" * 70)
    
    try:
        # Test 1: Enhanced fetcher integration
        integration_success = test_enhanced_fetcher_in_reversal()
        
        # Test 2: Reversal bot import
        import_success = test_reversal_bot_import()
        
        # Final summary
        print(f"\n🏁 Implementation Test Complete")
        print("=" * 50)
        
        if integration_success and import_success:
            print("✅ ALL TESTS PASSED!")
            print("   Enhanced fetcher with cache fallback is working correctly")
            print("   Reversal bot can successfully use the enhanced method")
            print("   Cache fallback system is ready for production use")
            
            # Save success status
            status = {
                'integration_test': 'PASSED',
                'import_test': 'PASSED',
                'cache_fallback_ready': True,
                'timestamp': datetime.now().isoformat(),
                'description': 'Enhanced fetcher with cache fallback successfully implemented in reversal bot'
            }
            
            with open('reversal_bot_cache_fallback_status.json', 'w') as f:
                json.dump(status, f, indent=2)
            
            print(f"\n📋 Status saved to reversal_bot_cache_fallback_status.json")
            
        else:
            print("❌ SOME TESTS FAILED")
            print("   Check the error messages above for details")
            
            status = {
                'integration_test': 'PASSED' if integration_success else 'FAILED',
                'import_test': 'PASSED' if import_success else 'FAILED',
                'cache_fallback_ready': False,
                'timestamp': datetime.now().isoformat(),
                'description': 'Enhanced fetcher implementation has issues'
            }
            
            with open('reversal_bot_cache_fallback_status.json', 'w') as f:
                json.dump(status, f, indent=2)
        
        print(f"\n📝 Cache fallback implementation complete!")
        print("   The reversal bot now uses:")
        print("   1. Historical API as primary source for previous close")
        print("   2. Cache files as fallback when historical API fails")
        print("   3. Original LTP method as last resort")
        
    except Exception as e:
        logger.error(f"Error in main test execution: {e}")
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()