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

from config import *
from .stock_monitor import StockMonitor
from .rule_engine import RuleEngine
from .selection_engine import SelectionEngine
from .paper_trader import PaperTrader
from ..utils.upstox_fetcher import UpstoxFetcher

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')


class LiveTradingOrchestrator:
    """Main orchestrator for live trading operations"""

    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.monitor = StockMonitor()
        self.rule_engine = RuleEngine()
        self.selection_engine = SelectionEngine()
        self.paper_trader = PaperTrader()

        self.data_streamer = None
        self.instrument_keys = []
        self.stock_symbols = {}  # instrument_key -> symbol

        self.prep_completed = False
        self.trading_active = False

        logger.info("Live Trading Orchestrator initialized")

    def load_candidate_stocks(self) -> Dict[str, float]:
        """
        Load candidate stocks from text files and get previous close prices

        Returns:
            Dict of symbol -> previous_close
        """
        candidates = {}

        try:
            # Load continuation candidates
            if os.path.exists(CONTINUATION_LIST_FILE):
                with open(CONTINUATION_LIST_FILE, 'r') as f:
                    symbols = [s.strip() for s in f.read().split(',') if s.strip()]
                    for symbol in symbols:
                        candidates[symbol] = None  # Will fetch previous close later

            # Load reversal candidates (for future)
            if os.path.exists(REVERSAL_LIST_FILE):
                with open(REVERSAL_LIST_FILE, 'r') as f:
                    content = f.read()
                    if content and not content.startswith('#'):
                        symbols = [s.strip() for s in content.split(',') if s.strip()]
                        for symbol in symbols:
                            candidates[symbol] = None

            logger.info(f"Loaded {len(candidates)} candidate stocks")

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
                    logger.info(f"✅ {symbol}: Previous close ₹{prev_closes[symbol]:.2f} (from LTP 'cp' field)")
                else:
                    logger.warning(f"❌ Could not get 'cp' field for {symbol}, LTP data: {ltp_data}")
                    prev_closes[symbol] = 0.0  # Fallback

            except Exception as e:
                logger.error(f"❌ Error getting LTP data for {symbol}: {e}")
                prev_closes[symbol] = 0.0

        return prev_closes

    def prepare_instruments(self, candidates: Dict[str, float]) -> bool:
        """Prepare instrument keys for subscription"""
        try:
            self.instrument_keys = []
            self.stock_symbols = {}

            for symbol, prev_close in candidates.items():
                if prev_close is None:
                    continue

                # Get instrument key
                instrument_key = self.upstox_fetcher.get_instrument_key(symbol)
                if instrument_key:
                    self.instrument_keys.append(instrument_key)
                    self.stock_symbols[instrument_key] = symbol

                    # Add to monitor
                    self.monitor.add_stock(symbol, instrument_key, prev_close)
                else:
                    logger.error(f"Could not get instrument key for {symbol}")

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

            # Get previous close prices
            symbols = list(candidates.keys())
            prev_closes = self.get_previous_closes(symbols)

            # Update candidates with prev closes
            candidates.update(prev_closes)

            # Prepare instruments
            if not self.prepare_instruments(candidates):
                logger.error("Failed to prepare instruments")
                return False

            # Preload stock scoring metadata
            from .stock_scorer import stock_scorer
            stock_scorer.preload_metadata(symbols)

            # Set selection method to quality_score
            self.selection_engine.set_selection_method("quality_score")

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
            # Process tick in monitor (now includes ohlc_data)
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

            logger.info(f"✅ ENTERED: {stock.symbol} at {price:.2f}")

        except Exception as e:
            logger.error(f"Error executing entry for {stock.symbol}: {e}")

    def execute_exit(self, stock, price: float, timestamp: datetime, reason: str):
        """Execute exit trade"""
        try:
            # Exit position
            stock.exit_position(price, timestamp, reason)

            # Log to paper trader
            self.paper_trader.log_exit(stock, price, timestamp, reason)

            logger.info(f"✅ EXITED: {stock.symbol} at {price:.2f} | {reason}")

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

            # Monitor until end of day or stopped
            while self.trading_active:
                current_time = datetime.now(IST).time()

                # At 9:19, prepare entries and select stocks
                if current_time >= ENTRY_DECISION_TIME:
                    self.prepare_and_select_stocks()
                    break  # Exit loop after setup

                time.sleep(1)

            # Keep monitoring for entries/exits
            logger.info("Monitoring for entry/exit signals...")
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
        while True:
            current_time = self.get_current_time_str()
            if current_time >= market_open_str:
                logger.info("Market opened!")
                break
            time.sleep(1)

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
            logger.info(f"🎯 Ready to trade: {stock.symbol} (Entry: {stock.entry_high:.2f}, SL: {stock.entry_sl:.2f})")

    def run(self):
        """Main run method"""
        try:
            logger.info("=== LIVE TRADING BOT STARTED ===")

            # Prep phase
            if not self.prep_phase():
                logger.error("Prep phase failed")
                return

            # Wait until prep end time (convert to string comparison like options bot)
            prep_end_str = PREP_END.strftime("%H:%M")
            current_time_str = self.get_current_time_str()
            if current_time_str < prep_end_str:
                # Calculate seconds until prep end
                current_seconds = datetime.now(IST).hour * 3600 + datetime.now(IST).minute * 60 + datetime.now(IST).second
                prep_seconds = PREP_END.hour * 3600 + PREP_END.minute * 60 + PREP_END.second
                wait_seconds = prep_seconds - current_seconds

                if wait_seconds > 0:
                    logger.info(f"Waiting {wait_seconds:.0f} seconds until prep end...")
                    import time
                    time.sleep(wait_seconds)

            # Trading phase
            if not self.trading_phase():
                logger.error("Trading phase failed")
                return

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in main run: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources"""
        logger.info("=== CLEANUP ===")

        try:
            if self.data_streamer:
                self.data_streamer.disconnect()

            # Log final summary
            summary = self.monitor.get_summary()
            self.paper_trader.log_session_summary(summary)

            # Export to CSV
            self.paper_trader.export_trades_csv()

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
    orchestrator = LiveTradingOrchestrator()
    try:
        orchestrator.run()
    except KeyboardInterrupt:
        orchestrator.stop()
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()
