"""
Main Live Trading Orchestrator
Coordinates all components for live stock trading
"""

import os
import time
import logging
import sys
from datetime import datetime, time as dt_time
from typing import Dict, List
import pytz

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from .config import (
    REVERSAL_LIST_FILE,
    CONTINUATION_LIST_FILE,
    MARKET_OPEN,
    ENTRY_DECISION_TIME,
    PREP_END,
    LOG_LEVEL,
    LOG_FORMAT
)
from .stock_monitor import StockMonitor
from .rule_engine import RuleEngine
from .selection_engine import SelectionEngine
from .paper_trader import PaperTrader
from .reversal_monitor import ReversalMonitor
from .volume_profile import volume_profile_calculator
try:
    # Try relative import first (when run as part of package)
    from ...utils.upstox_fetcher import UpstoxFetcher
except ImportError:
    # Fallback to absolute import (when run standalone)
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    from utils.upstox_fetcher import UpstoxFetcher

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')


class LiveTradingOrchestrator:
    """Main orchestrator for live trading operations"""

    def __init__(self, reversal_mode=False, config_file=None):
        self.reversal_mode = reversal_mode

        # Use the global working fetcher instance (same as continuation bot)
        from src.utils.upstox_fetcher import upstox_fetcher
        self.upstox_fetcher = upstox_fetcher

        if self.reversal_mode:
            self.reversal_monitor = ReversalMonitor()
            self.monitor = None  # Not used in reversal mode
            self.selection_engine = None  # Not used in reversal mode
        else:
            self.monitor = StockMonitor()
            self.rule_engine = RuleEngine()
            self.selection_engine = SelectionEngine()
            self.reversal_monitor = None  # Not used in continuation mode

        self.paper_trader = PaperTrader()

        self.data_streamer = None
        self.instrument_keys = []
        self.stock_symbols = {}  # instrument_key -> symbol
        self.prev_closes = {}  # symbol -> previous_close

        self.prep_completed = False
        self.trading_active = False

        mode_str = "REVERSAL" if self.reversal_mode else "CONTINUATION"
        logger.info(f"Live Trading Orchestrator initialized - Mode: {mode_str}")

    def load_candidate_stocks(self) -> Dict[str, float]:
        """
        Load candidate stocks from text files and get previous close prices

        Returns:
            Dict of symbol -> previous_close
        """
        candidates = {}

        try:
            if self.reversal_mode:
                # Load reversal candidates
                if os.path.exists(REVERSAL_LIST_FILE):
                    with open(REVERSAL_LIST_FILE, 'r') as f:
                        content = f.read()
                        if content and not content.startswith('#'):
                            symbols = [s.strip() for s in content.split(',') if s.strip()]
                            for symbol in symbols:
                                candidates[symbol] = None  # Will fetch previous close later
                    logger.info(f"Loaded {len(candidates)} reversal candidates")
                else:
                    logger.error("Reversal list file not found")
            else:
                # Load continuation candidates
                if os.path.exists(CONTINUATION_LIST_FILE):
                    with open(CONTINUATION_LIST_FILE, 'r') as f:
                        symbols = [s.strip() for s in f.read().split(',') if s.strip()]
                        for symbol in symbols:
                            candidates[symbol] = None  # Will fetch previous close later
                    logger.info(f"Loaded {len(candidates)} continuation candidates")
                else:
                    logger.error("Continuation list file not found")

        except Exception as e:
            logger.error(f"Error loading candidate stocks: {e}")

        return candidates

    def get_previous_closes(self, symbols: List[str]) -> Dict[str, float]:
        """Get previous close prices for symbols using LTP API 'cp' field"""
        prev_closes = {}

        for symbol in symbols:
            try:
                # Use LTP API to get 'cp' field (previous close) as recommended by expert
                ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
                if ltp_data and 'cp' in ltp_data and ltp_data['cp'] is not None:
                    prev_closes[symbol] = float(ltp_data['cp'])
                    logger.info(f"{symbol}: Previous close ₹{prev_closes[symbol]:.2f} (from LTP 'cp' field)")
                else:
                    logger.warning(f"Could not get 'cp' field for {symbol}, LTP data: {ltp_data}")
                    prev_closes[symbol] = 0.0  # Fallback

            except Exception as e:
                logger.error(f"Error getting LTP data for {symbol}: {e}")
                prev_closes[symbol] = 0.0

        return prev_closes

    def prepare_instruments(self, candidates: Dict[str, float]) -> bool:
        """Prepare instrument keys for subscription"""
        try:
            self.instrument_keys = []
            self.stock_symbols = {}
            self.prev_closes = {}

            for symbol, prev_close in candidates.items():
                if prev_close is None:
                    continue

                # Store previous close for reversal mode
                self.prev_closes[symbol] = prev_close

                # For reversal mode, extract clean symbol name for API calls
                if self.reversal_mode:
                    clean_symbol = symbol.split('-')[0]  # Remove -u/-d suffix
                else:
                    clean_symbol = symbol

                # Get instrument key using clean symbol name
                instrument_key = self.upstox_fetcher.get_instrument_key(clean_symbol)
                if instrument_key:
                    self.instrument_keys.append(instrument_key)
                    self.stock_symbols[instrument_key] = symbol  # Keep original symbol for tracking

                    if not self.reversal_mode:
                        # Add to continuation monitor
                        self.monitor.add_stock(symbol, instrument_key, prev_close)
                else:
                    logger.error(f"Could not get instrument key for {symbol} (clean: {clean_symbol})")

            logger.info(f"Prepared {len(self.instrument_keys)} instruments for subscription")
            return len(self.instrument_keys) > 0

        except Exception as e:
            logger.error(f"Error preparing instruments: {e}")
            return False

    def prep_phase(self) -> bool:
        """Preparation phase: Load candidates, get data, prepare subscriptions"""
        logger.info("=== STARTING PREP PHASE ===")

        try:
            # Load candidate stocks
            candidates = self.load_candidate_stocks()
            if not candidates:
                logger.error("No candidate stocks loaded")
                return False

            # Get previous close prices - extract clean symbols from reversal format
            symbols = list(candidates.keys())

            # For reversal mode, extract clean symbol names (remove -u/-d suffixes)
            if self.reversal_mode:
                clean_symbols = []
                for symbol in symbols:
                    # Remove the -u/-d suffix (e.g., "ELECON-u6" -> "ELECON")
                    clean_symbol = symbol.split('-')[0]
                    clean_symbols.append(clean_symbol)
                api_symbols = clean_symbols
            else:
                api_symbols = symbols

            prev_closes = self.get_previous_closes(api_symbols)

            # For reversal mode, map back to original symbol keys
            if self.reversal_mode:
                symbol_mapping = {symbol.split('-')[0]: symbol for symbol in symbols}
                mapped_prev_closes = {}
                for clean_symbol, prev_close in prev_closes.items():
                    original_symbol = symbol_mapping.get(clean_symbol, clean_symbol)
                    mapped_prev_closes[original_symbol] = prev_close
                prev_closes = mapped_prev_closes

            # Update candidates with prev closes
            candidates.update(prev_closes)

            # Prepare instruments
            if not self.prepare_instruments(candidates):
                logger.error("Failed to prepare instruments")
                return False

            if not self.reversal_mode:
                # Preload stock scoring metadata for continuation
                from .stock_scorer import stock_scorer
                stock_scorer.preload_metadata(symbols)

                # Calculate VAH (Value Area High) from previous day's volume profile
                logger.info("Calculating VAH from previous day's volume profile...")
                self.vah_dict = volume_profile_calculator.calculate_vah_for_stocks(symbols)
                logger.info(f"VAH calculated for {len(self.vah_dict)} stocks")

                # Set selection method to quality_score
                self.selection_engine.set_selection_method("quality_score")
            else:
                # Load reversal watchlist and rank stocks - do this in prep phase
                success = self.reversal_monitor.load_watchlist(REVERSAL_LIST_FILE)
                if not success:
                    logger.error("Failed to load reversal watchlist")
                    return False

                # Set previous closes for all stocks in watchlist
                self.reversal_monitor.set_prev_closes(prev_closes)

                # Preload stock scoring metadata for reversal (should be done in prep phase)
                # For reversal mode, use clean symbol names (remove -u/-d suffixes)
                clean_symbols = []
                for symbol in symbols:
                    # Remove the -u/-d suffix (e.g., "ELECON-u6" -> "ELECON")
                    clean_symbol = symbol.split('-')[0]
                    clean_symbols.append(clean_symbol)
                
                logger.info("Preloading stock scoring metadata for reversal...")
                from .stock_scorer import stock_scorer
                stock_scorer.preload_metadata(clean_symbols)
                logger.info(f"Stock scoring metadata preloaded for {len(clean_symbols)} reversal stocks")

                # Rank stocks by quality score
                self.reversal_monitor.rank_stocks_by_quality()

            # Initialize data streamer (using simple version for now)
            try:
                from .simple_data_streamer import SimpleStockStreamer
                self.data_streamer = SimpleStockStreamer(self.instrument_keys, self.stock_symbols)
                self.data_streamer.tick_handler = self.handle_tick
            except ImportError:
                logger.error("Simple streamer not available, trying complex streamer")
                from .data_streamer import StockDataStreamer
                self.data_streamer = StockDataStreamer(self.instrument_keys, self.stock_symbols)
                self.data_streamer.tick_handler = self.handle_tick

            logger.info("=== PREP PHASE COMPLETED ===")
            self.prep_completed = True
            return True

        except Exception as e:
            logger.error(f"Error in prep phase: {e}")
            return False

    def handle_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_data=None):
        """Handle incoming tick data"""
        try:
            if self.reversal_mode:
                # Handle reversal mode - use first tick tracking (expert's solution)
                # Only update tick if stock exists in watchlist (should be preloaded)
                stock = self.reversal_monitor.find_stock_in_watchlist(symbol)
                if stock:
                    # Update tick data (this should not trigger cache loading if done properly)
                    self.reversal_monitor.update_stock_tick(symbol, price, timestamp)

                    # Track current low for Strong Start conditions
                    if price < stock.current_low:
                        stock.current_low = price

                    if stock.first_tick_captured:
                        # Calculate gap if not already done
                        if not stock.gap_calculated and hasattr(stock, 'prev_close') and stock.prev_close:
                            self.reversal_monitor.calculate_stock_gap(stock)

                        # Check for OOPS conditions
                        if stock.gap_calculated and self.reversal_monitor.check_oops_conditions(stock, price):
                            if self.reversal_monitor.active_positions < self.reversal_monitor.max_positions:
                                # Execute OOPS trade
                                stock.triggered = True
                                stock.entry_price = price
                                stock.stop_loss = price * 0.96
                                self.reversal_monitor.active_positions += 1
                                self.reversal_monitor.log_paper_trade(symbol, "ENTRY", price, "OOPS")

                        # Check for Strong Start conditions
                        if stock.gap_calculated and self.reversal_monitor.check_strong_start_conditions(stock, stock.current_low):
                            if self.reversal_monitor.active_positions < self.reversal_monitor.max_positions:
                                # Execute Strong Start trade
                                stock.triggered = True
                                stock.entry_price = price
                                stock.stop_loss = price * 0.96
                                self.reversal_monitor.active_positions += 1
                                self.reversal_monitor.log_paper_trade(symbol, "ENTRY", price, "Strong Start")
            else:
                # Handle continuation mode
                self.monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_data)

                # Check for violations during confirmation window
                current_time = datetime.now(IST).time()
                if MARKET_OPEN <= current_time <= ENTRY_DECISION_TIME:
                    self.monitor.check_violations()

                # Check entry signals
                entry_signals = self.monitor.check_entry_signals()
                for stock in entry_signals:
                    self.execute_entry(stock, price, timestamp)

                # Check exit signals
                exit_signals = self.monitor.check_exit_signals()
                for stock in exit_signals:
                    self.execute_exit(stock, price, timestamp, "Stop Loss Hit")

        except Exception as e:
            logger.error(f"Error handling tick for {symbol}: {e}")

    def execute_entry(self, stock, price: float, timestamp: datetime):
        """Execute entry trade"""
        try:
            # Enter position
            stock.enter_position(price, timestamp)

            # Log to paper trader
            self.paper_trader.log_entry(stock, price, timestamp)

            logger.info(f"ENTERED: {stock.symbol} at {price:.2f}")

        except Exception as e:
            logger.error(f"Error executing entry for {stock.symbol}: {e}")

    def execute_exit(self, stock, price: float, timestamp: datetime, reason: str):
        """Execute exit trade"""
        try:
            # Exit position
            stock.exit_position(price, timestamp, reason)

            # Log to paper trader
            self.paper_trader.log_exit(stock, price, timestamp, reason)

            logger.info(f"EXITED: {stock.symbol} at {price:.2f} | {reason}")

        except Exception as e:
            logger.error(f"Error executing exit for {stock.symbol}: {e}")

    def trading_phase(self) -> bool:
        """Live trading phase: Monitor and trade"""
        logger.info("=== STARTING TRADING PHASE ===")

        try:
            self.trading_active = True

            # Start data streaming
            if not self.data_streamer.connect():
                logger.error("Failed to connect data streamer")
                return False

            # Wait for market open
            self.wait_for_market_open()

            # Apply VAH filtering for continuation mode
            if not self.reversal_mode:
                self.apply_vah_filtering()

            if self.reversal_mode:
                # Reversal mode: Continuous monitoring throughout the day
                logger.info("Reversal mode: Starting continuous monitoring...")

                # Start data streaming in a separate thread or process
                import threading
                stream_thread = threading.Thread(target=self.data_streamer.run)
                stream_thread.start()

                # Main trading loop for market context logic
                while self.trading_active:
                    current_time = datetime.now(IST).time()

                    # Collect market data for context analysis
                    market_data = {}
                    for symbol in self.stock_symbols.values():
                        try:
                            # For reversal mode, extract clean symbol name for API calls
                            if self.reversal_mode:
                                clean_symbol = symbol.split('-')[0]  # Remove -u/-d suffix
                            else:
                                clean_symbol = symbol

                            ltp_data = self.upstox_fetcher.get_ltp_data(clean_symbol)
                            if ltp_data:
                                market_data[symbol] = ltp_data  # Keep original symbol as key
                        except Exception as e:
                            logger.error(f"Error getting market data for {symbol}: {e}")

                    # Execute market context logic
                    self.reversal_monitor.execute_market_context_logic(market_data, current_time)

                    # Sleep briefly to avoid CPU overload
                    time.sleep(1)

                # Wait for stream thread to finish
                stream_thread.join()
            else:
                # Continuation mode: 9:19 selection logic
                # Monitor until end of day or stopped
                while self.trading_active:
                    current_time = datetime.now(IST).time()

                    # At 9:19, prepare entries and select stocks
                    if current_time >= ENTRY_DECISION_TIME:
                        # Check volume validations for SVRO continuation stocks
                        if not self.reversal_mode:
                            self.monitor.check_volume_validations()

                        self.prepare_and_select_stocks()
                        break  # Exit loop after setup

                    time.sleep(1)

                # Keep monitoring for entries/exits
                logger.info("Continuation mode: Monitoring for entry/exit signals...")
                self.data_streamer.run()

            return True

        except Exception as e:
            logger.error(f"Error in trading phase: {e}")
            return False
        finally:
            self.trading_active = False

    def get_current_time_str(self):
        """Get current time as HH:MM string"""
        return datetime.now(IST).strftime("%H:%M")

    def wait_for_market_open(self):
        """Wait until market opens"""
        logger.info("Waiting for market open...")

        market_open_str = MARKET_OPEN.strftime("%H:%M")
        current_time_str = self.get_current_time_str()
        
        # Check if market is already open
        if current_time_str >= market_open_str:
            logger.info(f"Market already open! Current: {current_time_str}, Open: {market_open_str}")
            return

        # Wait until market opens
        while True:
            current_time_str = self.get_current_time_str()
            if current_time_str >= market_open_str:
                logger.info("Market opened!")
                break
            time.sleep(1)

    def apply_vah_filtering(self):
        """Apply VAH filtering: reject stocks that open below previous day's VAH"""
        logger.info("=== APPLYING VALUE AREA FILTERING (SVRO Component) ===")

        try:
            rejected_count = 0
            qualified_count = 0

            # Get opening prices for all stocks
            for stock in self.monitor.get_active_stocks():
                try:
                    # Get opening price from LTP API
                    ltp_data = self.upstox_fetcher.get_ltp_data(stock.symbol)
                    if ltp_data and 'open_price' in ltp_data and ltp_data['open_price']:
                        open_price = float(ltp_data['open_price'])
                        stock.set_open_price(open_price)

                        # Calculate gap percentage
                        prev_close = self.prev_closes.get(stock.symbol, 0)
                        if prev_close > 0:
                            gap_pct = ((open_price - prev_close) / prev_close) * 100
                        else:
                            gap_pct = 0.0

                        # Check VAH condition
                        vah = self.vah_dict.get(stock.symbol)
                        if vah is not None:
                            vah_status = "VAH OK" if open_price >= vah else "Below VAH"
                            gap_status = "Gap Up" if gap_pct > 0 else "Gap Down"

                            if open_price < vah:
                                # Reject stock
                                stock.reject(f"Opened below VAH (Open: ₹{open_price:.2f} < VAH: ₹{vah:.2f})")
                                self.paper_trader.log_rejection(stock, stock.rejection_reason)
                                rejected_count += 1
                                status = "REJECTED"
                            else:
                                qualified_count += 1
                                status = "QUALIFIED"

                            # Enhanced logging with SVRO details
                            logger.info(f"{stock.symbol}: Open ₹{open_price:.2f} | {gap_status} {gap_pct:+.2f}% | VAH ₹{vah:.2f} | {vah_status} | {status}")
                        else:
                            logger.warning(f"{stock.symbol}: Open ₹{open_price:.2f} | {gap_status} {gap_pct:+.2f}% | No VAH data | SKIPPED")
                    else:
                        logger.warning(f"Could not get opening price for {stock.symbol}")
                except Exception as e:
                    logger.error(f"Error applying VAH filter for {stock.symbol}: {e}")

            logger.info(f"Value Area filtering complete: {qualified_count} qualified, {rejected_count} rejected")

        except Exception as e:
            logger.error(f"Error in Value Area filtering: {e}")

    def prepare_and_select_stocks(self):
        """Prepare entry levels and select stocks to trade"""
        logger.info("=== PREPARING ENTRIES AT 9:19 ===")

        # Prepare entry levels for qualified stocks
        self.monitor.prepare_entries()

        # Get qualified stocks
        qualified_stocks = self.monitor.get_qualified_stocks()
        logger.info(f"Qualified stocks: {len(qualified_stocks)}")

        # Log rejections
        for stock in self.monitor.stocks.values():
            if not stock.is_active:
                self.paper_trader.log_rejection(stock, stock.rejection_reason or "Unknown")

        if not qualified_stocks:
            logger.warning("No qualified stocks for selection")
            return

        # Select stocks to trade
        selected_stocks = self.selection_engine.select_stocks(qualified_stocks)
        logger.info(f"Selected {len(selected_stocks)} stocks for trading: {[s.symbol for s in selected_stocks]}")

        # Mark selected stocks as ready for entry
        for stock in selected_stocks:
            stock.entry_ready = True
            logger.info(f"Ready to trade: {stock.symbol} (Entry: {stock.entry_high:.2f}, SL: {stock.entry_sl:.2f})")

    def run(self):
        """Main run method with graceful WebSocket cleanup"""
        try:
            logger.info("=== LIVE TRADING BOT STARTED ===")

            # Prep phase
            logger.info("Starting prep phase...")
            prep_result = self.prep_phase()
            logger.info(f"Prep phase completed with result: {prep_result}")

            if not prep_result:
                logger.error("Prep phase failed - exiting")
                return

            logger.info("Prep phase successful, proceeding to timing logic...")

            # Wait until prep end time
            current_time = datetime.now(IST).time()
            prep_end_time = PREP_END
            
            logger.info(f"Current time: {current_time.strftime('%H:%M:%S')}, Prep end time: {prep_end_time.strftime('%H:%M:%S')}")

            # Compare times properly (not strings)
            if current_time < prep_end_time:
                # Calculate seconds until prep end
                current_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
                prep_seconds = prep_end_time.hour * 3600 + prep_end_time.minute * 60 + prep_end_time.second
                wait_seconds = prep_seconds - current_seconds

                logger.info(f"Calculated wait time: {wait_seconds} seconds")

                if wait_seconds > 0:
                    logger.info(f"Waiting {wait_seconds:.0f} seconds until prep end...")
                    import time
                    time.sleep(wait_seconds)
                    logger.info("Wait completed, proceeding to trading phase...")
                else:
                    logger.info("No wait needed, proceeding immediately...")
            else:
                logger.info("Past prep end time, proceeding to trading phase...")

            # Trading phase
            logger.info("Starting trading phase...")
            trading_result = self.trading_phase()
            logger.info(f"Trading phase completed with result: {trading_result}")

            if not trading_result:
                logger.error("Trading phase failed")
                return

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt - initiating graceful cleanup")
        except Exception as e:
            logger.error(f"Error in main run: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            # GRACEFUL WEBSOCKET CLEANUP (prevents lingering connections)
            logger.info("Initiating graceful WebSocket cleanup...")
            try:
                if hasattr(self, 'data_streamer') and self.data_streamer:
                    self.data_streamer.disconnect()
                    logger.info("WebSocket disconnected gracefully")
                    import time
                    time.sleep(2)  # Give server time to process disconnect
                else:
                    logger.info("No active data streamer to disconnect")
            except Exception as cleanup_err:
                logger.error(f"WebSocket cleanup error: {cleanup_err}")

            # Continue with normal cleanup
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info("=== CLEANUP ===")

        try:
            if self.data_streamer:
                self.data_streamer.disconnect()

            if not self.reversal_mode:
                # Log final summary for continuation mode
                summary = self.monitor.get_summary()
                self.paper_trader.log_session_summary(summary)

                # Export to CSV
                self.paper_trader.export_trades_csv()

            # Note: Reversal mode doesn't use paper trader for now
            # Could be extended later to track reversal trades

            self.paper_trader.close()

            logger.info("=== SESSION ENDED ===")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def stop(self):
        """Stop trading"""
        logger.info("Stopping live trading...")
        self.trading_active = False
        if self.data_streamer:
            self.data_streamer.running = False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Live Trading Bot')
    parser.add_argument('--reversal', action='store_true',
                       help='Run in reversal trading mode instead of continuation')

    args = parser.parse_args()

    # Initialize orchestrator with reversal mode if requested
    orchestrator = LiveTradingOrchestrator(reversal_mode=args.reversal)

    try:
        orchestrator.run()
    except KeyboardInterrupt:
        orchestrator.stop()
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()
