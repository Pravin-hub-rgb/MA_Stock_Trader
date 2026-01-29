#!/usr/bin/env python3
"""
Test script specifically for LTPC opening price capture
"""

import sys
import os
sys.path.append('src')

from trading.live_trading.data_streamer import StockDataStreamer
from datetime import datetime
import pytz

def test_ltpc_opening_price_capture():
    """Test LTPC opening price capture logic"""
    print("🧪 Testing LTPC Opening Price Capture Logic\n")

    # Create data streamer instance
    streamer = StockDataStreamer(['NSE_EQ|INE002A01018'], {'NSE_EQ|INE002A01018': 'BSE'})

    # Test the opening price capture logic with mock LTPC data
    print("📊 Simulating LTPC ticks after market open...")

    # Mock LTPC data (what would come from WebSocket)
    mock_ltpc_data = [
        {'ltp': 385.50, 'ltt': int(datetime.now().timestamp() * 1000)},  # First tick = opening price
        {'ltp': 385.75, 'ltt': int(datetime.now().timestamp() * 1000)},  # Subsequent ticks
        {'ltp': 386.00, 'ltt': int(datetime.now().timestamp() * 1000)},  # More ticks
    ]

    # Simulate market open time
    from src.trading.live_trading.config import MARKET_OPEN
    print(f"🎯 Market open time set to: {MARKET_OPEN}")

    # Test opening price capture
    for i, ltpc in enumerate(mock_ltpc_data):
        print(f"\n📡 Processing LTPC tick #{i+1}: LTP = ₹{ltpc['ltp']}")

        # Simulate the logic from data_streamer.py
        ltp = ltpc['ltp']

        if not streamer.market_opened:
            current_time = datetime.now(pytz.timezone('Asia/Kolkata')).time()
            print(f"   Current time: {current_time}, Market open: {MARKET_OPEN}")

            if current_time >= MARKET_OPEN:
                streamer.market_opened = True
                if 'BSE' not in streamer.opening_prices:
                    streamer.opening_prices['BSE'] = float(ltp)
                    print(f"   ✅ OPENING PRICE CAPTURED: ₹{ltp} for BSE")
                    break  # First tick should capture opening price
            else:
                print("   ⏳ Waiting for market open...")
        else:
            print("   ℹ️ Market already opened, opening price already captured")

    # Check final state
    print("\n📈 Final State:")
    print(f"   Market opened: {streamer.market_opened}")
    print(f"   Opening prices captured: {len(streamer.opening_prices)}")
    if 'BSE' in streamer.opening_prices:
        print(f"   BSE opening price: ₹{streamer.opening_prices['BSE']}")

    # Test gap analysis readiness
    reversal_symbols = ['BSE']  # Mock
    gap_analysis_ready = all(symbol in streamer.opening_prices for symbol in reversal_symbols)
    print(f"   Gap analysis ready: {gap_analysis_ready}")

    print("\n✅ LTPC Opening Price Capture Test Completed!")

if __name__ == "__main__":
    test_ltpc_opening_price_capture()
