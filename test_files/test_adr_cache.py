#!/usr/bin/env python3
"""
Test script to verify ADR retrieval from cache
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from utils.cache_manager import cache_manager
from utils.upstox_fetcher import upstox_fetcher

def test_adr_cache():
    """Test ADR retrieval from cache"""
    print('=== ADR Cache Test ===')
    
    test_symbols = ['ITC', 'RELIANCE', 'TATASTEEL', 'HDFCBANK']
    
    for symbol in test_symbols:
        try:
            # Load cached data
            cached_data = cache_manager.load_cached_data(symbol)
            if cached_data is not None and not cached_data.empty:
                if 'adr_percent' in cached_data.columns:
                    latest_adr = cached_data['adr_percent'].iloc[-1]
                    print(f'{symbol}: ADR {latest_adr:.2f}% (from cache)')
                else:
                    print(f'{symbol}: No adr_percent column in cache')
                    print(f'Available columns: {list(cached_data.columns)}')
            else:
                print(f'{symbol}: No cached data available')
        except Exception as e:
            print(f'{symbol}: Error - {e}')

def test_live_trading_stock_scorer():
    """Test live trading stock scorer ADR loading"""
    print('\n=== Testing Live Trading Stock Scorer ===')
    
    try:
        from trading.live_trading.stock_scorer import stock_scorer
        
        # Test preload metadata
        test_symbols = ['ITC', 'RELIANCE']
        prev_closes = {'ITC': 500.0, 'RELIANCE': 2500.0}
        
        print('Preloading metadata...')
        stock_scorer.preload_metadata(test_symbols, prev_closes)
        
        for symbol in test_symbols:
            if symbol in stock_scorer.stock_metadata:
                metadata = stock_scorer.stock_metadata[symbol]
                print(f'{symbol}: ADR {metadata["adr_percent"]:.2f}%, Price Rs{metadata["current_price"]:.0f}')
            else:
                print(f'{symbol}: No metadata loaded')
                
    except Exception as e:
        print(f'Error testing stock scorer: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_adr_cache()
    test_live_trading_stock_scorer()