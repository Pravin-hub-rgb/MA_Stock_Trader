#!/usr/bin/env python3
"""
Test Live Ticks from Upstox WebSocket
Simple test to verify live price data is streaming
"""

import sys
import os
import json
from datetime import datetime
import pytz

# Add src to path
sys.path.append('src')

from utils.upstox_fetcher import UpstoxFetcher

# Import simple streamer directly to avoid package conflicts
sys.path.append('src/trading/live_trading')
import simple_data_streamer
SimpleStockStreamer = simple_data_streamer.SimpleStockStreamer

IST = pytz.timezone('Asia/Kolkata')

def load_test_stocks():
    """Load test stocks"""
    try:
        with open('src/trading/continuation_list.txt', 'r') as f:
            content = f.read().strip()
            if not content:
                return []

            symbols = [s.strip() for s in content.split(',') if s.strip()]
            return symbols[:2]  # Test with first 2 stocks

    except Exception as e:
        print(f"❌ Error loading stocks: {e}")
        return []

def get_instrument_keys(fetcher, symbols):
    """Get instrument keys for symbols"""
    instrument_keys = []
    stock_symbols = {}

    for symbol in symbols:
        try:
            key = fetcher.get_instrument_key(symbol)
            if key:
                instrument_keys.append(key)
                stock_symbols[key] = symbol
                print(f"✅ {symbol} → {key}")
            else:
                print(f"❌ {symbol} → No key found")
        except Exception as e:
            print(f"❌ {symbol} → Error: {e}")

    return instrument_keys, stock_symbols

def test_live_ticks():
    """Test live tick streaming"""
    print("🧪 LIVE TICKS TEST")
    print("=" * 50)
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load stocks
    symbols = load_test_stocks()
    if not symbols:
        print("❌ No stocks to test")
        return 1

    print(f"📋 Testing with stocks: {symbols}")
    print()

    # Get Upstox fetcher
    fetcher = UpstoxFetcher()

    # Get instrument keys
    instrument_keys, stock_symbols = get_instrument_keys(fetcher, symbols)
    if not instrument_keys:
        print("❌ No instrument keys found")
        return 1

    print()
    print("🔌 Starting WebSocket connection...")
    print("You should see live price updates below:")
    print("-" * 50)

    # Create streamer
    streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    try:
        # Run for 30 seconds to see live ticks
        import time
        start_time = time.time()

        def tick_handler(instrument_key, symbol, price, timestamp):
            # Print tick (already done in on_message)
            pass

        streamer.tick_handler = tick_handler
        streamer.run()

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")

    print("-" * 50)
    print("✅ Live ticks test completed")
    return 0

if __name__ == "__main__":
    sys.exit(test_live_ticks())