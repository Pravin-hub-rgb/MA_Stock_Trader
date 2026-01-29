#!/usr/bin/env python3
"""
Previous Close Bug Test and Fix Script
Tests for stale previous close data and implements historical API fix
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

class PreviousCloseTester:
    """Test and fix previous close calculation issues"""
    
    def __init__(self):
        try:
            from utils.upstox_fetcher import upstox_fetcher
            self.upstox_fetcher = upstox_fetcher
            logger.info("✅ Upstox fetcher imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import upstox_fetcher: {e}")
            raise
    
    def test_ltp_vs_historical(self, symbols):
        """Test LTP vs Historical for discrepancies"""
        print("🔍 Testing LTP vs Historical Previous Close")
        print("=" * 50)
        
        results = {}
        
        for symbol in symbols:
            print(f"\n🧪 Testing {symbol}...")
            
            try:
                # Get LTP data
                ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
                if ltp_data and 'cp' in ltp_data:
                    ltp_close = float(ltp_data['cp'])
                    print(f"   LTP 'cp': ₹{ltp_close:.2f}")
                else:
                    print(f"   LTP 'cp': Not available")
                    ltp_close = None
                
                # Get historical data (last 7 days to ensure we get Friday's data)
                today = datetime.now().date()
                start_date = today - timedelta(days=7)
                end_date = today - timedelta(days=1)
                
                df = self.upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
                
                if not df.empty:
                    print(f"   Historical data found: {len(df)} days")
                    
                    # Show all historical closes
                    for date_idx, row in df.iterrows():
                        print(f"   {date_idx}: Close ₹{row['close']:.2f}")
                    
                    # Get most recent close
                    hist_close = float(df.iloc[-1]['close'])
                    print(f"   Historical close: ₹{hist_close:.2f}")
                    
                    # Compare
                    if ltp_close:
                        diff = abs(hist_close - ltp_close)
                        if diff > 0.01:
                            print(f"   ⚠️  DISCREPANCY: ₹{diff:.2f}")
                            results[symbol] = {
                                'status': 'DISCREPANCY',
                                'ltp': ltp_close,
                                'historical': hist_close,
                                'discrepancy': diff
                            }
                        else:
                            print(f"   ✅ MATCH")
                            results[symbol] = {
                                'status': 'MATCH',
                                'ltp': ltp_close,
                                'historical': hist_close,
                                'discrepancy': diff
                            }
                    else:
                        results[symbol] = {
                            'status': 'LTP_FAILED',
                            'ltp': None,
                            'historical': hist_close,
                            'discrepancy': None
                        }
                else:
                    print(f"   ❌ No historical data")
                    results[symbol] = {
                        'status': 'HISTORICAL_FAILED',
                        'ltp': ltp_close,
                        'historical': None,
                        'discrepancy': None
                    }
                    
            except Exception as e:
                logger.error(f"❌ Error testing {symbol}: {e}")
                results[symbol] = {
                    'status': 'ERROR',
                    'ltp': None,
                    'historical': None,
                    'discrepancy': None
                }
        
        return results
    
    def analyze_bug_scenario(self):
        """Analyze the specific bug scenario from the report"""
        print(f"\n🎯 Analyzing Bug Scenario")
        print("=" * 30)
        
        # From the bug report:
        # Current date: 27-01-2026 (Tuesday)
        # Should use: 23-01-2026 (Friday) close price
        # Actually using: 22-01-2026 (Thursday) close price
        
        symbol = 'ASHAPURMIN'
        print(f"Testing bug scenario for {symbol}:")
        print(f"Current date: 2026-01-27 (Tuesday)")
        print(f"Expected previous close: 2026-01-23 (Friday)")
        print(f"Bug would show: 2026-01-22 (Thursday)")
        
        # Get current LTP
        ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
        if ltp_data and 'cp' in ltp_data:
            ltp_close = float(ltp_data['cp'])
            print(f"Current LTP 'cp': ₹{ltp_close:.2f}")
            
            # Check if this matches Thursday's close (bug scenario)
            if abs(ltp_close - 750.75) < 0.01:  # Thursday's close
                print("   ⚠️  BUG DETECTED: Showing Thursday's close instead of Friday's!")
                return True
            elif abs(ltp_close - 681.60) < 0.01:  # Friday's close
                print("   ✅ CORRECT: Showing Friday's close")
                return False
            else:
                print(f"   ❓ UNEXPECTED: Close doesn't match expected values")
                return False
        else:
            print("   ❌ Cannot determine - LTP data not available")
            return False

class PreviousCloseFixer:
    """Implement the historical API fix for previous close"""
    
    def __init__(self, upstox_fetcher):
        self.upstox_fetcher = upstox_fetcher
    
    def get_previous_close_historical(self, symbol):
        """Get previous close using historical API (more reliable)"""
        try:
            # Get last 7 days to ensure we get the last trading day
            today = datetime.now().date()
            start_date = today - timedelta(days=7)
            end_date = today - timedelta(days=1)
            
            df = self.upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)
            
            if not df.empty:
                # Return the most recent close (last trading day)
                return float(df.iloc[-1]['close'])
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting historical previous close for {symbol}: {e}")
            return None
    
    def create_fixed_get_ltp_data(self):
        """Create a fixed version of get_ltp_data method"""
        
        original_method = self.upstox_fetcher.get_ltp_data
        
        def fixed_get_ltp_data(symbol):
            """Fixed LTP data method that uses historical API as primary source"""
            try:
                # Method 1: Try historical API (most accurate)
                hist_close = self.get_previous_close_historical(symbol)
                if hist_close is not None:
                    # Get current LTP data but use historical close for 'cp'
                    ltp_data = original_method(symbol)
                    if ltp_data:
                        ltp_data['cp'] = hist_close
                        return ltp_data
                
                # Method 2: Fall back to original method
                return original_method(symbol)
                
            except Exception as e:
                logger.error(f"All methods failed for {symbol}: {e}")
                return {}
        
        return fixed_get_ltp_data
    
    def apply_fix(self):
        """Apply the fix to the upstox fetcher"""
        print("🔧 Applying Previous Close Fix")
        print("=" * 30)
        
        # Create the fixed method
        fixed_method = self.create_fixed_get_ltp_data()
        
        # Backup the original method
        self.upstox_fetcher._original_get_ltp_data = self.upstox_fetcher.get_ltp_data
        
        # Apply the fix
        self.upstox_fetcher.get_ltp_data = fixed_method
        
        print("✅ Fix applied successfully")
        print("   - Historical API now used as primary source for previous close")
        print("   - Original method kept as fallback")
    
    def test_fix(self, symbols):
        """Test the fix with sample symbols"""
        print(f"\n🧪 Testing Fix Implementation")
        print("=" * 30)
        
        for symbol in symbols:
            print(f"\nTesting {symbol}:")
            
            # Test original method
            original_data = self.upstox_fetcher._original_get_ltp_data(symbol)
            if original_data and 'cp' in original_data:
                print(f"   Original LTP 'cp': ₹{original_data['cp']:.2f}")
            
            # Test fixed method
            fixed_data = self.upstox_fetcher.get_ltp_data(symbol)
            if fixed_data and 'cp' in fixed_data:
                print(f"   Fixed LTP 'cp': ₹{fixed_data['cp']:.2f}")
                
                # Show difference
                if original_data and 'cp' in original_data:
                    diff = abs(fixed_data['cp'] - original_data['cp'])
                    if diff > 0.01:
                        print(f"   ✅ Fix applied: Difference of ₹{diff:.2f}")
                    else:
                        print(f"   ✅ Same result: No change needed")

def main():
    """Main execution function"""
    print("🚀 Previous Close Bug Test and Fix")
    print("=" * 60)
    
    # Test symbols from the bug report
    test_symbols = ['ASHAPURMIN', 'GODREJPROP', 'IIFL', 'BALUFORGE', 'BHEL', 'DEVYANI']
    
    try:
        # Step 1: Test current behavior
        tester = PreviousCloseTester()
        results = tester.test_ltp_vs_historical(test_symbols)
        
        # Step 2: Analyze bug scenario
        bug_detected = tester.analyze_bug_scenario()
        
        # Step 3: Apply fix if needed
        if bug_detected or any(r['status'] == 'DISCREPANCY' for r in results.values()):
            print(f"\n⚠️  Bug detected or discrepancies found - applying fix")
            
            fixer = PreviousCloseFixer(tester.upstox_fetcher)
            fixer.apply_fix()
            fixer.test_fix(test_symbols[:3])  # Test with first 3 symbols
            
            # Save fix status
            fix_status = {
                'bug_detected': bug_detected,
                'discrepancies_found': any(r['status'] == 'DISCREPANCY' for r in results.values()),
                'fix_applied': True,
                'timestamp': datetime.now().isoformat()
            }
            
            with open('previous_close_fix_status.json', 'w') as f:
                json.dump(fix_status, f, indent=2)
            
            print(f"\n📋 Fix Status Saved to previous_close_fix_status.json")
            
        else:
            print(f"\n✅ No bugs or discrepancies found - no fix needed")
            
            # Save status
            fix_status = {
                'bug_detected': bug_detected,
                'discrepancies_found': False,
                'fix_applied': False,
                'timestamp': datetime.now().isoformat()
            }
            
            with open('previous_close_fix_status.json', 'w') as f:
                json.dump(fix_status, f, indent=2)
        
        # Step 4: Final summary
        print(f"\n🏁 Test and Fix Summary")
        print("=" * 30)
        
        discrepancies = [s for s, r in results.items() if r['status'] == 'DISCREPANCY']
        matches = [s for s, r in results.items() if r['status'] == 'MATCH']
        
        print(f"✅ Matches: {len(matches)}")
        print(f"⚠️  Discrepancies: {len(discrepancies)}")
        if discrepancies:
            print(f"   Affected symbols: {', '.join(discrepancies)}")
        
        if bug_detected:
            print(f"⚠️  Bug scenario confirmed")
        else:
            print(f"✅ Bug scenario not detected")
        
        print(f"\n📝 Results saved to previous_close_fix_status.json")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"❌ Execution failed: {e}")

if __name__ == "__main__":
    main()