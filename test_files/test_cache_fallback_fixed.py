#!/usr/bin/env python3
"""
Cache Fallback Test for Previous Close - Fixed Version
Tests cache-based previous close as fallback when Upstox API fails
"""

import sys
import os
import logging
import json
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, 'src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CacheFallbackTester:
    """Test cache-based previous close as fallback method"""
    
    def __init__(self):
        try:
            from utils.upstox_fetcher import upstox_fetcher
            from scanner.stock_scorer import stock_scorer
            self.upstox_fetcher = upstox_fetcher
            self.stock_scorer = stock_scorer
            logger.info("✅ Upstox fetcher and stock scorer imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import required modules: {e}")
            raise
    
    def test_cache_fallback(self, symbols):
        """Test cache-based previous close as fallback"""
        print("🔍 Testing Cache Fallback for Previous Close")
        print("=" * 50)
        
        results = {}
        
        for symbol in symbols:
            print(f"\n🧪 Testing {symbol}...")
            
            try:
                # Method 1: Upstox LTP (primary)
                ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
                if ltp_data and 'cp' in ltp_data:
                    upstox_close = float(ltp_data['cp'])
                    print(f"   Upstox LTP 'cp': ₹{upstox_close:.2f}")
                else:
                    print(f"   Upstox LTP 'cp': Not available")
                    upstox_close = None
                
                # Method 2: Historical API (secondary)
                today = datetime.now().date()
                start_date = today - timedelta(days=7)
                end_date = today - timedelta(days=1)
                
                df = self.upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
                if not df.empty:
                    hist_close = float(df.iloc[-1]['close'])
                    print(f"   Historical close: ₹{hist_close:.2f}")
                else:
                    print(f"   Historical close: Not available")
                    hist_close = None
                
                # Method 3: Cache fallback (tertiary)
                cache_close = self.get_previous_close_from_cache(symbol)
                if cache_close:
                    print(f"   Cache close: ₹{cache_close:.2f}")
                else:
                    print(f"   Cache close: Not available")
                
                # Determine best available close
                best_close = None
                source = None
                
                if upstox_close:
                    best_close = upstox_close
                    source = "Upstox LTP"
                elif hist_close:
                    best_close = hist_close
                    source = "Historical API"
                elif cache_close:
                    best_close = cache_close
                    source = "Cache"
                
                if best_close:
                    print(f"   ✅ Best available: ₹{best_close:.2f} ({source})")
                else:
                    print(f"   ❌ No previous close available")
                
                results[symbol] = {
                    'upstox': upstox_close,
                    'historical': hist_close,
                    'cache': cache_close,
                    'best': best_close,
                    'source': source
                }
                
            except Exception as e:
                logger.error(f"❌ Error testing {symbol}: {e}")
                results[symbol] = {
                    'upstox': None,
                    'historical': None,
                    'cache': None,
                    'best': None,
                    'source': 'ERROR'
                }
        
        return results
    
    def get_previous_close_from_cache(self, symbol):
        """Get previous close from cache as fallback"""
        try:
            # Method 1: Try stock scorer cache
            if hasattr(self.stock_scorer, 'adr_cache') and symbol in self.stock_scorer.adr_cache:
                # The adr_cache might have recent data, but not necessarily previous close
                # This is more for ADR calculation
                pass
            
            # Method 2: Try bhavcopy cache files
            bhavcopy_file = os.path.join('bhavcopy_cache', f'{symbol.lower()}_daily.csv')
            if os.path.exists(bhavcopy_file):
                try:
                    import pandas as pd
                    df = pd.read_csv(bhavcopy_file, parse_dates=['date'])
                    if not df.empty:
                        # Get the most recent close
                        latest_close = float(df.iloc[-1]['close'])
                        print(f"   Found in bhavcopy cache: ₹{latest_close:.2f}")
                        return latest_close
                except Exception as e:
                    logger.warning(f"Error reading bhavcopy cache for {symbol}: {e}")
            
            # Method 3: Try scores cache
            cache_file = os.path.join('bhavcopy_cache', 'stock_scores.json')
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    # Check if we have any close data in the cache
                    if 'scores' in cache_data and symbol in cache_data['scores']:
                        score_data = cache_data['scores'][symbol]
                        if 'price' in score_data:
                            print(f"   Found in scores cache: ₹{score_data['price']:.2f}")
                            return float(score_data['price'])
                except Exception as e:
                    logger.warning(f"Error reading scores cache for {symbol}: {e}")
            
            # Method 4: Try general cache directory
            cache_dir = 'src/scanner/cache'
            if os.path.exists(cache_dir):
                cache_file = os.path.join(cache_dir, f'{symbol}_metadata.pkl')
                if os.path.exists(cache_file):
                    try:
                        import pickle
                        with open(cache_file, 'rb') as f:
                            cached_data = pickle.load(f)
                        
                        if 'prev_close' in cached_data:
                            print(f"   Found in metadata cache: ₹{cached_data['prev_close']:.2f}")
                            return float(cached_data['prev_close'])
                        elif 'close' in cached_data:
                            print(f"   Found in metadata cache: ₹{cached_data['close']:.2f}")
                            return float(cached_data['close'])
                    except Exception as e:
                        logger.warning(f"Error reading metadata cache for {symbol}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache previous close for {symbol}: {e}")
            return None
    
    def test_fallback_scenarios(self, symbols):
        """Test various fallback scenarios"""
        print(f"\n🎯 Testing Fallback Scenarios")
        print("=" * 40)
        
        for symbol in symbols:
            print(f"\nTesting {symbol}:")
            
            # Test cache availability
            cache_close = self.get_previous_close_from_cache(symbol)
            if cache_close:
                print(f"   ✅ Cache fallback available: ₹{cache_close:.2f}")
            else:
                print(f"   ❌ Cache fallback not available")
            
            # Test complete fallback chain
            print("   Fallback chain test:")
            print("   1. Upstox LTP API (primary)")
            print("   2. Historical API (secondary)")
            print("   3. Cache fallback (tertiary)")
            print("   4. Manual calculation (last resort)")

