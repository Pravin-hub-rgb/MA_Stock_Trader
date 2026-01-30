#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Bot Test Runner - Monolithic Test Environment
Dedicated test environment for SVRO continuation trading using 1-minute OHLC data
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import logging
from typing import Dict, List, Optional, Callable
import pytz

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import continuation bot components
from src.trading.live_trading.continuation_stock_monitor import StockMonitor
from src.trading.live_trading.rule_engine import RuleEngine
from src.trading.live_trading.selection_engine import SelectionEngine
from src.trading.live_trading.paper_trader import PaperTrader
from src.trading.live_trading.simple_data_streamer import SimpleStockStreamer
from src.trading.live_trading.volume_profile import volume_profile_calculator
from src.utils.upstox_fetcher import UpstoxFetcher, iep_manager
from src.trading.live_trading.continuation_modules.continuation_timing_module import ContinuationTimingManager
from config import MARKET_OPEN, ENTRY_TIME, PREP_START

# Configure logging for testing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuation_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ContinuationTest')


class ContinuationTest:
    """Monolithic test environment for continuation bot"""

    def __init__(self):
        self.logger = logger
        self.monitor = None
        self.rule_engine = RuleEngine()
        self.selection_engine = SelectionEngine()
        self.paper_trader = PaperTrader()
        self.data_streamer = None
        self.is_running = False
        self.test_results = []
        self.test_start_time = None

        self.logger.info("Continuation Test Environment initialized")

    def setup_test_environment(self):
        """Setup the monolithic test environment"""
        self.logger.info("Setting up continuation bot test environment...")

        # Create components
        upstox_fetcher = UpstoxFetcher()
        self.monitor = StockMonitor()
        self.rule_engine = RuleEngine()
        self.selection_engine = SelectionEngine()
        self.paper_trader = PaperTrader()

        IST = pytz.timezone('Asia/Kolkata')

        # Load continuation stock configuration
        from src.trading.live_trading.stock_classifier import StockClassifier
        classifier = StockClassifier()
        stock_config = classifier.get_continuation_stock_configuration()

        symbols = stock_config['symbols']
        situations = stock_config['situations']

        self.logger.info(f"LOADED {len(symbols)} continuation stocks:")
        for symbol in symbols:
            situation = situations[symbol]
            desc = {
                'continuation': 'SVRO Continuation',
            }.get(situation, situation)
            self.logger.info(f"   {symbol}: {desc}")

        # Get previous closes using LTP API
        prev_closes = {}
        for symbol in symbols:
            try:
                data = upstox_fetcher.get_ltp_data(symbol)
                if data and 'cp' in data and data['cp'] is not None:
                    prev_closes[symbol] = float(data['cp'])
                    self.logger.info(f"   OK {symbol}: Rs{prev_closes[symbol]:.2f}")
                else:
                    self.logger.info(f"   ERROR {symbol}: No previous close data")
            except Exception as e:
                self.logger.info(f"   ERROR {symbol}: {e}")

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
                    self.monitor.add_stock(symbol, key, prev_close, situation)
            except Exception as e:
                self.logger.info(f"   ERROR {symbol}: No instrument key")

        self.logger.info(f"\nPREPARED {len(instrument_keys)} continuation instruments")

        # Initialize data streamer
        self.data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)

