#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test to identify reconnection triggers in continuation bot
Simulates exact continuation bot phases to see if unsubscription causes reconnection
"""

import sys
import os
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, 'src')

def test_reconnection_phases():
    """Test reconnection behavior across continuation bot phases"""
    
    print("=== COMPREHENSIVE RECONNECTION PHASE TEST ===")
    print("Simulating exact continuation bot workflow")
    print()
    
    try:
        # Import the exact same modules used in run_continuation.py
        from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
        from src.utils.upstox_fetcher import UpstoxFetcher
        
        # Test with 3 stocks to simulate continuation bot phases
        test_stocks = [
            {"symbol": "ADANIPOWER", "instrument_key": "NSE_EQ|INE049A01022"},
            {"symbol": "RELIANCE", "instrument_key": "NSE_EQ|INE002A01018"},
            {"symbol": "TATASTEEL", "instrument_key": "NSE_EQ|INE034A01027"}
        ]
        
        print("=== PHASE 1: INITIAL SETUP ===")
        
        # Get instrument keys using UpstoxFetcher
        upstox_fetcher = UpstoxFetcher()
        valid_stocks = []
        
        for stock in test_stocks:
            try:
                instrument_key = upstox_fetcher.get_instrument_key(stock["symbol"])
                if instrument_key:
                    valid_stocks.append({
                        "symbol": stock["symbol"],
                        "instrument_key": instrument_key
                    })
                    print(f"✅ {stock['symbol']}: {instrument_key}")
                else:
                    print(f"❌ Could not get instrument key for {stock['symbol']}")
            except Exception as e:
                print(f"❌ Error getting instrument key for {stock['symbol']}: {e}")
        
        if len(valid_stocks) < 2:
            print("❌ Need at least 2 valid stocks for this test")
            return False
        
        # Create SimpleStockStreamer
        instrument_keys = [stock["instrument_key"] for stock in valid_stocks]
        stock_symbols = {stock["instrument_key"]: stock["symbol"] for stock in valid_stocks}
        
        print(f"\nCreating SimpleStockStreamer with {len(valid_stocks)} stocks")
        data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
        
        # Track all events for debugging
        events_log = []
        
        def log_event(event_type, details=""):
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            event_info = f"[{timestamp}] {event_type}: {details}"
            events_log.append(event_info)
            print(event_info)
        
        # Override WebSocket callbacks for detailed logging
        original_on_open = data_streamer.on_open
        original_on_close = data_streamer.on_close
        original_on_error = data_streamer.on_error
        
        def debug_on_open():
            log_event("WEBSOCKET_OPEN", "Connection established")
            original_on_open()
        
        def debug_on_close(*args):
            close_code = args[0] if args else "None"
            close_reason = args[1] if len(args) > 1 else "None"
            log_event("WEBSOCKET_CLOSE", f"Code: {close_code}, Reason: {close_reason}")
            original_on_close(*args)
        
        def debug_on_error(error):
            log_event("WEBSOCKET_ERROR", str(error))
            original_on_error(error)
        
        data_streamer.on_open = debug_on_open
        data_streamer.on_close = debug_on_close
        data_streamer.on_error = debug_on_error
        
        # Connect to data stream
        print("\n=== PHASE 2: CONNECT AND SUBSCRIBE ===")
        print("Connecting to data stream...")
        if not data_streamer.connect():
            print("❌ FAILED to connect to data stream")
            return False
        
        print("✅ Connected! Waiting for subscription...")
        time.sleep(3)
        
        # Phase 1: Monitor all 3 stocks
        print("\n=== PHASE 3: MONITOR ALL STOCKS (10 seconds) ===")
        ticks_received = {stock["symbol"]: [] for stock in valid_stocks}
        
        def phase1_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            ticks_received[symbol].append(tick_info)
            print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        data_streamer.tick_handler = phase1_tick_handler
        
        # Monitor for 10 seconds
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < 10:
            time.sleep(0.1)
        
        # Count ticks per stock
        print(f"\n=== PHASE 3 RESULTS ===")
        for stock in valid_stocks:
            symbol = stock["symbol"]
            count = len(ticks_received[symbol])
            print(f"{symbol}: {count} ticks")
        
        total_ticks = sum(len(ticks) for ticks in ticks_received.values())
        if total_ticks == 0:
            print("❌ NO TICKS RECEIVED - Cannot continue test!")
            return False
        
        print("✅ SUCCESS: All stocks receiving ticks!")
        
        # Phase 2: Unsubscribe 1 stock (simulating gap/VAH rejection)
        print("\n=== PHASE 4: UNSUBSCRIBE 1 STOCK (Gap/VAH Rejection) ===")
        stock_to_unsub = valid_stocks[0]  # Unsubscribe first stock
        symbol_to_unsub = stock_to_unsub["symbol"]
        instrument_to_unsub = stock_to_unsub["instrument_key"]
        
        log_event("UNSUBSCRIBE", f"Unsubscribing {symbol_to_unsub}")
        
        try:
            data_streamer.unsubscribe([instrument_to_unsub])
            print(f"✅ Unsubscribed {symbol_to_unsub}")
        except Exception as e:
            print(f"❌ Unsubscribe error: {e}")
            return False
        
        # Monitor for 15 seconds to catch any reconnection
        print(f"\n=== PHASE 4: MONITOR AFTER UNSUBSCRIBING {symbol_to_unsub} (15 seconds) ===")
        remaining_stocks = valid_stocks[1:]  # Remove unsubscribed stock
        ticks_after_phase2 = {stock["symbol"]: [] for stock in remaining_stocks}
        
        def phase2_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
            tick_info = {
                'instrument_key': instrument_key,
                'symbol': symbol,
                'price': price,
                'timestamp': timestamp,
                'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
            }
            if symbol in ticks_after_phase2:
                ticks_after_phase2[symbol].append(tick_info)
                print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
            else:
                print(f"[TICK FROM UNEXPECTED STOCK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
        
        data_streamer.tick_handler = phase2_tick_handler
        
        # Monitor for 15 seconds to catch reconnection
        start_time = datetime.now()
        reconnection_detected = False
        while (datetime.now() - start_time).total_seconds() < 15:
            time.sleep(0.1)
            # Check if any new WebSocket events occurred
            recent_events = [event for event in events_log if "WEBSOCKET" in event and "15:" in event[-15:]]
            if any("OPEN" in event for event in recent_events):
                reconnection_detected = True
        
        # Check results
        print(f"\n=== PHASE 4 RESULTS ===")
        for stock in remaining_stocks:
            symbol = stock["symbol"]
            count = len(ticks_after_phase2[symbol])
            print(f"{symbol}: {count} ticks")
        
        # Check for unexpected ticks from unsubscribed stock
        unexpected_ticks = []
        for event in events_log:
            if "TICK FROM UNEXPECTED STOCK" in event:
                unexpected_ticks.append(event)
        
        if unexpected_ticks:
            print(f"❌ PROBLEM: {len(unexpected_ticks)} ticks from unsubscribed stock!")
            for tick in unexpected_ticks[:3]:  # Show first 3
                print(f"   {tick}")
        
        if reconnection_detected:
            print("❌ PROBLEM: Reconnection detected after unsubscription!")
        
        # Phase 3: Unsubscribe another stock (simulating low/volume rejection)
        print(f"\n=== PHASE 5: UNSUBSCRIBE ANOTHER STOCK (Low/Volume Rejection) ===")
        if len(remaining_stocks) > 1:
            stock_to_unsub2 = remaining_stocks[0]
            symbol_to_unsub2 = stock_to_unsub2["symbol"]
            instrument_to_unsub2 = stock_to_unsub2["instrument_key"]
            
            log_event("UNSUBSCRIBE", f"Unsubscribing {symbol_to_unsub2}")
            
            try:
                data_streamer.unsubscribe([instrument_to_unsub2])
                print(f"✅ Unsubscribed {symbol_to_unsub2}")
            except Exception as e:
                print(f"❌ Unsubscribe error: {e}")
                return False
            
            # Monitor for 15 seconds
            print(f"\n=== PHASE 5: MONITOR AFTER UNSUBSCRIBING {symbol_to_unsub2} (15 seconds) ===")
            final_stocks = remaining_stocks[1:]
            ticks_after_phase3 = {stock["symbol"]: [] for stock in final_stocks}
            
            def phase3_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
                tick_info = {
                    'instrument_key': instrument_key,
                    'symbol': symbol,
                    'price': price,
                    'timestamp': timestamp,
                    'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
                }
                if symbol in ticks_after_phase3:
                    ticks_after_phase3[symbol].append(tick_info)
                    print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
                else:
                    print(f"[TICK FROM UNEXPECTED STOCK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
            
            data_streamer.tick_handler = phase3_tick_handler
            
            # Monitor for 15 seconds
            start_time = datetime.now()
            reconnection_detected2 = False
            while (datetime.now() - start_time).total_seconds() < 15:
                time.sleep(0.1)
                recent_events = [event for event in events_log if "WEBSOCKET" in event and "15:" in event[-15:]]
                if any("OPEN" in event for event in recent_events):
                    reconnection_detected2 = True
            
            print(f"\n=== PHASE 5 RESULTS ===")
            for stock in final_stocks:
                symbol = stock["symbol"]
                count = len(ticks_after_phase3[symbol])
                print(f"{symbol}: {count} ticks")
            
            if reconnection_detected2:
                print("❌ PROBLEM: Reconnection detected after second unsubscription!")
        
        # Phase 4: Unsubscribe final stock (simulating entry completion)
        print(f"\n=== PHASE 6: UNSUBSCRIBE FINAL STOCK (Entry Completion) ===")
        if final_stocks:
            final_stock = final_stocks[0]
            final_symbol = final_stock["symbol"]
            final_instrument = final_stock["instrument_key"]
            
            log_event("UNSUBSCRIBE", f"Unsubscribing {final_symbol} (final stock)")
            
            try:
                data_streamer.unsubscribe([final_instrument])
                print(f"✅ Unsubscribed {final_symbol} (all stocks now unsubscribed)")
            except Exception as e:
                print(f"❌ Unsubscribe error: {e}")
                return False
            
            # Monitor for 15 seconds - should see NO ticks
            print(f"\n=== PHASE 6: MONITOR AFTER UNSUBSCRIBING ALL STOCKS (15 seconds) ===")
            final_ticks = []
            
            def final_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
                tick_info = {
                    'instrument_key': instrument_key,
                    'symbol': symbol,
                    'price': price,
                    'timestamp': timestamp,
                    'time_str': timestamp.strftime('%H:%M:%S.%f')[:-3]
                }
                final_ticks.append(tick_info)
                print(f"[TICK] {tick_info['time_str']} - {symbol}: Rs{price:.2f}")
            
            data_streamer.tick_handler = final_tick_handler
            
            # Monitor for 15 seconds
            start_time = datetime.now()
            final_reconnection = False
            while (datetime.now() - start_time).total_seconds() < 15:
                time.sleep(0.1)
                recent_events = [event for event in events_log if "WEBSOCKET" in event and "15:" in event[-15:]]
                if any("OPEN" in event for event in recent_events):
                    final_reconnection = True
            
            print(f"\n=== PHASE 6 RESULTS ===")
            print(f"Ticks received after unsubscribing all stocks: {len(final_ticks)}")
            
            if len(final_ticks) > 0:
                print("❌ PROBLEM: Still receiving ticks after unsubscribing ALL stocks!")
            elif final_reconnection:
                print("❌ PROBLEM: Reconnection detected with NO active stocks!")
            else:
                print("✅ SUCCESS: No ticks and no reconnection after unsubscribing all stocks")
        
        # Final summary
        print(f"\n=== COMPREHENSIVE TEST SUMMARY ===")
        print("WebSocket Events:")
        for event in events_log:
            if "WEBSOCKET" in event:
                print(f"  {event}")
        
        print(f"\nReconnection Analysis:")
        if reconnection_detected:
            print("❌ PROBLEM: Reconnection triggered after Phase 2 unsubscription")
        if 'reconnection_detected2' in locals() and reconnection_detected2:
            print("❌ PROBLEM: Reconnection triggered after Phase 3 unsubscription")
        if 'final_reconnection' in locals() and final_reconnection:
            print("❌ PROBLEM: Reconnection triggered after Phase 4 unsubscription (no active stocks)")
        
        if not reconnection_detected and not ('reconnection_detected2' in locals() and reconnection_detected2) and not ('final_reconnection' in locals() and final_reconnection):
            print("✅ SUCCESS: No unwanted reconnections detected")
        
        # Cleanup
        try:
            data_streamer.disconnect()
            print("✅ WebSocket disconnected")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("COMPREHENSIVE RECONNECTION PHASE TEST")
    print("Testing if unsubscription triggers unwanted reconnections")
    print("=" * 70)
    
    success = test_reconnection_phases()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 COMPREHENSIVE TEST COMPLETED!")
        print("Check the results above to see if reconnection issues were detected.")
    else:
        print("❌ COMPREHENSIVE TEST FAILED!")
        print("Check the error messages above for more details.")
    print("=" * 70)