# -*- coding: utf-8 -*-
"""
Simplified Data Streamer for Live Testing
Minimal imports to avoid conflicts with upstox_client
"""

import upstox_client
import json
import os
import sys
import logging
from datetime import datetime, timedelta
import pytz

# Minimal setup
logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class SimpleStockStreamer:
    """Minimal WebSocket streamer for testing"""

    def __init__(self, instrument_keys, stock_symbols):
        self.instrument_keys = instrument_keys
        self.stock_symbols = stock_symbols
        self.streamer = None
        self.connected = False
        self.running = True
        self.reconnecting = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5
        self.last_connection_time = None
        self.last_disconnection_time = None
        self.reconnection_reason = None

        # Track active subscriptions - only these will be re-subscribed on reconnection
        self.active_instruments = set(instrument_keys.copy())
        
        # Track intentional disconnections to prevent unwanted reconnections
        self.intentional_disconnect = False
        
        # Load access token directly
        config_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'upstox_config.json')
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.access_token = config['access_token']

        logger.info(f"Simple streamer monitoring {len(instrument_keys)} stocks")
    
    def update_active_instruments(self, new_instrument_keys):
        """
        Update the active instruments list to only include validated stocks
        This fixes the subscription tracking discrepancy
        
        Args:
            new_instrument_keys: List of instrument keys to track (only validated stocks)
        """
        self.active_instruments = set(new_instrument_keys)
        logger.info(f"Updated active instruments to {len(new_instrument_keys)} validated stocks")
        print(f"Active instruments updated to {len(new_instrument_keys)} validated stocks")
    
    def update_active_instruments_reversal(self, new_instrument_keys):
        """
        Update the active instruments list to only include gap-validated stocks for reversal bot
        This fixes the subscription tracking discrepancy
        
        Args:
            new_instrument_keys: List of instrument keys to track (only gap-validated stocks)
        """
        self.active_instruments = set(new_instrument_keys)
        logger.info(f"Updated active instruments to {len(new_instrument_keys)} gap-validated stocks")
        print(f"Active instruments updated to {len(new_instrument_keys)} gap-validated stocks")

    def on_message(self, message):
        """Handle WebSocket messages"""
        try:
            # Handle different message formats
            if isinstance(message, list):
                # Sometimes messages come as a list of dicts
                for msg_item in message:
                    self._process_message_dict(msg_item)
            elif isinstance(message, dict):
                self._process_message_dict(message)
            else:
                # Unknown message format
                logger.warning(f"Unknown message format: {type(message)}")

        except Exception as e:
            # Avoid formatting errors with None values
            error_msg = str(e) if e is not None else "Unknown error"
            logger.error(f"Message processing error: {error_msg}")

    def _process_message_dict(self, message):
        """Process a single message dictionary"""
        if 'feeds' in message:
            feeds = message['feeds']
            current_time = datetime.now(IST)

            for instrument_key, feed_data in feeds.items():
                if instrument_key not in self.stock_symbols:
                    continue

                symbol = self.stock_symbols[instrument_key]

                # Extract LTP
                ltp = None
                ohlc_list = []

                if isinstance(feed_data, dict):
                    # CRITICAL: Handle marketFF path (missing before)
                    if 'fullFeed' in feed_data:
                        full_feed = feed_data['fullFeed']
                        if isinstance(full_feed, dict) and 'marketFF' in full_feed:
                            market_ff = full_feed['marketFF']
                            if isinstance(market_ff, dict):
                                # Extract LTP for reversal first-tick capture
                                if 'ltpc' in market_ff:
                                    ltpc_data = market_ff['ltpc']
                                    if isinstance(ltpc_data, dict):
                                        ltp = ltpc_data.get('ltp')
                                
                                # Extract OHLC for continuation 1-min capture
                                if 'marketOHLC' in market_ff:
                                    market_ohlc = market_ff['marketOHLC']
                                    if isinstance(market_ohlc, dict) and 'ohlc' in market_ohlc:
                                        ohlc_list = market_ohlc['ohlc']

                if ltp is not None:
                    ltp = float(ltp)
                    # Removed tick printing for cleaner output

                    # Call tick handler if set
                    if hasattr(self, 'tick_handler'):
                        self.tick_handler(instrument_key, symbol, ltp, current_time, ohlc_list)

    def on_open(self):
        """WebSocket opened"""
        current_time = datetime.now(IST).strftime('%H:%M:%S')
        self.last_connection_time = datetime.now(IST)
        self.connection_attempts += 1

        # Only log attempt number for reconnections, not initial connection
        if self.connection_attempts > 1:
            print(f"WebSocket RECONNECTED at {current_time} (attempt #{self.connection_attempts})")
        else:
            print(f"WebSocket OPENED at {current_time}")

        self.connected = True

        # Wait a bit then subscribe
        import time
        time.sleep(1)

        try:
            # Subscribe only to active instruments (those not unsubscribed)
            active_list = list(self.active_instruments)
            self.streamer.subscribe(active_list, "full")
            print(f"Subscribed to {len(active_list)} active instruments in 'full' mode (LTP + OHLC) at {datetime.now(IST).strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Subscription error at {datetime.now(IST).strftime('%H:%M:%S')}: {e}")

    def on_error(self, error):
        """WebSocket error"""
        current_time = datetime.now(IST).strftime('%H:%M:%S')
        print(f"WebSocket ERROR at {current_time}: {error}")
        # Don't set connected=False here as connection might still be active
        if not self.reconnecting:
            self.reconnect()

    def on_close(self, *args):
        """WebSocket closed"""
        current_time = datetime.now(IST).strftime('%H:%M:%S')
        self.last_disconnection_time = datetime.now(IST)
        close_code = args[0] if args else "unknown"
        close_reason = args[1] if len(args) > 1 else "unknown"
        print(f"WebSocket CLOSED at {current_time} - Code: {close_code}, Reason: {close_reason}")
        self.connected = False
        
        # Only reconnect if this was NOT an intentional disconnection
        if not self.reconnecting and not self.intentional_disconnect:
            self.reconnect()
        else:
            print("Skipping reconnection - intentional disconnection or already reconnecting")

    def connect(self):
        """Connect to WebSocket using Market Data Feed endpoint with auto-redirect"""
        try:
            configuration = upstox_client.Configuration()
            configuration.access_token = self.access_token
            # Enable auto-redirect as recommended by Upstox experts
            configuration.redirect_uri = None  # Let API handle redirects

            # Use MarketDataStreamerV3 which handles auto-redirect internally
            self.streamer = upstox_client.MarketDataStreamerV3(
                upstox_client.ApiClient(configuration)
            )

            # Register callbacks
            self.streamer.on("open", self.on_open)
            self.streamer.on("message", self.on_message)
            self.streamer.on("error", self.on_error)
            self.streamer.on("close", self.on_close)

            print("Connecting to Market Data Feed...")
            self.streamer.connect()
            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def fetch_recent_data_rest(self, symbol, minutes_back=5):
        """Fetch recent data via REST API for data recovery during disconnects"""
        try:
            from src.utils.upstox_fetcher import upstox_fetcher

            # Get recent OHLC data
            end_date = datetime.now(IST).strftime('%Y-%m-%d')
            start_date = (datetime.now(IST) - timedelta(minutes=minutes_back)).strftime('%Y-%m-%d')

            df = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)

            if not df.empty and len(df) > 0:
                latest = df.iloc[-1]
                ltp = latest.get('close', 0)
                if ltp > 0:
                    print(f"REST recovery: {symbol} LTP ₹{ltp:.2f}")
                    # Call tick handler with recovered data
                    if hasattr(self, 'tick_handler'):
                        self.tick_handler(symbol, symbol, ltp, datetime.now(IST), [])
                    return True

            return False

        except Exception as e:
            print(f"REST data recovery failed: {e}")
            return False

    def run(self):
        """Run the streamer - maintain existing connection or establish new one"""
        # If already connected, just maintain the connection
        if self.connected and self.streamer:
            print("Connection active - monitoring for signals...")
            try:
                import time
                while self.running and self.connected:
                    time.sleep(1)

                if not self.running:
                    print("Stopped by user")
                else:
                    print("Connection lost - attempting reconnection...")
                    # If connection was lost, try to reconnect
                    return self._reconnect_with_retries()

            except KeyboardInterrupt:
                print("Stopped by user")
                return self._cleanup_connection()

        # Not connected - establish new connection
        return self._connect_with_retries()

    def _connect_with_retries(self):
        """Establish new connection with retries"""
        max_retries = 3
        retry_delay = 1  # Start with 1 second, exponential backoff

        for attempt in range(max_retries):
            try:
                current_time = datetime.now(IST).strftime('%H:%M:%S')
                print(f"Establishing connection (attempt {attempt + 1}/{max_retries}) at {current_time}")

                if not self.connect():
                    if attempt < max_retries - 1:
                        print(f"Retrying in {retry_delay} seconds...")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff: 1s, 2s, 4s
                        continue
                    else:
                        print("Max connection attempts reached")
                        return False

                # Connection successful - run the streaming loop
                try:
                    import time
                    while self.running and self.connected:
                        time.sleep(1)

                    # If we get here, either user stopped or connection was lost
                    if not self.running:
                        print("Stopped by user")
                    else:
                        print("Connection lost - per Upstox guidelines, not auto-reconnecting")

                except KeyboardInterrupt:
                    print("Stopped by user")
                    # Clean up and re-raise
                    if self.streamer:
                        try:
                            self.streamer.disconnect()
                            print("WebSocket disconnected")
                        except:
                            pass
                    raise  # Re-raise to let caller handle it

                # Clean disconnect
                if self.streamer:
                    try:
                        self.streamer.disconnect()
                    except:
                        pass

                return True

            except Exception as e:
                print(f"Connection error: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached - exiting")
                    return False

    def _reconnect_with_retries(self):
        """Reconnect with proper exponential backoff after connection loss"""
        if self.reconnecting:
            return False
        
        self.reconnecting = True
        attempt = 1
        
        while attempt <= self.max_reconnect_attempts and not self.connected:
            # Exponential backoff: 5, 10, 20, 40, 80 seconds
            wait_time = 5 * (2 ** (attempt - 1))
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            print(f"Reconnecting (attempt {attempt}/{self.max_reconnect_attempts}) at {current_time} - waiting {wait_time}s...")
            
            import time
            time.sleep(wait_time)
            
            try:
                if self.connect():
                    if self.connected:
                        print(f"Reconnection successful at {datetime.now(IST).strftime('%H:%M:%S')}")
                        break
            except Exception as e:
                print(f"Reconnect attempt {attempt} failed: {e}")
            
            attempt += 1
        
        self.reconnecting = False
        
        if not self.connected:
            print("Max reconnection attempts reached - stopping")
            return False
        
        return True

    def reconnect(self):
        """Attempt to reconnect with proper exponential backoff"""
        if self.reconnecting:
            return
        
        self.reconnecting = True
        attempt = 1
        
        while attempt <= self.max_reconnect_attempts and not self.connected:
            # Proper exponential backoff: 5, 10, 20, 40, 80 seconds
            wait_time = 5 * (2 ** (attempt - 1))
            current_time = datetime.now(IST).strftime('%H:%M:%S')
            print(f"Reconnecting (attempt {attempt}/{self.max_reconnect_attempts}) at {current_time} - waiting {wait_time}s...")
            
            import time
            time.sleep(wait_time)
            
            try:
                if self.connect():
                    if self.connected:
                        print(f"Reconnection successful at {datetime.now(IST).strftime('%H:%M:%S')}")
                        break
            except Exception as e:
                print(f"Reconnect attempt {attempt} failed: {e}")
            
            attempt += 1
        
        self.reconnecting = False
        
        if not self.connected:
            print("Max reconnection attempts reached - stopping")

    def unsubscribe(self, instrument_keys):
        """
        Unsubscribe from specific instruments and remove from active list
        
        Args:
            instrument_keys: List of instrument keys to unsubscribe from
        """
        try:
            # Remove from active instruments list so they won't be re-subscribed on reconnection
            for key in instrument_keys:
                if key in self.active_instruments:
                    self.active_instruments.remove(key)
            
            # Call Upstox unsubscribe if streamer is available
            if self.streamer:
                self.streamer.unsubscribe(instrument_keys)
            
            print(f"Unsubscribed from {len(instrument_keys)} instruments")
            print(f"Active instruments remaining: {len(self.active_instruments)}")
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            raise

    def disconnect(self):
        """Disconnect from WebSocket - intentional disconnection"""
        # Set flag to prevent unwanted reconnection
        self.intentional_disconnect = True
        
        if self.streamer:
            try:
                self.streamer.disconnect()
                print("WebSocket disconnected (intentional)")
            except:
                pass
        self.connected = False

    def _cleanup_connection(self):
        """Clean up WebSocket connection"""
        if self.streamer:
            try:
                self.streamer.disconnect()
                print("WebSocket disconnected")
            except:
                pass
            return True
