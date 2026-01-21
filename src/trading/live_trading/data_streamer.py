"""
Adapted Data Streamer for Stock Live Trading
Based on option-trading-bot/upstox/data_streamer.py but modified for stocks
"""

import upstox_client
import json
from datetime import datetime
import pytz
import signal
import sys
import logging
import os
from typing import Dict, List, Optional

# Load Upstox config
UPSTOX_CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'upstox_config.json')
with open(UPSTOX_CONFIG_FILE, 'r') as f:
    upstox_config = json.load(f)

ACCESS_TOKEN = upstox_config['access_token']

# Import config values
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import *

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class StockDataStreamer:
    """WebSocket data streamer adapted for stocks"""

    def __init__(self, instrument_keys: List[str], stock_symbols: Dict[str, str]):
        """
        Args:
            instrument_keys: List of Upstox instrument keys to subscribe
            stock_symbols: Dict mapping instrument_key -> symbol for logging
        """
        self.instrument_keys = instrument_keys
        self.stock_symbols = stock_symbols
        self.running = True
        self.streamer = None

        # Setup signal handling
        signal.signal(signal.SIGINT, self.signal_handler)

        # Connection tracking
        self.connected = False
        self.subscription_successful = False

        logger.info(f"Monitoring {len(instrument_keys)} stocks: {list(stock_symbols.values())}")

    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Shutting down streamer...")
        self.running = False
        if self.streamer:
            self.streamer.disconnect()
        sys.exit(0)

    def now(self) -> str:
        """Current time in IST"""
        return datetime.now(IST).strftime("%H:%M:%S.%f")[:-3]

    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        current_time = datetime.now(IST).strftime("%H:%M")
        return MARKET_START <= current_time <= MARKET_END

    def is_confirmation_window_open(self) -> bool:
        """Check if we're in the 5-minute confirmation window (9:15-9:20)"""
        current_time = datetime.now(IST).time()
        return MARKET_OPEN <= current_time <= ENTRY_DECISION_TIME

    def on_message(self, message):
        """WebSocket message handler - adapted for stocks"""
        try:
            # Handle marketInfo messages (metadata)
            if isinstance(message, dict) and 'marketInfo' in message:
                return

            # ==================================================================================
            # DICT FEED HANDLER (SDK 2.17.0+ auto-decodes protobuf to dict)
            # ==================================================================================
            if isinstance(message, dict) and 'feeds' in message:
                feeds = message['feeds']

                for instrument_key, feed_data in feeds.items():
                    if instrument_key not in self.stock_symbols:
                        continue

                    symbol = self.stock_symbols[instrument_key]

                    # Extract LTP and timestamp
                    ltp = None
                    timestamp = None
                    ohlc_data = None

                    if isinstance(feed_data, dict):
                        # Path 1: fullFeed → marketFF → ltpc (FULL mode)
                        if 'fullFeed' in feed_data:
                            full_feed = feed_data['fullFeed']
                            if isinstance(full_feed, dict) and 'marketFF' in full_feed:
                                market_ff = full_feed['marketFF']
                                if isinstance(market_ff, dict):
                                    # Extract LTPC
                                    if 'ltpc' in market_ff:
                                        ltpc_data = market_ff['ltpc']
                                        if isinstance(ltpc_data, dict):
                                            ltp = ltpc_data.get('ltp')
                                            ltt = ltpc_data.get('ltt', 0)
                                            timestamp = datetime.fromtimestamp(int(ltt) / 1000, IST) if ltt else datetime.now(IST)

                                    # Extract OHLC (for 1-min candles)
                                    if 'marketOHLC' in market_ff:
                                        market_ohlc = market_ff['marketOHLC']
                                        if isinstance(market_ohlc, dict) and 'ohlc' in market_ohlc:
                                            ohlc_list = market_ohlc['ohlc']
                                            # Get the most recent 1-min candle
                                            i1_candles = [c for c in ohlc_list if c.get('interval') == 'I1']
                                            if i1_candles:
                                                ohlc_data = max(i1_candles, key=lambda c: c.get('ts', 0))

                        # Path 2: ltpc directly (LTPC-only mode)
                        elif 'ltpc' in feed_data:
                            ltpc_data = feed_data['ltpc']
                            if isinstance(ltpc_data, dict):
                                ltp = ltpc_data.get('ltp')
                                ltt = ltpc_data.get('ltt', 0)
                                timestamp = datetime.fromtimestamp(int(ltt) / 1000, IST) if ltt else datetime.now(IST)

                    # Skip if no LTP
                    if ltp is None:
                        continue

                    ltp = float(ltp)
                    if timestamp is None:
                        timestamp = datetime.now(IST)

                    # Pass tick to external handler (will be set by main orchestrator)
                    if hasattr(self, 'tick_handler'):
                        self.tick_handler(instrument_key, symbol, ltp, timestamp, ohlc_data)

                    if PRINT_TICKS:
                        logger.debug(f"[{symbol}] LTP: {ltp:.2f} at {timestamp.strftime('%H:%M:%S')}")

                return

            # Handle other dict messages silently
            if isinstance(message, dict):
                return

            # ==================================================================================
            # PROTOBUF BINARY HANDLER (Fallback for older SDK versions)
            # ==================================================================================
            if isinstance(message, bytes):
                try:
                    from option_trading_bot.upstox.MarketDataFeedV3_pb2 import FeedResponse
                    feed_response = FeedResponse()
                    feed_response.ParseFromString(message)

                    # Skip if not live feed
                    if not feed_response.feeds:
                        return

                    # Process feeds from protobuf
                    for instrument_key, feed_data in feed_response.feeds.items():
                        if instrument_key not in self.stock_symbols:
                            continue

                        symbol = self.stock_symbols[instrument_key]

                        # Extract data from protobuf structure
                        ltp = None
                        timestamp = None
                        ohlc_data = None

                        # Try fullFeed path
                        if feed_data.HasField('fullFeed'):
                            full_feed = feed_data.fullFeed
                            if full_feed.HasField('marketFF'):
                                market_ff = full_feed.marketFF
                                if market_ff.HasField('ltpc'):
                                    ltpc = market_ff.ltpc
                                    ltp = float(ltpc.ltp)
                                    timestamp = datetime.fromtimestamp(ltpc.ltt / 1000, IST) if ltpc.ltt else datetime.now(IST)

                                # Process OHLC
                                if market_ff.HasField('marketOHLC'):
                                    market_ohlc = market_ff.marketOHLC
                                    for ohlc_item in market_ohlc.ohlc:
                                        if ohlc_item.interval == "I1":
                                            ohlc_data = {
                                                'interval': 'I1',
                                                'ts': ohlc_item.ts,
                                                'open': ohlc_item.open,
                                                'high': ohlc_item.high,
                                                'low': ohlc_item.low,
                                                'close': ohlc_item.close
                                            }
                                            break

                        # Try ltpc-only path
                        elif feed_data.HasField('ltpc'):
                            ltpc = feed_data.ltpc
                            ltp = float(ltpc.ltp)
                            timestamp = datetime.fromtimestamp(ltpc.ltt / 1000, IST) if ltpc.ltt else datetime.now(IST)

                        if ltp is None:
                            continue

                        # Pass tick to external handler
                        if hasattr(self, 'tick_handler'):
                            self.tick_handler(instrument_key, symbol, ltp, timestamp, ohlc_data)

                except Exception as e:
                    logger.error(f"Protobuf decode error: {e}")
                    return

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def on_open(self):
        """Called when WebSocket opens"""
        logger.info("WebSocket connected")
        self.connected = True
        import time
        time.sleep(2)

        # Subscribe to instruments
        try:
            self.streamer.subscribe(self.instrument_keys, SUBSCRIPTION_MODE)
            self.subscription_successful = True
            logger.info(f"Subscribed to {len(self.instrument_keys)} instruments")
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            self.running = False

    def on_error(self, error):
        """WebSocket error handler"""
        logger.error(f"WebSocket error: {error}")
        self.connected = False

    def on_close(self, *args):
        """WebSocket close handler"""
        logger.warning("WebSocket closed")
        self.connected = False
        self.running = False

    def connect(self):
        """Establish WebSocket connection with retry logic"""
        configuration = upstox_client.Configuration()
        configuration.access_token = ACCESS_TOKEN

        for attempt in range(MAX_RETRIES):
            try:
                self.streamer = upstox_client.MarketDataStreamerV3(
                    upstox_client.ApiClient(configuration)
                )

                # Register callbacks
                self.streamer.on("open", self.on_open)
                self.streamer.on("message", self.on_message)
                self.streamer.on("error", self.on_error)
                self.streamer.on("close", self.on_close)

                logger.info("Connecting to market data...")
                self.streamer.connect()

                # Wait for connection and subscription
                timeout = 10
                start_time = time.time()
                while not self.subscription_successful and (time.time() - start_time) < timeout:
                    time.sleep(0.5)

                if self.subscription_successful:
                    logger.info("Live data streaming started")
                    return True
                else:
                    raise Exception("Subscription failed")

            except Exception as e:
                logger.error(f"Connection failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"🔄 Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("Max retries reached")
                    return False

        return False

    def disconnect(self):
        """Disconnect WebSocket"""
        if self.streamer:
            self.streamer.disconnect()
        self.connected = False
        self.running = False

    def run(self):
        """Main run loop - blocks until stopped"""
        if not self.connect():
            return False

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.disconnect()

        return True
