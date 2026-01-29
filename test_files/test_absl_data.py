#!/usr/bin/env python3
"""
Test script to check ABSLAMC data fetching
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.data_fetcher import data_fetcher
from datetime import datetime, timedelta

def main():
    symbol = 'ABSLAMC'

    # Test 1: Current date range
    print("=== TEST 1: Current date range ===")
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
    print(f'Fetching data for {symbol} from {start_date} to {end_date}')
    data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)

    if not data.empty:
        print('Latest data:')
        latest = data.iloc[-1]
        print(f'Date: {latest["date"]}')
        print(f'Close: ₹{latest["close"]:.2f}')
        print('\nAll dates in data:')
        for idx, row in data.iterrows():
            print(f'  {row["date"]}: ₹{row["close"]:.2f}')
    else:
        print('No data found')

    print("\n=== TEST 2: Real-time data ===")
    # Test 2: Try real-time data fetch
    realtime_data = data_fetcher.fetch_realtime_data(symbol)
    if realtime_data:
        print(f'Real-time data: {realtime_data}')
    else:
        print('No real-time data available')

    print("\n=== TEST 3: yfinance direct test ===")
    # Test 3: Direct yfinance call
    try:
        import yfinance as yf
        ticker = f"{symbol}.NS"
        print(f'Direct yfinance call for {ticker}')

        # Try to get just today's data
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            print(f'Direct yfinance result: {hist.iloc[-1]}')
        else:
            print('No direct yfinance data')

        # Try info
        info = stock.info
        if info:
            print(f'Info available: {info.get("regularMarketPrice", "N/A")}')
        else:
            print('No info available')

    except Exception as e:
        print(f'Direct yfinance error: {e}')

if __name__ == "__main__":
    main()
