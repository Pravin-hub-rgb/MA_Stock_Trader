#!/usr/bin/env python3
"""
Debug ADR calculation
"""

import sys
import os
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.data_fetcher import data_fetcher

def debug_adr_calculation():
    """Debug ADR calculation for a sample stock"""
    
    # Test with a known volatile stock
    symbol = "RELIANCE.NS"
    end_date = date.today().strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')
    
    print(f"Debugging ADR calculation for {symbol}")
    print(f"Date range: {start_date} to {end_date}")
    
    # Fetch data
    data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
    print(f"Data shape: {data.shape}")
    print(f"Data columns: {list(data.columns)}")
    
    if not data.empty:
        # Calculate indicators
        data_with_indicators = data_fetcher.calculate_technical_indicators(data)
        
        print(f"\nLast 5 rows with indicators:")
        print(data_with_indicators[['close', 'high', 'low', 'daily_range', 'adr', 'adr_percent']].tail())
        
        latest = data_with_indicators.iloc[-1]
        print(f"\nLatest values:")
        print(f"Close: {latest['close']}")
        print(f"High: {latest['high']}")
        print(f"Low: {latest['low']}")
        print(f"Daily Range: {latest['daily_range']}")
        print(f"ADR (20-day avg): {latest['adr']}")
        print(f"ADR %: {latest['adr_percent']}")
        
        # Manual calculation
        manual_adr = latest['daily_range']
        manual_adr_percent = (manual_adr / latest['close']) * 100
        print(f"\nManual calculation:")
        print(f"ADR % = ({manual_adr} / {latest['close']}) * 100 = {manual_adr_percent}")
        
    else:
        print("No data fetched")

if __name__ == "__main__":
    debug_adr_calculation()
