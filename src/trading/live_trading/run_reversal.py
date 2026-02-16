#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Trading Bot - API-based Opening Prices
Dedicated bot for OOPS reversal trading using official opening prices from API

MODULAR ARCHITECTURE: Uses reversal_modules for state management, tick processing,
and subscription management to eliminate cross-contamination bugs.
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import psutil
import portalocker

# Add src to path
sys.path.insert(0, 'src')

# Configure logging to show detailed VAH calculation info
# Use print statements instead of logging for UI compatibility
# logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

# Import modular architecture
from reversal_modules.integration import ReversalIntegration
from reversal_modules.subscription_manager import safe_unsubscribe

def kill_duplicate_processes():
    """Kill any other instances of reversal bot"""
    try:
        current_pid = os.getpid()
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.name() == 'python' and
                    proc.pid != current_pid and
                    proc.cmdline() and
                    'run_reversal.py' in ' '.join(proc.cmdline())):

                    proc.kill()
                    killed_count += 1
                    print(f"KILLED duplicate reversal bot process {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"CLEANED up {killed_count} duplicate reversal processes")
            time_module.sleep(2)

    except Exception as e:
        print(f"WARNING: Could not check for duplicates: {e}")

def acquire_singleton_lock():
    """Ensure only one instance of reversal bot runs"""
    lock_file = 'reversal_bot.lock'

    try:
        lock_handle = open(lock_file, 'w')
        portalocker.lock(lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        globals()['lock_handle'] = lock_handle
        print("[LOCK] Reversal bot singleton lock acquired")

    except portalocker.LockException:
        print("ERROR: Another reversal bot instance is already running - exiting")
        sys.exit(1)
    except Exception as e:
        print(f"WARNING: Could not acquire singleton lock: {e}")

def cleanup_singleton_lock():
    """Clean up the reversal bot singleton lock"""
    try:
        if 'lock_handle' in globals():
            globals()['lock_handle'].close()
            os.remove('reversal_bot.lock')
            print("[UNLOCK] Reversal bot singleton lock released")
    except Exception as e:
        print(f"WARNING: Could not cleanup lock: {e}")

def run_reversal_bot():
    """Run the reversal trading bot using API-based opening prices"""

    print("=== TOP LEVEL DEBUGGING START ===")
    print("STARTING REVERSAL TRADING BOT (API-BASED OPENING PRICES)")
    print("=" * 55)

    # Import components directly
    sys.path.insert(0, 'src/trading/live_trading')

    from reversal_stock_monitor import ReversalStockMonitor
    from rule_engine import RuleEngine
    from selection_engine import SelectionEngine
    from paper_trader import PaperTrader
    from simple_data_streamer import SimpleStockStreamer

    from volume_profile import volume_profile_calculator
    from src.utils.upstox_fetcher import UpstoxFetcher, iep_manager
    from config import MARKET_OPEN, ENTRY_TIME, PREP_START, API_POLL_DELAY_SECONDS, API_RETRY_DELAY_SECONDS

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = ReversalStockMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Load reversal stock configuration
    from src.trading.live_trading.stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_reversal_stock_configuration()

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"LOADED {len(symbols)} reversal stocks:")
    for symbol in symbols:
        situation = situations[symbol]
        desc = {
            'reversal_s1': 'Reversal Uptrend',
            'reversal_s2': 'Reversal Downtrend',
            'reversal_vip': 'VIP Reversal',
            'reversal_tertiary': 'Tertiary Reversal'
        }.get(situation, situation)
        print(f"   {symbol}: {desc}")

    # Get previous closes using LTP API
    prev_closes = {}
    for symbol in symbols:
        try:
            data = upstox_fetcher.get_ltp_data(symbol)
            if data and 'cp' in data and data['cp'] is not None:
                prev_closes[symbol] = float(data['cp'])
                print(f"   OK {symbol}: Prev Close Rs{prev_closes[symbol]:.2f}")
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
                situation = situations.get(symbol, 'reversal_s2')
                monitor.add_stock(symbol, key, prev_close, situation)
        except Exception as e:
            print(f"   ERROR {symbol}: No instrument key")

    print(f"\nPREPARED {len(instrument_keys)} reversal instruments")

    # Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    # CREATE INTEGRATION EARLY (needed for unsubscribe phases)
    # Create modular integration BEFORE gap validation
    integration = ReversalIntegration(data_streamer, monitor, paper_trader)

    # Reversal tick handler - simplified with modular architecture
    def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """
        Simplified reversal tick handler using modular architecture
        Delegates all logic to individual stocks based on their state
        """
        # Use modular integration for tick processing
        integration.simplified_tick_handler(instrument_key, symbol, price, timestamp, ohlc_list, monitor)

    # Set the reversal tick handler
    data_streamer.tick_handler = tick_handler_reversal

    # PRE-MARKET IEP FETCH SEQUENCE (Priority 1 Fix)
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
    
    # Fetch IEP for all reversal stocks
    print(f"FETCHING IEP for {len(symbols)} reversal stocks...")
    
    # Clean symbols from reversal_list.txt (remove postfix like -u11, -d14)
    clean_symbols = []
    for symbol in symbols:
        # Remove postfix after dash if present
        if '-' in symbol:
            clean_symbol = symbol.split('-')[0]
            clean_symbols.append(clean_symbol)
        else:
            clean_symbols.append(symbol)
    
    print(f"Clean symbols for IEP: {clean_symbols}")
    
    # Import IEP manager
    from src.utils.upstox_fetcher import iep_manager
    iep_prices = iep_manager.fetch_iep_batch(clean_symbols)
    
    if iep_prices:
        print("IEP FETCH COMPLETED SUCCESSFULLY")
        
        # Set opening prices and run gap validation
        for symbol in symbols:
            # Find the clean symbol for IEP lookup
            clean_symbol = symbol.split('-')[0] if '-' in symbol else symbol
            
            if clean_symbol in iep_prices:
                iep_price = iep_prices[clean_symbol]
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
                print(f"IEP price not found for symbol: {symbol}")
    else:
        print("IEP FETCH FAILED - MANUAL OPENING PRICE CAPTURE REQUIRED")
        print("WARNING: Opening prices will need to be set manually or via alternative method")

    # OPTIMIZATION: ONLY SUBSCRIBE TO GAP-VALIDATED STOCKS
    # Since gap validation completed at 9:14:30, we can filter stocks before subscription
    print("\n" + "=" * 55)
    print("OPTIMIZATION: FILTERING GAP-VALIDATED STOCKS")
    print("=" * 55)
    
    # Get gap-validated stocks
    gap_validated_stocks = []
    for stock in monitor.stocks.values():
        if stock.gap_validated:
            gap_validated_stocks.append(stock)

    # Create filtered instrument keys list
    gap_validated_instrument_keys = [stock.instrument_key for stock in gap_validated_stocks]

    print(f"GAP-VALIDATED STOCKS: {len(gap_validated_stocks)} out of {len(monitor.stocks)}")
    print(f"GAP-VALIDATED SYMBOLS: {[stock.symbol for stock in gap_validated_stocks]}")

    # OPTIMIZATION: Subscribe only to gap-validated stocks
    # This eliminates the need for Phase 1 unsubscription
    if gap_validated_instrument_keys:
        integration.prepare_and_subscribe(gap_validated_instrument_keys)
        print(f"OPTIMIZED SUBSCRIPTION: Only {len(gap_validated_stocks)} gap-validated stocks subscribed")
    else:
        print("NO GAP-VALIDATED STOCKS - No subscriptions needed")
        return

    # REMOVED: integration.phase_1_unsubscribe_after_gap_validation()
    # Reason: Optimization implemented - only gap-validated stocks are subscribed
    print()

    try:
        # PREP TIME: Load metadata and prepare data
        print("=== PREP TIME: Loading metadata and preparing data ===")

        #  REMOVED: Skip stock scoring metadata loading for pure first-come-first-serve
        # Classification (S1 vs S2) is already handled by StockClassifier
        # No ADR, price, or volume scoring needed for first-come-first-serve logic

        #  REMOVED: Skip reversal monitor watchlist loading for pure first-come-first-serve
        # Stock classification (S1 vs S2) is already handled by StockClassifier
        # No VIP/Secondary/Tertiary classification or quality ranking needed

        # Wait for market open (no prep end needed)
        current_time = datetime.now(IST).time()
        market_open = MARKET_OPEN

        if current_time < market_open:
            market_datetime = datetime.combine(datetime.now(IST).date(), market_open)
            market_datetime = IST.localize(market_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (market_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                print(f"WAITING {wait_seconds:.0f} seconds until market open...")
                time_module.sleep(wait_seconds)

        print("=== STARTING REVERSAL TRADING PHASE ===")

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

            print("MARKET OPEN! Monitoring live tick data...")

            # MARKET OPEN: Make OOPS stocks ready immediately
            print("\n=== MARKET OPEN: Making OOPS stocks ready ===")
            active_stocks = monitor.get_active_stocks()
            oops_stocks = [stock for stock in active_stocks if stock.situation == 'reversal_s2' and stock.gap_validated]
            
            if oops_stocks:
                print(f"OOPS CANDIDATES READY FOR IMMEDIATE TRADING ({len(oops_stocks)}):")
                for stock in oops_stocks:
                    stock.entry_ready = True
                    print(f"   {stock.symbol} (OOPS): Previous Close Rs{stock.previous_close:.2f} - Ready for trigger")
            else:
                print("No OOPS candidates ready")
            
            print(f"OOPS stocks ready: {len(oops_stocks)}")

            # Continue with normal entry timing for Strong Start stocks
            entry_time = ENTRY_TIME
            current_time = datetime.now(IST).time()

            if current_time < entry_time:
                entry_datetime = datetime.combine(datetime.now(IST).date(), entry_time)
                entry_datetime = IST.localize(entry_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (entry_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"\nWAITING {wait_seconds:.0f} seconds until entry time...")
                    time_module.sleep(wait_seconds)

            # Prepare entries and select stocks
            print("\n=== PREPARING ENTRIES ===")

            # Show current status after reversal qualification (only actively monitored stocks)
            print("POST-REVERSAL QUALIFICATION STATUS:")
            active_stocks = monitor.get_active_stocks()
            for stock in active_stocks:
                open_status = f"Open: Rs{stock.open_price:.2f}" if stock.open_price else "No opening price"

                gap_pct = 0.0
                if stock.open_price and stock.previous_close:
                    gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100

                gap_status = "Gap validated" if stock.gap_validated else f"Gap: {gap_pct:+.1f}%"
                low_status = "Low checked" if stock.low_violation_checked else "Low not checked"

                situation_desc = {
                    'reversal_s1': 'Rev-U',
                    'reversal_s2': 'Rev-D',
                    'reversal_vip': 'VIP',
                    'reversal_tertiary': 'Tert'
                }.get(stock.situation, stock.situation)

                rejection_info = ""
                if stock.rejection_reason:
                    rejection_info = f" | REJECTED: {stock.rejection_reason}"

                print(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status}{rejection_info}")

            print("About to call monitor.prepare_entries()")
            monitor.prepare_entries()
            print("monitor.prepare_entries() completed")

            # PHASE 2: CHECK LOW VIOLATIONS AND UNSUBSCRIBE
            # This happens at entry time (12:33:00) before preparing entries
            integration.phase_2_unsubscribe_after_low_violation()

            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Qualified stocks: {len(qualified_stocks)}")

            # SKIP SELECTION PHASE - Keep all qualified stocks subscribed for first-come-first-serve
            # All qualified stocks stay subscribed until both positions are filled
            print(f"All {len(qualified_stocks)} qualified stocks remain subscribed for first-come-first-serve")

            # Mark all qualified stocks as ready (no selection)
            print("\n=== ENTRY TIME: Strong Start candidates ready ===")
            strong_start_stocks = [stock for stock in qualified_stocks if stock.situation == 'reversal_s1']
            
            if strong_start_stocks:
                print(f"STRONG START CANDIDATES READY FOR TRADING ({len(strong_start_stocks)}):")
                for stock in strong_start_stocks:
                    stock.entry_ready = True
                    print(f"   {stock.symbol} (Strong Start): High Rs{stock.daily_high:.2f}, SL Rs{stock.entry_sl:.2f} - Ready for trigger")
            else:
                print("No Strong Start candidates ready")
            
            # OOPS stocks were already marked ready at market open
            oops_stocks = [stock for stock in qualified_stocks if stock.situation == 'reversal_s2']
            if oops_stocks:
                print(f"\nOOPS CANDIDATES (already ready since market open): {len(oops_stocks)}")
                for stock in oops_stocks:
                    print(f"   {stock.symbol} (OOPS): Previous Close Rs{stock.previous_close:.2f} - Ready for trigger")
            else:
                print("No OOPS candidates ready")

            # Initialize selected_stocks for the tick handler (all qualified stocks)
            global_selected_symbols = {stock.symbol for stock in qualified_stocks}

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
    
    # Show final high/low values for Strong Start candidates
    print("FINAL HIGH/LOW VALUES FOR STRONG START CANDIDATES:")
    active_stocks = monitor.get_active_stocks()
    ss_stocks = [stock for stock in active_stocks if stock.situation == 'reversal_s1']
    
    if ss_stocks:
        for stock in ss_stocks:
            print(f"   {stock.symbol}: High: Rs{stock.daily_high:.2f}, Low: Rs{stock.daily_low:.2f}")
    else:
        print("   No Strong Start candidates active")
    
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== REVERSAL BOT SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        # Prevent multiple instances
        kill_duplicate_processes()
        acquire_singleton_lock()

        # Run the reversal bot
        run_reversal_bot()

    except KeyboardInterrupt:
        print("\nReversal bot interrupted by user")
    except SystemExit:
        print("\nReversal bot exited (another instance running)")
    except Exception as e:
        print(f"\nReversal bot error: {e}")
    finally:
        # Always cleanup
        cleanup_singleton_lock()
        print("Reversal bot shutdown complete")