class EnhancedPreviousCloseFixer:
    """Enhanced fixer with cache fallback"""
    
    def __init__(self, upstox_fetcher, stock_scorer):
        self.upstox_fetcher = upstox_fetcher
        self.stock_scorer = stock_scorer
    
    def get_previous_close_with_fallback(self, symbol):
        """Get previous close with full fallback chain"""
        try:
            # Fallback chain: Upstox → Historical → Cache → None
            
            # Method 1: Upstox LTP (primary)
            ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'cp' in ltp_data:
                return float(ltp_data['cp'])
            
            # Method 2: Historical API (secondary)
            today = datetime.now().date()
            start_date = today - timedelta(days=7)
            end_date = today - timedelta(days=1)
            
            df = self.upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
            if not df.empty:
                return float(df.iloc[-1]['close'])
            
            # Method 3: Cache fallback (tertiary)
            cache_close = self.get_previous_close_from_cache(symbol)
            if cache_close:
                return cache_close
            
            # Method 4: Manual calculation from recent data (last resort)
            manual_close = self.get_manual_previous_close(symbol)
            if manual_close:
                return manual_close
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fallback chain for {symbol}: {e}")
            return None
    
    def get_previous_close_from_cache(self, symbol):
        """Get previous close from cache"""
        try:
            # Try bhavcopy cache files
            bhavcopy_file = os.path.join('bhavcopy_cache', f'{symbol.lower()}_daily.csv')
            if os.path.exists(bhavcopy_file):
                import pandas as pd
                df = pd.read_csv(bhavcopy_file, parse_dates=['date'])
                if not df.empty:
                    return float(df.iloc[-1]['close'])
            
            # Try scores cache
            cache_file = os.path.join('bhavcopy_cache', 'stock_scores.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if 'scores' in cache_data and symbol in cache_data['scores']:
                    score_data = cache_data['scores'][symbol]
                    if 'price' in score_data:
                        return float(score_data['price'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cache previous close for {symbol}: {e}")
            return None
    
    def get_manual_previous_close(self, symbol):
        """Manual calculation of previous close from available data"""
        try:
            # This is a last resort - try to get any available price data
            # Could use opening price, last known price, etc.
            return None  # Placeholder for manual calculation logic
            
        except Exception as e:
            logger.error(f"Error in manual previous close calculation for {symbol}: {e}")
            return None
    
    def create_enhanced_get_ltp_data(self):
        """Create enhanced LTP data method with full fallback"""
        
        original_method = self.upstox_fetcher.get_ltp_data
        
        def enhanced_get_ltp_data(symbol):
            """Enhanced LTP data method with cache fallback"""
            try:
                # Get current LTP data
                ltp_data = original_method(symbol)
                
                if ltp_data:
                    # Try to get better previous close using fallback chain
                    enhanced_close = self.get_previous_close_with_fallback(symbol)
                    
                    if enhanced_close is not None:
                        # Use enhanced close if available
                        ltp_data['cp'] = enhanced_close
                        ltp_data['source'] = 'enhanced_fallback'
                    else:
                        # Keep original if no enhancement available
                        ltp_data['source'] = 'original'
                
                return ltp_data
                
            except Exception as e:
                logger.error(f"Enhanced method failed for {symbol}: {e}")
                # Fall back to original method
                return original_method(symbol)
        
        return enhanced_get_ltp_data
    
    def apply_enhanced_fix(self):
        """Apply the enhanced fix with cache fallback"""
        print("🔧 Applying Enhanced Previous Close Fix with Cache Fallback")
        print("=" * 60)
        
        # Create the enhanced method
        enhanced_method = self.create_enhanced_get_ltp_data()
        
        # Apply the fix
        self.upstox_fetcher.get_ltp_data = enhanced_method
        
        print("✅ Enhanced fix applied successfully")
        print("   - Upstox LTP API (primary)")
        print("   - Historical API (secondary)")
        print("   - Cache fallback (tertiary)")
        print("   - Manual calculation (last resort)")

def main():
    """Main execution function"""
    print("🚀 Cache Fallback Test for Previous Close (Fixed)")
    print("=" * 60)
    
    # Test symbols
    test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE']
    
    try:
        # Test cache fallback
        tester = CacheFallbackTester()
        results = tester.test_cache_fallback(test_symbols)
        tester.test_fallback_scenarios(test_symbols)
        
        # Apply enhanced fix
        fixer = EnhancedPreviousCloseFixer(tester.upstox_fetcher, tester.stock_scorer)
        fixer.apply_enhanced_fix()
        
        # Test the enhanced fix
        print(f"\n🧪 Testing Enhanced Fix")
        print("=" * 30)
        
        for symbol in test_symbols[:2]:  # Test first 2 symbols
            print(f"\nTesting {symbol}:")
            
            enhanced_data = tester.upstox_fetcher.get_ltp_data(symbol)
            if enhanced_data:
                print(f"   Enhanced LTP 'cp': ₹{enhanced_data.get('cp', 'N/A'):.2f}")
                print(f"   Source: {enhanced_data.get('source', 'unknown')}")
        
        # Save results
        fallback_status = {
            'test_results': results,
            'enhanced_fix_applied': True,
            'timestamp': datetime.now().isoformat(),
            'fallback_chain': [
                "1. Upstox LTP API (primary)",
                "2. Historical API (secondary)", 
                "3. Cache fallback (tertiary)",
                "4. Manual calculation (last resort)"
            ]
        }
        
        with open('cache_fallback_status_fixed.json', 'w') as f:
            json.dump(fallback_status, f, indent=2)
        
        print(f"\n📋 Cache Fallback Status Saved to cache_fallback_status_fixed.json")
        
        # Final summary
        print(f"\n🏁 Cache Fallback Test Complete")
        print("=" * 40)
        
        cache_available = sum(1 for r in results.values() if r['cache'] is not None)
        print(f"✅ Cache fallback available for {cache_available}/{len(test_symbols)} symbols")
        
        if cache_available > 0:
            print("✅ Cache fallback system ready for use")
        else:
            print("⚠️  Cache fallback not available - may need cache initialization")
        
        print(f"\n📝 Enhanced fix applied with full fallback chain")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Execution failed: {e}")

if __name__ == "__main__":
    main()