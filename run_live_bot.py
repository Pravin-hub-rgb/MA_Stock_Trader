#!/usr/bin/env python3
"""
Standalone Live Trading Bot Runner
Avoids package import issues
"""

import sys
import os
import time as time_module
from datetime import datetime, time
import pytz
import psutil
import portalocker

# Add src to path
sys.path.append('src')

# Global variables for tick handler
global_selected_stocks = []
global_selected_symbols = set()

def kill_duplicate_processes():
    """Kill any other instances of this bot to prevent WebSocket conflicts"""
    try:
        current_pid = os.getpid()
        killed_count = 0

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if (proc.name() == 'python' and
                    proc.pid != current_pid and
                    proc.cmdline() and
                    'run_live_bot.py' in ' '.join(proc.cmdline())):

                    proc.kill()
                    killed_count += 1
                    print(f"🛑 Killed duplicate bot process {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed_count > 0:
            print(f"✅ Cleaned up {killed_count} duplicate processes")
            time_module.sleep(2)  # Give time for cleanup

    except Exception as e:
        print(f"⚠️ Warning: Could not check for duplicates: {e}")

def acquire_singleton_lock():
    """Ensure only one instance of the bot runs using file lock"""
    lock_file = 'bot.lock'

    try:
        # Try to acquire exclusive lock
        lock_handle = open(lock_file, 'w')
        portalocker.lock(lock_handle, portalocker.LOCK_EX | portalocker.LOCK_NB)

        # Store the handle to keep lock active
        globals()['lock_handle'] = lock_handle
        print("🔒 Singleton lock acquired")

    except portalocker.LockException:
        print("❌ Another instance is already running - exiting")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ Warning: Could not acquire singleton lock: {e}")

def cleanup_singleton_lock():
    """Clean up the singleton lock file"""
    try:
        if 'lock_handle' in globals():
            globals()['lock_handle'].close()
            os.remove('bot.lock')
            print("🔓 Singleton lock released")
    except Exception as e:
        print(f"⚠️ Warning: Could not cleanup lock: {e}")

def run_live_trading_bot():
    """Run the complete live trading bot"""

    print("🚀 STARTING LIVE TRADING BOT")
    print("=" * 50)

    # Import components directly
    sys.path.append('src/trading/live_trading')

    from stock_monitor import StockMonitor
    from reversal_monitor import ReversalMonitor
    from rule_engine import RuleEngine
    from selection_engine import SelectionEngine
    from paper_trader import PaperTrader
    from simple_data_streamer import SimpleStockStreamer
    from utils.upstox_fetcher import UpstoxFetcher
    from config import MARKET_OPEN, ENTRY_DECISION_TIME, TEST_MODE, SIMULATE_OPENING_PRICES

    # Create components
    upstox_fetcher = UpstoxFetcher()
    monitor = StockMonitor()
    reversal_monitor = ReversalMonitor()
    rule_engine = RuleEngine()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()

    # Parse command-line arguments
    from bot_args import parse_bot_arguments
    bot_config = parse_bot_arguments()

    # Load stock configuration based on mode
    from stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_stock_configuration(bot_config['mode'])

    symbols = stock_config['symbols']
    situations = stock_config['situations']

    print(f"📋 Loaded {len(symbols)} stocks for {bot_config['trading_mode']}:")
    for symbol in symbols:
        situation = situations[symbol]
        desc = {
            'continuation': 'Continuation',
            'reversal_s1': 'Reversal Uptrend',
            'reversal_s2': 'Reversal Downtrend'
        }.get(situation, situation)
        print(f"   {symbol}: {desc}")

    # Get previous closes
    prev_closes = {}
    for symbol in symbols:
        try:
            data = upstox_fetcher.get_latest_data(symbol)
            if data and 'close' in data:
                prev_closes[symbol] = data['close']
                print(f"   ✅ {symbol}: ₹{data['close']:.2f}")
        except Exception as e:
            print(f"   ❌ {symbol}: {e}")

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
            print(f"   ❌ {symbol}: No instrument key")

    print(f"\n✅ Prepared {len(instrument_keys)} instruments")

    # Initialize data streamer
    data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

    # Tick handler
    def tick_handler(instrument_key, symbol, price, timestamp, ohlc_list=None):
        global global_selected_stocks, global_selected_symbols
        monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)

        # Process reversal data (OHLC for climax detection)
        if ohlc_list and bot_config['mode'] == 'r':
            stock = monitor.stocks.get(instrument_key)
            if stock and stock.situation == 'reversal_s2':
                reversal_monitor.process_three_min_bar(symbol, ohlc_list)
                # Check for climax detection
                if reversal_monitor.detect_climax_bar(symbol) and not stock.climax_detected:
                    stock.climax_detected = True
                    print(f"🎯 {symbol}: Climax bar detected - monitoring for retracement entries")

        # Check violations during confirmation window
        current_time = datetime.now(IST).time()
        if MARKET_OPEN <= current_time <= ENTRY_DECISION_TIME:
            monitor.check_violations()

        # Prepare entries for newly qualified stocks
        qualified_stocks = monitor.get_qualified_stocks()
        for stock in qualified_stocks:
            if not stock.entry_ready:
                # This stock just got qualified, prepare entry levels
                monitor.prepare_entries()  # This will set entry levels for all qualified stocks
                # Re-get qualified stocks to include the newly prepared ones
                qualified_stocks = monitor.get_qualified_stocks()
                global_selected_stocks = selection_engine.select_stocks(qualified_stocks)
                global_selected_symbols = {stock.symbol for stock in global_selected_stocks}

                for sel_stock in global_selected_stocks:
                    if not sel_stock.entry_ready:
                        sel_stock.entry_ready = True
                        gap_pct = ((sel_stock.open_price-sel_stock.previous_close)/sel_stock.previous_close*100)
                        print(f"✅ {sel_stock.symbol} qualified - Gap: {gap_pct:+.1f}% | Entry: ₹{sel_stock.entry_high:.2f} | SL: ₹{sel_stock.entry_sl:.2f}")
                break  # Only do this once per tick to avoid spam

        # Check entry signals only after entry decision time (only for selected stocks)
        if current_time >= ENTRY_DECISION_TIME and global_selected_stocks:
            entry_signals = monitor.check_entry_signals()

            for stock in entry_signals:
                if stock.symbol in global_selected_symbols:  # Only allow selected stocks to enter
                    print(f"📈 {stock.symbol} entry triggered at ₹{price:.2f}, SL placed at ₹{stock.entry_sl:.2f}")
                    stock.enter_position(price, timestamp)
                    paper_trader.log_entry(stock, price, timestamp)

            # Check reversal entry signals
            if bot_config['mode'] == 'r':
                for stock in monitor.stocks.values():
                    if stock.symbol in global_selected_symbols and stock.situation == 'reversal_s2':
                        # Check sub-case 2A (within first 5 min)
                        if reversal_monitor.should_enter_subcase_2a(stock, current_time):
                            print(f"🎯 {stock.symbol} sub-case 2A entry triggered at ₹{price:.2f} (open=low)")
                            stock.entry_high = price  # Set entry level for SL calculation
                            stock.entry_sl = price * 0.96  # 4% SL
                            stock.enter_position(price, timestamp)
                            paper_trader.log_entry(stock, price, timestamp)
                            break  # One entry per tick

                        # Check sub-case 2B (dynamic retracement, no time limit)
                        should_enter_2b, trigger_price = reversal_monitor.should_enter_subcase_2b(stock, current_time)
                        if should_enter_2b and stock.entry_attempts < stock.max_entry_attempts:
                            stock.entry_attempts += 1
                            print(f"🎯 {stock.symbol} sub-case 2B entry #{stock.entry_attempts} triggered at ₹{price:.2f} (trigger: ₹{trigger_price:.2f})")
                            stock.entry_high = price  # Set entry level for SL calculation
                            stock.entry_sl = price * 0.96  # 4% SL
                            stock.enter_position(price, timestamp)
                            paper_trader.log_entry(stock, price, timestamp)

                            # Update retracement trigger for next attempt
                            reversal_monitor.update_retracement_trigger(stock)
                            break  # One entry per tick

        # Check trailing stops and exit signals for entered positions
        if current_time >= ENTRY_DECISION_TIME:
            # Check for trailing stop adjustments (5% profit -> move SL to entry)
            for stock in monitor.stocks.values():
                if stock.entered and stock.entry_price and stock.current_price:
                    profit_pct = (stock.current_price - stock.entry_price) / stock.entry_price
                    if profit_pct >= 0.05:  # 5% profit
                        new_sl = stock.entry_price  # Move SL to breakeven
                        if stock.entry_sl < new_sl:
                            old_sl = stock.entry_sl
                            stock.entry_sl = new_sl
                            print(f"🔒 {stock.symbol} trailing stop adjusted: ₹{old_sl:.2f} → ₹{new_sl:.2f} (5% profit)")

            # Check exit signals (including updated trailing stops)
            exit_signals = monitor.check_exit_signals()
            for stock in exit_signals:
                pnl = (price - stock.entry_price) / stock.entry_price * 100
                print(f"📉 {stock.symbol} exited at ₹{price:.2f}, PNL: {pnl:+.2f}%")
                stock.exit_position(price, timestamp, "Stop Loss Hit")
                paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")

        # Position status logging removed to reduce tick spam

    data_streamer.tick_handler = tick_handler

    print("\n=== BOT INITIALIZED ===")
    print("Waiting for market timing...")
    print()

    try:
        # PREP TIME: Load metadata and prepare data (ALWAYS needed for scoring)
        print("=== PREP TIME: Loading metadata and preparing data ===")

        # Load stock scoring metadata (ADR, volume baselines, etc.)
        from stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)
        print("✅ Stock metadata loaded for scoring")

        if TEST_MODE:
            print("🧪 TEST MODE: Running qualification test sequence")
            # Run test sequence instead of waiting for market timing
            monitor.run_test_sequence()
            print("🧪 TEST MODE: Test sequence complete")
        else:
            # Wait for prep end (9:14:30)
            prep_end = time(9, 14, 30)
            current_time = datetime.now(IST).time()

            if current_time < prep_end:
                # Create timezone-aware datetime for prep_end
                prep_datetime = datetime.combine(datetime.now(IST).date(), prep_end)
                prep_datetime = IST.localize(prep_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (prep_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"⏳ Waiting {wait_seconds:.0f} seconds until prep end...")
                    time_module.sleep(wait_seconds)

        print("=== STARTING TRADING PHASE ===")

        # Connect to data stream
        if data_streamer.connect():
            print("✅ Data stream connected")

            # Wait for market open
            market_open = MARKET_OPEN
            current_time = datetime.now(IST).time()

            if current_time < market_open:
                # Create timezone-aware datetime for market_open
                market_datetime = datetime.combine(datetime.now(IST).date(), market_open)
                market_datetime = IST.localize(market_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (market_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"⏳ Waiting {wait_seconds:.0f} seconds for market open...")
                    time_module.sleep(wait_seconds)

            print("📈 MARKET OPEN! Monitoring live data...")

            # At ENTRY_DECISION_TIME, prepare entries
            entry_decision_time = ENTRY_DECISION_TIME
            current_time = datetime.now(IST).time()

            if current_time < entry_decision_time:
                # Create timezone-aware datetime for entry decision
                decision_datetime = datetime.combine(datetime.now(IST).date(), entry_decision_time)
                decision_datetime = IST.localize(decision_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (decision_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    print(f"⏳ Waiting {wait_seconds:.0f} seconds until entry decision...")
                    time_module.sleep(wait_seconds)

            # Prepare entries and select stocks
            print("\n=== PREPARING ENTRIES ===")

            # Show current status before qualification
            print("📊 PRE-QUALIFICATION STATUS:")
            for stock in monitor.stocks.values():
                open_status = f"📈 Open: ₹{stock.open_price:.2f}" if stock.open_price else "❌ No opening price"
                gap_status = "✅ Gap validated" if stock.gap_validated else "❓ Gap not validated"
                low_status = "✅ Low checked" if stock.low_violation_checked else "❓ Low not checked"
                situation_desc = {
                    'continuation': 'Cont',
                    'reversal_s1': 'Rev-U',
                    'reversal_s2': 'Rev-D'
                }.get(stock.situation, stock.situation)
                print(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status}")

            monitor.prepare_entries()

            qualified_stocks = monitor.get_qualified_stocks()
            print(f"Qualified stocks: {len(qualified_stocks)}")

            selected_stocks = selection_engine.select_stocks(qualified_stocks)
            print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

            # Mark selected stocks as ready
            for stock in selected_stocks:
                stock.entry_ready = True
                print(f"🎯 Ready to trade: {stock.symbol} (Entry: ₹{stock.entry_high:.2f}, SL: ₹{stock.entry_sl:.2f})")

            # Initialize selected_stocks for the tick handler (fix scope issue)
            selected_symbols = {stock.symbol for stock in selected_stocks}

            # Keep monitoring for entries, exits, and trailing stops
            print("\n📊 Monitoring for entry/exit signals...")
            # Start the streaming loop to monitor for signals
            data_streamer.run()

        else:
            print("❌ Failed to connect data stream")

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")

    # Cleanup
    print("\n=== CLEANUP ===")
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print("=== SESSION ENDED ===")
    print(f"Summary: {summary}")

if __name__ == "__main__":
    try:
        # Prevent multiple instances
        kill_duplicate_processes()
        acquire_singleton_lock()

        # Run the bot
        run_live_trading_bot()

    except KeyboardInterrupt:
        print("\n🛑 Bot interrupted by user")
    except SystemExit:
        print("\n🛑 Bot exited (another instance running)")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
    finally:
        # Always cleanup
        cleanup_singleton_lock()
        print("🏁 Bot shutdown complete")
