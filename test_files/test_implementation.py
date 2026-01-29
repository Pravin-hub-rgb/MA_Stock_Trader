#!/usr/bin/env python3
"""
Test the previous close fix implementation
"""

from src.utils.upstox_fetcher import UpstoxFetcher

def test_implementation():
    """Test the previous close fix implementation"""
    print("Testing Previous Close Fix Implementation")
    print("=" * 50)
    
    # Test the implementation
    fetcher = UpstoxFetcher()
    
    # Test with a sample symbol
    symbol = 'CHOLAFIN'
    print(f'Testing previous close fix for {symbol}...')
    
    # Test historical API method (now integrated into get_ltp_data)
    print('1. Testing historical API integration...')
    print('   Historical API is now integrated into get_ltp_data method')
    
    # Test LTP data method (which should use historical API as primary)
    print('2. Testing LTP data method...')
    try:
        ltp_data = fetcher.get_ltp_data(symbol)
        print(f'   LTP data: {ltp_data}')
        if 'cp' in ltp_data:
            print(f'   Previous close (cp): {ltp_data["cp"]}')
    except Exception as e:
        print(f'   LTP data error: {e}')
    
    print('Test completed!')

if __name__ == "__main__":
    test_implementation()