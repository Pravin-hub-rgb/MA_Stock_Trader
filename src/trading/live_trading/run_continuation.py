#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Trading Bot - Pure OHLC-based Trading
Dedicated bot for SVRO continuation trading using 1-minute OHLC data
"""

import sys
import os
import time as time_module
from datetime import datetime, time
import pytz
import psutil
import portalocker

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed VAH calculation info
# Use print statements instead of logging for UI compatibility
# logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

def kill_duplicate_processes():
    """Kill any other instances of continuation bot"""
    try:
        current_pid = os.getpid()
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.name() == 'python' and
                    proc.pid != current_pid and
                    proc.cmdline() and
                    'run_continuation.py' in ' '.join(proc.cmdline())):

                    proc.kill()
                    killed_count += 1
                    print(f"KILLED duplicate continuation bot process {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"CLEANED up {killed_count} duplicate continuation processes")
            time_module.sleep(2)

    except Exception as e:
        print(f"WARNING: Could not check for duplicates: {e}")

def acquire_singleton_lock():
    """Ensure only one instance of continuation bot runs"""
    lock_file = 'continuation_bot.lock'

    try:
        lock_handle = open(lock_file, 'w')
        portalocker.lock(lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        globals()['lock_handle'] = lock_handle
        print("[LOCK] Continuation bot singleton lock acquired")

    except portalocker.LockException:
        print("ERROR: Another continuation bot instance is already running - exiting")
        sys.exit(1)
    except Exception as e:
        print(f"WARNING: Could not acquire singleton lock: {e}")

def cleanup_singleton_lock():
    """Clean up the continuation bot singleton lock"""
    try:
        if 'lock_handle' in globals():
            globals()['lock_handle'].close()
            os.remove('continuation_bot.lock')
            print("[UNLOCK] Continuation bot singleton lock released")
    except Exception as e:
        print(f"WARNING: Could not cleanup lock: {e}")

def run_continuation_bot():
    """Run the continuation trading bot using pure OHLC processing"""

    print("STARTING CONTINUATION TRADING BOT (OHLC-ONLY)")
    print("=" * 50)

    # Import components directly
    sys.path.insert(0, 'src/trading/live_trading')

    from continuation_stock_monitor import StockMonitor
    from rule_engine import RuleEngine
    from selection_engine import SelectionEngine
    from paper_trader import PaperTrader
    from simple_data_streamer import SimpleStockStreamer

    from volume_profile import volume_profile_calculator
    from src.utils.upstox_fetcher import UpstoxFetcher, iep_manager
    from src.trading.live_trading.continuation_modules.continuation_timing_module import ContinuationTimingManager
    from config import MARKET_OPEN, ENTRY_TIME, PREP_START

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = StockMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load continuation stock configuration
    from stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_continuation_stock_configuration()

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"LOADED {len(symbols)} continuation stocks:")
    for symbol in symbols:
        situation = situations[symbol]
        desc = {
            'continuation': 'SVRO Continuation',
        }.get(situation, situation)
        print(f"   {symbol}: {desc}")

    # Get previous closes using LTP API
    prev_closes = {}
    for symbol in symbols:
        try:
            data = upstox_fetcher.get_ltp_data(symbol)
            if data and 'cp' in data and data['cp'] is not None:
                prev_closes[symbol] = float(data['cp'])
                print(f"   OK {symbol}: Rs{prev_closes[symbol]:.2f}")
            else:
                print(f"   ERROR {symbol}: No previous close data")
        except Exception as e:
            print(f"   ERROR {symbol}: {e}")

    # Prepare instruments
    instrument_keys = []
    stock_symbols = {}
    for symbol, prev_close in prev_closes.items():
        try:
            key = upstox_fetcher.get_instrument_key(symbol)
            if key:
                instrument_keys.append(key)
                stock_symbols[key] = symbol
                situation = situations.get(symbol, 'continuation')
                monitor.add_stock(symbol, key, prev_close, situation)
        except Exception as e:
            print(f"   ERROR {symbol}: No instrument key")

    print(f"\nPREPARED {len(instrument_keys)} continuation instruments")

    # Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    # Continuation tick handler - OHLC only, no tick processing
    def tick_handler_continuation(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """Continuation tick handler - OHLC only, no tick processing"""
        global global_selected_stocks, global_selected_symbols

        # Process OHLC data only (no tick-based opening price capture)
        monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)

        # Update price tracking for low violation monitoring
        stock = monitor.stocks.get(instrument_key)
        if stock:
            stock.update_price(price, timestamp)

        # Check violations for opened stocks (continuous monitoring)
        monitor.check_violations()

        # Check volume validations for continuation stocks
        monitor.check_volume_validations()

        # Check entry signals only after entry decision time (9:19)
        current_time = datetime.now(IST).time()
        if current_time >= ENTRY_TIME and 'global_selected_stocks' in globals() and global_selected_stocks:
            entry_signals = monitor.check_entry_signals()

            for stock in entry_signals:
                if stock.symbol in global_selected_symbols:
                    print(f"ENTRY {stock.symbol} entry triggered at Rs{price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
                    stock.enter_position(price, timestamp)
                    paper_trader.log_entry(stock, price, timestamp)

        # Check exit signals for entered positions
        if current_time >= ENTRY_TIME:
            # Check for trailing stop adjustments (5% profit -> move SL to entry)
            for stock in monitor.stocks.values():
                if stock.entered and stock.entry_price and stock.current_price:
                    profit_pct = (stock.current_price - stock.entry_price) / stock.entry_price
                    if profit_pct >= 0.05:  # 5% profit
                        new_sl = stock.entry_price  # Move SL to breakeven
                        if stock.entry_sl < new_sl:
                            old_sl = stock.entry_sl
                            stock.entry_sl = new_sl
                            print(f"TRAILING {stock.symbol} trailing stop adjusted: Rs{old_sl:.2f} -> Rs{new_sl:.2f} (5% profit)")

            # Check exit signals (including updated trailing stops)
            exit_signals = monitor.check_exit_signals()
            for stock in exit_signals:
                pnl = (price - stock.entry_price) / stock.entry_price * 100
                print(f"EXIT {stock.symbol} exited at Rs{price:.2f}, PNL: {pnl:+.2f}%")
                stock.exit_position(price, timestamp, "Stop Loss Hit")
                paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")

    # Initialize global variables for tick handler
    global_selected_stocks = []
    global_selected_symbols = set()
    
    # Set the continuation tick handler
    data_streamer.tick_handler = tick_handler_continuation

    print("\n=== CONTINUATION BOT INITIALIZED ===")
    print("Using pure OHLC processing - no tick-based opening prices")
    print()

    try:
        # PREP TIME: Load metadata and prepare data
        print("=== PREP TIME: Loading metadata and preparing data ===")

        # Load stock scoring metadata (ADR, volume baselines, etc.)
        from stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)
        print("OK Stock metadata loaded for scoring")
        
        # Get mean volume baselines from cache during PREP time
        print("LOADING mean volume baselines from cache...")
        for stock in monitor.stocks.values():
            try:
                metadata = stock_scorer.stock_metadata.get(stock.symbol, {})
                volume_baseline = metadata.get('volume_baseline', 1000000)
                stock.volume_baseline = volume_baseline
                print(f"Mean volume baseline for {stock.symbol}: {volume_baseline:,}")
            except Exception as e:
                print(f"ERROR loading mean volume baseline for {stock.symbol}: {e}")

        # Calculate VAH from previous day's volume profile
        print("Calculating VAH from previous day's volume profile...")
        continuation_symbols = [symbol for symbol, situation in situations.items() if situation == 'continuation']
        print(f"Continuation symbols: {continuation_symbols}")
        if continuation_symbols:
            try:
                result = volume_profile_calculator.calculate_vah_for_stocks(continuation_symbols)
                global_vah_dict = result

                print(f"VAH calculated for {len(global_vah_dict)} continuation stocks")

                # Save VAH results to file for frontend display
                if global_vah_dict:
                    import json
                    vah_results = {
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'continuation',
                        'results': global_vah_dict,
                        'summary': f"{len(global_vah_dict)} stocks calculated"
                    }

                    with open('vah_results.json', 'w') as f:
                        json.dump(vah_results, f, indent=2)

                    print(f"VAH results saved to vah_results.json")

                    # Print VAH results explicitly for UI visibility
                    if global_vah_dict:
                        print("VAH CALCULATION RESULTS:")
                        for symbol, vah in global_vah_dict.items():
                            print(f"[OK] {symbol}: Upper Range (VAH) = Rs{vah:.2f}")
                        print(f"Summary: {len(global_vah_dict)} stocks successfully calculated")

            except Exception as e:
                print(f"VAH calculation error: {e}")
                global_vah_dict = {}
        else:
            global_vah_dict = {}
            print("No continuation stocks to calculate VAH for")

        # PRE-MARKET IEP FETCH SEQUENCE
        print("=== PRE-MARKET IEP FETCH SEQUENCE ===")
        
        # Wait for PREP_START time (30 seconds before market open)
        prep_start = PREP_START
        current_time = datetime.now(IST).time()
        
        if current_time < prep_start:
            prep_datetime = datetime.combine(datetime.now(IST).date(), prep_start)
            prep_datetime = IST.localize(prep_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (prep_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds until PREP_START ({prep_start})...")
                time_module.sleep(wait_seconds)
        
        # Fetch IEP for all continuation stocks
        print(f"FETCHING IEP for {len(symbols)} continuation stocks...")
        iep_prices = iep_manager.fetch_iep_batch(symbols)
        
        if iep_prices:
            print("IEP FETCH COMPLETED SUCCESSFULLY")
            
            # Set opening prices and run gap validation
            for symbol, iep_price in iep_prices.items():
                # Find stock by symbol
                stock = None
                for s in monitor.stocks.values():
                    if s.symbol == symbol:
                        stock = s
                        break
                
                if stock:
                    stock.set_open_price(iep_price)
                    print(f"Set opening price for {symbol}: Rs{iep_price:.2f}")
                    
                    # Run gap validation immediately (at 9:14:30)
                    if hasattr(stock, 'validate_gap'):
                        stock.validate_gap()
                        if stock.gap_validated:
                            print(f"Gap validated for {symbol}")
                        else:
                            print(f"Gap validation failed for {symbol}")
                else:
                    print(f"Stock not found for symbol: {symbol}")
        else:
            print("IEP FETCH FAILED - FALLING BACK TO OHLC")
        
        print("=== STARTING CONTINUATION TRADING PHASE ===")

        # Connect to data stream
        print("ATTEMPTING to connect to data stream...")
        if data_streamer.connect():
            print("CONNECTED Data stream connected")

            # Wait for market open
            market_open = MARKET_OPEN
            current_time = datetime.now(IST).time()

            if current_time < market_open:
                market_datetime = datetime.combine(datetime.now(IST).date(), market_open)
                market_datetime = IST.localize(market_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (market_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"WAITING {wait_seconds:.0f} seconds for market open...")
                    time_module.sleep(wait_seconds)

            print("MARKET OPEN! Monitoring live OHLC data...")

            # Capture initial volume at market open for cumulative tracking
            print("CAPTURING initial volume at market open for cumulative tracking...")
            for stock in monitor.stocks.values():
                try:
                    initial_volume = upstox_fetcher.get_current_volume(stock.symbol)
                    if initial_volume > 0:
                        stock.initial_volume = initial_volume
                        print(f"Initial volume captured for {stock.symbol}: {initial_volume:,}")
                    else:
                        print(f"WARNING: No initial volume for {stock.symbol}")
                except Exception as e:
                    print(f"ERROR capturing initial volume for {stock.symbol}: {e}")

            # For continuation: IEP-based opening prices (already set at 9:14:30)
            print("USING IEP-BASED OPENING PRICES - Set at 9:14:30 from pre-market IEP")
            print("Gap validation completed at 9:14:30, ready for trading")

            # Continue with normal entry decision timing
            entry_decision_time = ENTRY_TIME
            current_time = datetime.now(IST).time()

            if current_time < entry_decision_time:
                decision_datetime = datetime.combine(datetime.now(IST).date(), entry_decision_time)
                decision_datetime = IST.localize(decision_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (decision_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"\nWAITING {wait_seconds:.0f} seconds until entry decision...")
                    time_module.sleep(wait_seconds)

            # Prepare entries and select stocks
            print("\n=== PREPARING ENTRIES ===")

            # Show current status after OHLC-based qualification
            print("POST-OHLC QUALIFICATION STATUS:")
            for stock in monitor.stocks.values():
                open_status = f"Open: Rs{stock.open_price:.2f}" if stock.open_price else "No opening price"

                gap_pct = 0.0
                if stock.open_price and stock.previous_close:
                    gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100

                gap_status = "Gap validated" if stock.gap_validated else f"Gap: {gap_pct:+.2f}%"
                low_status = "Low checked" if stock.low_violation_checked else "Low not checked"
                # Format volume status with detailed information
                if stock.volume_validated and stock.early_volume and stock.volume_baseline:
                    # Calculate volume ratio for display
                    volume_ratio = (stock.early_volume / stock.volume_baseline * 100) if stock.volume_baseline > 0 else 0
                    # Format volume numbers with K suffix
                    cumulative_vol_str = f"{stock.early_volume/1000:.1f}K" if stock.early_volume >= 1000 else f"{stock.early_volume:,}"
                    baseline_vol_str = f"{stock.volume_baseline/1000:.1f}K" if stock.volume_baseline >= 1000 else f"{stock.volume_baseline:,}"
                    volume_status = f"Volume validated {volume_ratio:.1f}% ({cumulative_vol_str}) >= 7.5% of ({baseline_vol_str})"
                else:
                    volume_status = "Volume not checked"

                situation_desc = {
                    'continuation': 'Cont',
                }.get(stock.situation, stock.situation)

                rejection_info = ""
                if stock.rejection_reason:
                    rejection_info = f" | REJECTED: {stock.rejection_reason}"

                print(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status} | {volume_status}{rejection_info}")

            # Apply VAH validation for continuation stocks
            print("=== APPLYING VAH VALIDATION ===")
            if global_vah_dict:
                for stock in monitor.stocks.values():
                    if stock.situation == 'continuation' and stock.symbol in global_vah_dict:
                        vah_price = global_vah_dict[stock.symbol]
                        if hasattr(stock, 'validate_vah_rejection'):
                            stock.validate_vah_rejection(vah_price)
            
            monitor.prepare_entries()

            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Qualified stocks: {len(qualified_stocks)}")

            selected_stocks = selection_engine.select_stocks(qualified_stocks)
            print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

            # Mark selected stocks as ready
            for stock in selected_stocks:
                stock.entry_ready = True
                print(f"READY to trade: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")

            # Initialize selected_stocks for the tick handler
            global_selected_symbols = {stock.symbol for stock in selected_stocks}

            # Keep monitoring for entries, exits, and trailing stops
            print("\nMONITORING for entry/exit signals...")
            data_streamer.run()

        else:
            print("FAILED to connect data stream")
            print("CONTINUING without data stream for testing...")

    except KeyboardInterrupt:
        print("\nSTOPPED by user")

    # Cleanup
    print("\n=== CLEANUP ===")
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== CONTINUATION BOT SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        # Prevent multiple instances
        kill_duplicate_processes()
        acquire_singleton_lock()

        # Run the continuation bot
        run_continuation_bot()

    except KeyboardInterrupt:
        print("\nContinuation bot interrupted by user")
    except SystemExit:
        print("\nContinuation bot exited (another instance running)")
    except Exception as e:
        print(f"\nContinuation bot error: {e}")
    finally:
        # Always cleanup
        cleanup_singleton_lock()
        print("Continuation bot shutdown complete")