# Setup tick handler
        def tick_handler_continuation(instrument_key, symbol, price, timestamp, ohlc_list=None):
            """Continuation tick handler - OHLC only, no tick processing"""
            # Process OHLC data only (no tick-based opening price capture)
            self.monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)

            # Update price tracking for low violation monitoring
            stock = self.monitor.stocks.get(instrument_key)
            if stock:
                stock.update_price(price, timestamp)

            # Check violations for opened stocks (continuous monitoring)
            self.monitor.check_violations()

            # Check volume validations for continuation stocks
            self.monitor.check_volume_validations()

            # Check entry signals only after entry decision time (9:19)
            current_time = datetime.now(IST).time()
            if current_time >= ENTRY_TIME and self.test_results:
                entry_signals = self.monitor.check_entry_signals()

                for stock in entry_signals:
                    if stock.symbol in [r['symbol'] for r in self.test_results]:
                        self.logger.info(f"ENTRY {stock.symbol} entry triggered at Rs{price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
                        stock.enter_position(price, timestamp)
                        self.paper_trader.log_entry(stock, price, timestamp)

            # Check exit signals for entered positions
            if current_time >= ENTRY_TIME:
                # Check for trailing stop adjustments (5% profit -> move SL to entry)
                for stock in self.monitor.stocks.values():
                    if stock.entered and stock.entry_price and stock.current_price:
                        profit_pct = (stock.current_price - stock.entry_price) / stock.entry_price
                        if profit_pct >= 0.05:  # 5% profit
                            new_sl = stock.entry_price  # Move SL to breakeven
                            if stock.entry_sl < new_sl:
                                old_sl = stock.entry_sl
                                stock.entry_sl = new_sl
                                self.logger.info(f"TRAILING {stock.symbol} trailing stop adjusted: Rs{old_sl:.2f} -> Rs{new_sl:.2f} (5% profit)")

                # Check exit signals (including updated trailing stops)
                exit_signals = self.monitor.check_exit_signals()
                for stock in exit_signals:
                    pnl = (price - stock.entry_price) / stock.entry_price * 100
                    self.logger.info(f"EXIT {stock.symbol} exited at Rs{price:.2f}, PNL: {pnl:+.2f}%")
                    stock.exit_position(price, timestamp, "Stop Loss Hit")
                    self.paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")

        self.data_streamer.tick_handler = tick_handler_continuation

        self.logger.info("\n=== CONTINUATION BOT TEST ENVIRONMENT INITIALIZED ===")
        self.logger.info("Using pure OHLC processing - no tick-based opening prices")
        self.logger.info("Preparing entries and selecting stocks")

        # PREP TIME: Load metadata and prepare data
        self.logger.info("=== PREP TIME: Loading metadata and preparing data ===")

        # Load stock scoring metadata (ADR, volume baselines, etc.)
        from src.trading.live_trading.stock_scorer import stock_scorer
        stock_scorer.preload_metadata(list(prev_closes.keys()), prev_closes)
        self.logger.info("OK Stock metadata loaded for scoring")

        # Get mean volume baselines from cache during PREP time
        self.logger.info("LOADING mean volume baselines from cache...")
        for stock in self.monitor.stocks.values():
            try:
                metadata = stock_scorer.stock_metadata.get(stock.symbol, {})
                volume_baseline = metadata.get('volume_baseline', 1000000)
                stock.volume_baseline = volume_baseline
                self.logger.info(f"Mean volume baseline for {stock.symbol}: {volume_baseline:,}")
            except Exception as e:
                self.logger.info(f"ERROR loading mean volume baseline for {stock.symbol}: {e}")

        # Calculate VAH from previous day's volume profile
        self.logger.info("Calculating VAH from previous day's volume profile...")
        continuation_symbols = [symbol for symbol, situation in situations.items() if situation == 'continuation']
        self.logger.info(f"Continuation symbols: {continuation_symbols}")
        if continuation_symbols:
            try:
                result = volume_profile_calculator.calculate_vah_for_stocks(continuation_symbols)
                global_vah_dict = result

                self.logger.info(f"VAH calculated for {len(global_vah_dict)} continuation stocks")

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

                    self.logger.info(f"VAH results saved to vah_results.json")

                    # Print VAH results explicitly for UI visibility
                    if global_vah_dict:
                        self.logger.info("VAH CALCULATION RESULTS:")
                        for symbol, vah in global_vah_dict.items():
                            self.logger.info(f"[OK] {symbol}: Upper Range (VAH) = Rs{vah:.2f}")
                        self.logger.info(f"Summary: {len(global_vah_dict)} stocks successfully calculated")

            except Exception as e:
                self.logger.info(f"VAH calculation error: {e}")
                global_vah_dict = {}
        else:
            global_vah_dict = {}
            self.logger.info("No continuation stocks to calculate VAH for")

        # PRE-MARKET IEP FETCH SEQUENCE
        self.logger.info("=== PRE-MARKET IEP FETCH SEQUENCE ===")

        # Wait for PREP_START time (30 seconds before market open)
        prep_start = PREP_START
        current_time = datetime.now(IST).time()

        if current_time < prep_start:
            prep_datetime = datetime.combine(datetime.now(IST).date(), prep_start)
            prep_datetime = IST.localize(prep_datetime)
            current_datetime = datetime.now(IST)
            wait_seconds = (prep_datetime - current_datetime).total_seconds()
            if wait_seconds > 0:
                self.logger.info(f"WAITING {wait_seconds:.0f} seconds until PREP_START ({prep_start})...")
                time_module.sleep(wait_seconds)

        # Fetch IEP for all continuation stocks
        self.logger.info(f"FETCHING IEP for {len(symbols)} continuation stocks...")
        iep_prices = iep_manager.fetch_iep_batch(symbols)

        if iep_prices:
            self.logger.info("IEP FETCH COMPLETED SUCCESSFULLY")

            # Set opening prices and run gap validation
            for symbol, iep_price in iep_prices.items():
                # Find stock by symbol
                stock = None
                for s in self.monitor.stocks.values():
                    if s.symbol == symbol:
                        stock = s
                        break

                if stock:
                    stock.set_open_price(iep_price)
                    self.logger.info(f"Set opening price for {symbol}: Rs{iep_price:.2f}")

                    # Run gap validation immediately (at 9:14:30)
                    if hasattr(stock, 'validate_gap'):
                        stock.validate_gap()
                        if stock.gap_validated:
                            self.logger.info(f"Gap validated for {symbol}")
                        else:
                            self.logger.info(f"Gap validation failed for {symbol}")
                else:
                    self.logger.info(f"Stock not found for symbol: {symbol}")
        else:
            self.logger.info("IEP FETCH FAILED - FALLING BACK TO OHLC")

        self.logger.info("=== STARTING CONTINUATION TRADING PHASE ===")

        # Connect to data stream
        self.logger.info("ATTEMPTING to connect to data stream...")
        if self.data_streamer.connect():
            self.logger.info("CONNECTED Data stream connected")

            # Wait for market open
            market_open = MARKET_OPEN
            current_time = datetime.now(IST).time()

            if current_time < market_open:
                market_datetime = datetime.combine(datetime.now(IST).date(), market_open)
                market_datetime = IST.localize(market_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (market_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    self.logger.info(f"WAITING {wait_seconds:.0f} seconds for market open...")
                    time_module.sleep(wait_seconds)

            self.logger.info("MARKET OPEN! Monitoring live OHLC data...")

            # Capture initial volume at market open for cumulative tracking
            self.logger.info("CAPTURING initial volume at market open for cumulative tracking...")
            for stock in self.monitor.stocks.values():
                try:
                    initial_volume = upstox_fetcher.get_current_volume(stock.symbol)
                    if initial_volume > 0:
                        stock.initial_volume = initial_volume
                        self.logger.info(f"Initial volume captured for {stock.symbol}: {initial_volume:,}")
                    else:
                        self.logger.info(f"WARNING: No initial volume for {stock.symbol}")
                except Exception as e:
                    self.logger.info(f"ERROR capturing initial volume for {stock.symbol}: {e}")

            # For continuation: IEP-based opening prices (already set at 9:14:30)
            self.logger.info("USING IEP-BASED OPENING PRICES - Set at 9:14:30 from pre-market IEP")
            self.logger.info("Gap validation completed at 9:14:30, ready for trading")

            # Continue with normal entry decision timing
            entry_decision_time = ENTRY_TIME
            current_time = datetime.now(IST).time()

            if current_time < entry_decision_time:
                decision_datetime = datetime.combine(datetime.now(IST).date(), entry_decision_time)
                decision_datetime = IST.localize(decision_datetime)
                current_datetime = datetime.now(IST)
                wait_seconds = (decision_datetime - current_datetime).total_seconds()
                if wait_seconds > 0:
                    self.logger.info(f"\nWAITING {wait_seconds:.0f} seconds until entry decision...")
                    time_module.sleep(wait_seconds)

            # Prepare entries and select stocks
            self.logger.info("\n=== PREPARING ENTRIES ===")

            # Show current status after OHLC-based qualification
            self.logger.info("POST-OHLC QUALIFICATION STATUS:")
            for stock in self.monitor.stocks.values():
                open_status = f"Open: Rs{stock.open_price:.2f}" if stock.open_price else "No opening price"

                gap_pct = 0.0
                if stock.open_price and stock.previous_close:
                    gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100

                gap_status = "Gap validated" if stock.gap_validated else f"Gap: {gap_pct:+.1f}%"
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

                self.logger.info(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status} | {volume_status}{rejection_info}")

            # Apply VAH validation for continuation stocks
            self.logger.info("=== APPLYING VAH VALIDATION ===")
            if global_vah_dict:
                for stock in self.monitor.stocks.values():
                    if stock.situation == 'continuation' and stock.symbol in global_vah_dict:
                        vah_price = global_vah_dict[stock.symbol]
                        if hasattr(stock, 'validate_vah_rejection'):
                            stock.validate_vah_rejection(vah_price)

            self.monitor.prepare_entries()

            qualified_stocks = self.monitor.get_qualified_stocks()
            self.logger.info(f"Qualified stocks: {len(qualified_stocks)}")

            selected_stocks = self.selection_engine.select_stocks(qualified_stocks)
            self.logger.info(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

            # Mark selected stocks as ready
            for stock in selected_stocks:
                stock.entry_ready = True
                self.logger.info(f"READY to trade: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")

            # Initialize selected_stocks for the tick handler
            self.test_results = selected_stocks

            # Keep monitoring for entries, exits, and trailing stops
            self.logger.info("\nMONITORING for entry/exit signals...")
            self.data_streamer.run()

        else:
            self.logger.info("FAILED to connect data stream")
            self.logger.info("CONTINUING without data stream for testing...")

    def run_test(self):
        """Run the complete continuation bot test"""
        print("🚀 Starting Continuation Bot Test")
        print("Testing: Monolithic continuation bot with SVRO entry system")
        print("Setup: All continuation bot features with exact architecture")
        print()

        try:
            # Setup test environment
            self.setup_test_environment()

            # Run test
            self.is_running = True
            self.test_start_time = time.time()

            # Wait for test completion
            max_test_duration = 300  # 5 minutes max
            start_time = time.time()

            while self.is_running and (time.time() - start_time) < max_test_duration:
                time.sleep(1)

            # Stop test
            self.stop_test()

            # Print results
            self._print_results()

            return len(self.test_results) > 0

        except Exception as e:
            self.logger.error(f"Test execution failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def stop_test(self):
        """Stop the test"""
        self.is_running = False

        if self.data_streamer:
            self.data_streamer.stop_streaming()

        self.logger.info("Continuation bot test stopped")

    def _print_results(self):
        """Print test results"""
        print("\n" + "="*60)
        print("CONTINUATION BOT TEST RESULTS")
        print("="*60)

        if not self.test_results:
            print("❌ No entries triggered")
            return

        for stock in self.test_results:
            print(f"\n{stock.symbol} - ✅ TRIGGERED")
            print(f"  Entry Price: {stock.entry_price:.2f}")
            print(f"  Entry High: {stock.entry_high:.2f}")
            print(f"  Entry SL: {stock.entry_sl:.2f}")
            print(f"  Gap: {((stock.open_price - stock.previous_close) / stock.previous_close * 100):+.1f}%")
            print(f"  Volume Ratio: {(stock.early_volume / stock.volume_baseline * 100):.1f}%")
            print(f"  VAH Validation: {'Passed' if hasattr(stock, 'vah_validated') and stock.vah_validated else 'Failed'}")

        print(f"\nTotal Entries: {len(self.test_results)}")
        print("🎉 CONTINUATION BOT TEST COMPLETED!")

    def get_test_summary(self):
        """Get test summary"""
        return {
            'total_stocks': len(self.monitor.stocks) if self.monitor else 0,
            'qualified_stocks': len(self.monitor.get_qualified_stocks()) if self.monitor else 0,
            'selected_stocks': len(self.test_results),
            'entered_positions': len([s for s in self.monitor.stocks.values() if s.entered]) if self.monitor else 0,
            'test_duration': time.time() - self.test_start_time if self.test_start_time else 0
        }


def main():
    """Main test runner"""
    test = ContinuationTest()
    success = test.run_test()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)