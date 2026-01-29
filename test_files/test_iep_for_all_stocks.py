#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to fetch IEP prices for all stocks in continuation_list.txt
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

def test_iep_for_all_stocks():
    """Test IEP fetching for all continuation stocks"""
    print("=== TESTING IEP FETCH FOR ALL CONTINUATION STOCKS ===")
    
    try:
        from src.utils.upstox_fetcher import upstox_fetcher, iep_manager
        
        # Read continuation list directly
        continuation_list_file = 'src/trading/continuation_list.txt'
        if os.path.exists(continuation_list_file):
            with open(continuation_list_file, 'r') as f:
                symbols = [symbol.strip() for symbol in f.read().split(',')]
        else:
            # Fallback to known symbols
            symbols = ['BLISSGVS', 'CUPID', 'GRAPHITE', 'JAINREC', 'JWL', 'KROSS']
        
        situations = {symbol: 'continuation' for symbol in symbols}
        
        print(f"Found {len(symbols)} continuation stocks:")
        for symbol in symbols:
            situation = situations[symbol]
            print(f"  {symbol}: {situation}")
        
        print(f"\nFetching IEP for all {len(symbols)} stocks...")
        
        # Fetch IEP for all stocks
        iep_prices = iep_manager.fetch_iep_batch(symbols)
        
        print(f"\nIEP FETCH RESULTS:")
        print(f"Successfully fetched: {len(iep_prices)} stocks")
        
        for symbol in symbols:
            if symbol in iep_prices:
                price = iep_prices[symbol]
                print(f"  ✓ {symbol}: Rs{price:.2f}")
            else:
                print(f"  ✗ {symbol}: No IEP data")
        
        # Test individual stock fetching as fallback
        print(f"\nTesting individual stock fetching for failed stocks...")
        failed_stocks = [symbol for symbol in symbols if symbol not in iep_prices]
        
        for symbol in failed_stocks:
            try:
                price = iep_manager.get_iep_for_symbol(symbol)
                if price:
                    print(f"  ✓ {symbol} (individual): Rs{price:.2f}")
                else:
                    print(f"  ✗ {symbol} (individual): No data")
            except Exception as e:
                print(f"  ✗ {symbol} (individual): Error - {e}")
        
        print(f"\n=== TEST COMPLETED ===")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_iep_for_all_stocks()
    if success:
        print("Test completed successfully!")
    else:
        print("Test failed!")
    sys.exit(0 if success else 1)