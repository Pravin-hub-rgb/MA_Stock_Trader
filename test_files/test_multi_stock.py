#!/usr/bin/env python3
"""
Quick Multi-Stock Threading Test
Test monitoring 6 stocks simultaneously for threading functionality
"""

import sys
import os
import json
from datetime import datetime
import pytz

# Add src to path
sys.path.append('src')

from utils.upstox_fetcher import UpstoxFetcher

# Import simple streamer directly
sys.path.append('src/trading/live_trading')
import simple_data_streamer

SimpleStockStreamer = simple_data_streamer.SimpleStockStreamer

IST = pytz.timezone('Asia/Kolkata')

def load_test_stocks():
    """Load stocks from continuation_list.txt"""
    try:
        with open('src/trading/continuation_list.txt', 'r') as f:
            content = f.read().strip()
            if not content:
                return []

            symbols = [s.strip() for s in content.split(',') if s.strip()]
            return symbols

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

def test_multi_stock_threading():
    """Test multi-stock threading with live data"""
    print("🧪 MULTI-STOCK THREADING TEST")
    print("=" * 50)
    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load stocks
    symbols = load_test_stocks()
    print(f"📋 Testing threading with {len(symbols)} stocks: {symbols}")
    print()

    # Get Upstox fetcher
    fetcher = UpstoxFetcher()

    # Get instrument keys
    instrument_keys, stock_symbols = get_instrument_keys(fetcher, symbols)
    if not instrument_keys:
        print("❌ No instrument keys found")
        return 1

    print()
    print("🔌 Starting WebSocket connection for multi-stock monitoring...")
    print("You should see interleaved price updates from all stocks:")
    print("-" * 60)

    # Create streamer
    streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    # Track tick counts per stock
    tick_counts = {symbol: 0 for symbol in symbols}

    def tick_handler(instrument_key, symbol, price, timestamp):
        tick_counts[symbol] += 1
        # Only print every 10th tick to avoid spam
        if tick_counts[symbol] % 10 == 0:
            print(f"📊 {symbol}: {tick_counts[symbol]} ticks, Last: ₹{price:.2f}")

    streamer.tick_handler = tick_handler

    try:
        print("Monitoring for 60 seconds...")
        import time
        start_time = time.time()

        streamer.run()

        # Summary
        print("-" * 60)
        print("📊 THREADING TEST SUMMARY:")
        total_ticks = sum(tick_counts.values())
        print(f"Total ticks received: {total_ticks}")
        print(f"Stocks monitored: {len(symbols)}")
        print(f"Average ticks per stock: {total_ticks/len(symbols):.1f}")

        for symbol, count in tick_counts.items():
            print(f"  {symbol}: {count} ticks")

        if total_ticks > len(symbols) * 5:  # At least 5 ticks per stock
            print("✅ Threading working perfectly!")
            return 0
        else:
            print("⚠️ Limited ticks - check connection")
            return 1

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
        return 0

if __name__ == "__main__":
    sys.exit(test_multi_stock_threading())