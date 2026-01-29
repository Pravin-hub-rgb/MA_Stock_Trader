#!/usr/bin/env python3
"""
Test script to verify ADR retrieval for reversal list stocks
"""

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

from utils.cache_manager import cache_manager
from utils.upstox_fetcher import upstox_fetcher

def test_reversal_list_adr():
    """Test ADR retrieval for reversal list stocks"""
    print('=== ADR Cache Test for Reversal List Stocks ===')
    
    # Read reversal list
    reversal_list_path = 'src/trading/reversal_list.txt'
    reversal_stocks = []
    
    try:
        with open(reversal_list_path, 'r') as f:
            content = f.read().strip()
            # Parse symbols (remove postfix like -u11, -d14)
            symbols_with_postfix = content.split(',')
            reversal_stocks = [symbol.split('-')[0] for symbol in symbols_with_postfix]
    except Exception as e:
        print(f"Error reading reversal list: {e}")
        return
    
    print(f"Found {len(reversal_stocks)} reversal stocks: {', '.join(reversal_stocks)}")
    print()
    
    # Test ADR retrieval for each stock
    for symbol in reversal_stocks:
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

def test_reversal_live_trading_stock_scorer():
    """Test live trading stock scorer ADR loading for reversal stocks"""
    print('\n=== Testing Live Trading Stock Scorer for Reversal Stocks ===')
    
    # Read reversal list
    reversal_list_path = 'src/trading/reversal_list.txt'
    reversal_stocks = []
    
    try:
        with open(reversal_list_path, 'r') as f:
            content = f.read().strip()
            # Parse symbols (remove postfix like -u11, -d14)
            symbols_with_postfix = content.split(',')
            reversal_stocks = [symbol.split('-')[0] for symbol in symbols_with_postfix]
    except Exception as e:
        print(f"Error reading reversal list: {e}")
        return
    
    try:
        from trading.live_trading.stock_scorer import stock_scorer
        
        # Create dummy prev_closes for testing
        prev_closes = {symbol: 100.0 for symbol in reversal_stocks}
        
        print(f'Preloading metadata for {len(reversal_stocks)} reversal stocks...')
        stock_scorer.preload_metadata(reversal_stocks, prev_closes)
        
        print('\nADR values loaded from cache:')
        for symbol in reversal_stocks:
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
    test_reversal_list_adr()
    test_reversal_live_trading_stock_scorer()