#!/usr/bin/env python3
"""
Test script to verify real-time tick data vs cached data
"""

import sys
import os
import time
import json
from datetime import datetime
import pytz

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer

IST = pytz.timezone('Asia/Kolkata')

def test_real_time_ticks():
    """Test to see what kind of tick data we're receiving"""
    
    # Test with just one reversal stock
    test_stocks = [
        'NSE_EQ|INE0H9P01028'  # ARISINFRA
    ]
    
    stock_symbols = {
        'NSE_EQ|INE0H9P01028': 'ARISINFRA'
    }
    
    print("=" * 70)
    print("REAL-TIME TICK DATA TEST")
    print("=" * 70)
    print(f"Current time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Market status: {'OPEN' if 9 <= datetime.now(IST).hour < 15 else 'CLOSED'}")
    print()
    
    # Track received ticks
    tick_data = {}
    
    def tick_handler(instrument_key, symbol, ltp, current_time, ohlc_list):
        """Handle incoming ticks"""
        if symbol not in tick_data:
            tick_data[symbol] = []
        
        tick_info = {
            'timestamp': current_time,
            'ltp': ltp,
            'ohlc_count': len(ohlc_list) if ohlc_list else 0
        }
        
        tick_data[symbol].append(tick_info)
        
        print(f"TICK {symbol}: Rs{ltp:.2f} at {current_time.strftime('%H:%M:%S.%f')[:-3]} "
              f"(OHLC: {len(ohlc_list) if ohlc_list else 0})")
        
        # Show first 5 ticks, then every 10th tick
        if len(tick_data[symbol]) <= 5 or len(tick_data[symbol]) % 10 == 0:
            print(f"  Total ticks for {symbol}: {len(tick_data[symbol])}")
    
    # Create streamer
    streamer = SimpleStockStreamer(test_stocks, stock_symbols)
    streamer.tick_handler = tick_handler
    
    print("Connecting to data stream...")
    try:
        streamer.connect()
        
        print("Monitoring ticks for 60 seconds...")
        print("-" * 70)
        
        # Monitor for 60 seconds
        start_time = time.time()
        while time.time() - start_time < 60:
            time.sleep(1)
            
            # Show summary every 10 seconds
            if int(time.time() - start_time) % 10 == 0:
                print(f"\n[SUMMARY at {datetime.now(IST).strftime('%H:%M:%S')}]")
                for symbol, ticks in tick_data.items():
                    if ticks:
                        first_tick = ticks[0]['ltp']
                        last_tick = ticks[-1]['ltp']
                        change = last_tick - first_tick
                        change_pct = (change / first_tick) * 100
                        print(f"  {symbol}: {len(ticks)} ticks | "
                              f"First: Rs{first_tick:.2f} | Last: Rs{last_tick:.2f} | "
                              f"Change: {change:+.2f} ({change_pct:+.2f}%)")
                print("-" * 70)
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        
        # Final summary
        print(f"Final time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"Market status: {'OPEN' if 9 <= datetime.now(IST).hour < 15 else 'CLOSED'}")
        print()
        
        for symbol, ticks in tick_data.items():
            if ticks:
                first_tick = ticks[0]['ltp']
                last_tick = ticks[-1]['ltp']
                change = last_tick - first_tick
                change_pct = (change / first_tick) * 100
                print(f"{symbol}:")
                print(f"  Total ticks: {len(ticks)}")
                print(f"  First tick: Rs{first_tick:.2f}")
                print(f"  Last tick: Rs{last_tick:.2f}")
                print(f"  Change: {change:+.2f} ({change_pct:+.2f}%)")
                print(f"  Time range: {ticks[0]['timestamp'].strftime('%H:%M:%S')} to "
                      f"{ticks[-1]['timestamp'].strftime('%H:%M:%S')}")
                print()
            else:
                print(f"{symbol}: No ticks received")
                print()
        
        # Analysis
        print("ANALYSIS:")
        print("-" * 70)
        
        if not tick_data:
            print("❌ No ticks received - connection issue")
        else:
            market_status = "OPEN" if 9 <= datetime.now(IST).hour < 15 else "CLOSED"
            print(f"📊 Market status during test: {market_status}")
            
            if market_status == "CLOSED":
                if any(len(ticks) > 0 for ticks in tick_data.values()):
                    print("⚠️  Ticks received during market closed - likely cached/stale data")
                else:
                    print("✅ No ticks during market closed - correct behavior")
            else:
                print("✅ Ticks received during market open - correct behavior")
            
            # Check for price movement
            total_movement = 0
            for symbol, ticks in tick_data.items():
                if len(ticks) > 1:
                    first = ticks[0]['ltp']
                    last = ticks[-1]['ltp']
                    movement = abs(last - first)
                    total_movement += movement
            
            if total_movement > 0:
                print("✅ Price movement detected - likely real-time data")
            else:
                print("⚠️  No price movement - possibly cached data")
        
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        try:
            streamer.disconnect()
        except:
            pass

if __name__ == "__main__":
    test_real_time_ticks()
