#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify opening price capture functionality
Tests the exact first tick method used in the reversal bot
"""

import sys
import os
import time
from datetime import datetime
import pytz

# Add src to path
sys.path.append('src')

# Import components
from src.trading.live_trading.stock_monitor import StockMonitor
from src.trading.live_trading.reversal_monitor import ReversalMonitor
from src.trading.live_trading.selection_engine import SelectionEngine
from src.trading.live_trading.paper_trader import PaperTrader
from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
from src.utils.upstox_fetcher import UpstoxFetcher
from config import MARKET_OPEN, ENTRY_DECISION_TIME

def test_opening_price_capture():
    """Test the opening price capture functionality"""
    
    print("=== TESTING OPENING PRICE CAPTURE ===")
    print(f"Time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    
    # Create test components
    upstox_fetcher = UpstoxFetcher()
    monitor = StockMonitor()
    reversal_monitor = ReversalMonitor()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()
    
    # Test stocks for reversal mode
    test_stocks = {
        'ARISINFRA': 108.66,
        'AVANTEL': 134.38,
        'BALUFORGE': 401.55,
        'CUPID': 376.60,
        'DEVYANI': 125.14
    }
    
    print(f"TESTING with {len(test_stocks)} stocks:")
    for symbol, prev_close in test_stocks.items():
        print(f"   {symbol}: Rs{prev_close:.2f}")
    
    # Prepare instruments
    instrument_keys = []
    stock_symbols = {}
    
    for symbol, prev_close in test_stocks.items():
        try:
            key = upstox_fetcher.get_instrument_key(symbol)
            if key:
                instrument_keys.append(key)
                stock_symbols[key] = symbol
                # Add as reversal stock
                monitor.add_stock(symbol, key, prev_close, 'reversal_s2')
                print(f"   OK {symbol}: Added to monitor")
            else:
                print(f"   ERROR {symbol}: No instrument key")
        except Exception as e:
            print(f"   ERROR {symbol}: {e}")
    
    print(f"\nPREPARED {len(instrument_keys)} instruments")
    
    # Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
    
    # Global variables for tick handler
    global_selected_stocks = []
    global_selected_symbols = set()
    
    # Test tick handler
    def test_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
        print(f"\n--- TICK RECEIVED ---")
        print(f"Symbol: {symbol}")
        print(f"Price: Rs{price:.2f}")
        print(f"Time: {timestamp.strftime('%H:%M:%S')}")
        
        # Process tick
        monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)
        
        # Capture opening prices from first tick (EXPERT'S SOLUTION - works for any start time)
        stock = monitor.stocks.get(instrument_key)
        if stock and stock.open_price is None:
            # Use first tick as opening price (no time dependency)
            stock.set_open_price(price)
            print(f"CAPTURED opening price for {symbol}: Rs{price:.2f}")
            
            # Validate gap immediately
            if stock.validate_gap():
                print(f"VALIDATION: Gap validated for {symbol}")
            else:
                print(f"VALIDATION: Gap rejected for {symbol} - {stock.rejection_reason}")
        else:
            print(f"OPENING: {symbol} already has opening price: Rs{stock.open_price:.2f}" if stock else "OPENING: Stock not found")
        
        # Check violations
        if stock and stock.gap_validated and not stock.low_violation_checked:
            if stock.check_low_violation():
                print(f"VIOLATION: Low violation check passed for {symbol}")
            else:
                print(f"VIOLATION: Low violation check failed for {symbol} - {stock.rejection_reason}")
        
        # Show current status
        print(f"STATUS: {symbol} - Open: Rs{stock.open_price:.2f}, Gap: {((stock.open_price - stock.previous_close) / stock.previous_close * 100):+.1f}%, Active: {stock.is_active}")
        
        print("--- TICK END ---\n")
    
    data_streamer.tick_handler = test_tick_handler
    
    print("\n=== STARTING TEST ===")
    
    try:
        # Connect to data stream
        print("ATTEMPTING to connect to data stream...")
        if data_streamer.connect():
            print("CONNECTED Data stream connected")
            
            # Simulate market open
            print("MARKET OPEN! Testing opening price capture...")
            
            # Wait a bit for connection
            time.sleep(2)
            
            # Test with simulated ticks
            print("\n=== SIMULATING TICKS ===")
            
            # Simulate different opening scenarios
            test_scenarios = [
                ('ARISINFRA', 108.66, 'Flat open'),
                ('AVANTEL', 130.00, 'Gap down open'),
                ('BALUFORGE', 410.00, 'Gap up open'),
                ('CUPID', 370.00, 'Gap down open'),
                ('DEVYANI', 125.14, 'Flat open')
            ]
            
            for symbol, price, description in test_scenarios:
                instrument_key = next((k for k, v in stock_symbols.items() if v == symbol), None)
                if instrument_key:
                    timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))
                    print(f"\n>>> SIMULATING: {symbol} - {description} - Price: Rs{price:.2f}")
                    
                    # Call the tick handler
                    test_tick_handler(instrument_key, symbol, price, timestamp)
                    
                    # Wait between ticks
                    time.sleep(1)
            
            # Show final status
            print("\n=== FINAL STATUS ===")
            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Qualified stocks: {len(qualified_stocks)}")
            for stock in qualified_stocks:
                gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100
                print(f"   {stock.symbol}: Open Rs{stock.open_price:.2f}, Gap {gap_pct:+.1f}%, Status: {'QUALIFIED' if stock.is_active else 'REJECTED'}")
            
            # Show rejected stocks
            rejected_stocks = [s for s in monitor.stocks.values() if not s.is_active]
            if rejected_stocks:
                print(f"Rejected stocks: {len(rejected_stocks)}")
                for stock in rejected_stocks:
                    print(f"   {stock.symbol}: {stock.rejection_reason}")
            
            print("\n=== TEST COMPLETED ===")
            
        else:
            print("FAILED to connect data stream")
            return False
            
    except Exception as e:
        print(f"TEST ERROR: {e}")
        return False
    
    finally:
        # Cleanup
        data_streamer.disconnect()
        print("Test cleanup completed")

if __name__ == "__main__":
    test_opening_price_capture()
