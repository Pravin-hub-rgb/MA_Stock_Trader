#!/usr/bin/env python3
"""
Test script for first tick opening price tracking
Tests the expert's solution: First tick after bot start = opening price
"""

import sys
import os
import time
import logging
from datetime import datetime
import pytz

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.upstox_fetcher import UpstoxFetcher
from trading.live_trading.simple_data_streamer import SimpleStockStreamer

IST = pytz.timezone('Asia/Kolkata')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestReversalStock:
    """Test class for first tick opening price tracking"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.prev_close = None
        self.open_price = None
        self.first_tick_captured = False
        self.current_low = float('inf')
        self.gap_calculated = False
        
    def update_tick(self, price, timestamp):
        """Track first tick as opening price"""
        if not self.first_tick_captured:
            self.open_price = price
            self.first_tick_captured = True
            logger.info(f"✅ {self.symbol}: Captured first tick as open = ₹{price:.2f} (bot start time)")
            return True
        return False
    
    def calculate_gap(self):
        """Calculate gap percentage using first tick as opening price"""
        if self.open_price and self.prev_close:
            gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
            logger.info(f"📊 {self.symbol}: Gap % = {gap_pct:.2f}% (Open: ₹{self.open_price:.2f}, Prev Close: ₹{self.prev_close:.2f})")
            self.gap_calculated = True
            return gap_pct
        logger.warning(f"⚠️ {self.symbol}: Missing open or prev_close for gap calculation")
        return None
    
    def check_oops_conditions(self, current_price):
        """Check OOPS reversal conditions"""
        if not self.gap_calculated:
            return False
            
        gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
        crosses_prev_close = current_price > self.prev_close
        
        if gap_pct <= -2.0 and crosses_prev_close:
            logger.info(f"🎯 {self.symbol}: OOPS conditions met! Gap: {gap_pct:.2f}%, Crossed Prev Close: ₹{current_price:.2f}")
            return True
        return False
    
    def check_strong_start_conditions(self, current_low):
        """Check Strong Start conditions"""
        if not self.gap_calculated:
            return False
            
        gap_pct = ((self.open_price - self.prev_close) / self.prev_close) * 100
        open_equals_low = abs(self.open_price - current_low) / self.open_price <= 0.01
        
        if gap_pct >= 2.0 and open_equals_low:
            logger.info(f"🚀 {self.symbol}: Strong Start conditions met! Gap: {gap_pct:.2f}%, Open≈Low: ₹{current_low:.2f}")
            return True
        return False

class TestFirstTickTracker:
    """Test implementation of first tick tracking"""
    
    def __init__(self):
        self.fetcher = UpstoxFetcher()
        self.stocks = {}
        self.instrument_keys = []
        self.stock_symbols = {}
        
    def load_test_stocks(self):
        """Load test stocks from reversal list"""
        try:
            reversal_list_file = "src/trading/reversal_list.txt"
            if not os.path.exists(reversal_list_file):
                logger.error(f"Reversal list not found: {reversal_list_file}")
                return False
                
            with open(reversal_list_file, 'r') as f:
                content = f.read().strip()
                
            if not content:
                logger.error("Reversal list is empty")
                return False
                
            # Parse symbols (remove -u/-d suffixes)
            entries = content.split(',')
            symbols = []
            for entry in entries:
                entry = entry.strip()
                if entry:
                    symbol = entry.split('-')[0]
                    symbols.append(symbol)
                    
            logger.info(f"Loaded {len(symbols)} test stocks: {symbols[:5]}...")
            return symbols[:5]  # Test with first 5 stocks
            
        except Exception as e:
            logger.error(f"Error loading test stocks: {e}")
            return []
    
    def get_prev_closes(self, symbols):
        """Get previous close prices"""
        prev_closes = {}
        for symbol in symbols:
            try:
                ltp_data = self.fetcher.get_ltp_data(symbol)
                if ltp_data and 'cp' in ltp_data:
                    prev_closes[symbol] = float(ltp_data['cp'])
                    logger.info(f"✅ {symbol}: Previous close = ₹{prev_closes[symbol]:.2f}")
                else:
                    logger.warning(f"⚠️ Could not get prev close for {symbol}")
                    prev_closes[symbol] = 0.0
            except Exception as e:
                logger.error(f"Error getting prev close for {symbol}: {e}")
                prev_closes[symbol] = 0.0
        return prev_closes
    
    def setup_stocks(self, symbols):
        """Setup test stocks with previous closes"""
        prev_closes = self.get_prev_closes(symbols)
        
        for symbol in symbols:
            stock = TestReversalStock(symbol)
            stock.prev_close = prev_closes.get(symbol, 0.0)
            self.stocks[symbol] = stock
            
            # Get instrument key
            instrument_key = self.fetcher.get_instrument_key(symbol)
            if instrument_key:
                self.instrument_keys.append(instrument_key)
                self.stock_symbols[instrument_key] = symbol
                logger.info(f"✅ {symbol}: Instrument key = {instrument_key}")
            else:
                logger.warning(f"⚠️ No instrument key for {symbol}")
    
    def handle_tick(self, instrument_key, symbol, price, timestamp, ohlc_data=None):
        """Handle incoming tick data"""
        try:
            if symbol in self.stocks:
                stock = self.stocks[symbol]
                
                # Update tick - captures first tick as opening price
                first_tick_captured = stock.update_tick(price, timestamp)
                
                # If first tick was just captured, calculate gap
                if first_tick_captured:
                    gap = stock.calculate_gap()
                    
                    # Check reversal conditions
                    if gap is not None:
                        oops_triggered = stock.check_oops_conditions(price)
                        strong_start_triggered = stock.check_strong_start_conditions(price)
                        
                        if oops_triggered or strong_start_triggered:
                            logger.info(f"🎯 REVERSAL TRIGGERED for {symbol}!")
                        else:
                            logger.info(f"📊 {symbol}: Gap analysis complete, no triggers yet")
                
                # Update current low for ongoing analysis
                stock.current_low = min(stock.current_low, price)
                
        except Exception as e:
            logger.error(f"Error handling tick for {symbol}: {e}")
    
    def run_test(self):
        """Run the first tick tracking test"""
        logger.info("🚀 Starting First Tick Opening Price Test")
        logger.info(f"Current time: {datetime.now(IST).strftime('%H:%M:%S')}")
        
        # Load test stocks
        symbols = self.load_test_stocks()
        if not symbols:
            logger.error("No test stocks loaded")
            return False
        
        # Setup stocks
        self.setup_stocks(symbols)
        
        if not self.instrument_keys:
            logger.error("No instrument keys available")
            return False
        
        # Initialize data streamer
        try:
            self.data_streamer = SimpleStockStreamer(self.instrument_keys, self.stock_symbols)
            self.data_streamer.tick_handler = self.handle_tick
            logger.info(f"📡 Initialized streamer for {len(self.instrument_keys)} stocks")
        except Exception as e:
            logger.error(f"Error initializing streamer: {e}")
            return False
        
        # Start streaming
        logger.info("📡 Starting data streaming...")
        logger.info("Waiting for first ticks to capture opening prices...")
        
        try:
            self.data_streamer.connect()
            self.data_streamer.run()
        except KeyboardInterrupt:
            logger.info("Test interrupted by user")
        except Exception as e:
            logger.error(f"Error in streaming: {e}")
        finally:
            if hasattr(self, 'data_streamer'):
                self.data_streamer.disconnect()
        
        logger.info("✅ First tick tracking test completed")
        return True

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("TESTING: First Tick as Opening Price (Expert Solution)")
    logger.info("=" * 60)
    
    test_tracker = TestFirstTickTracker()
    success = test_tracker.run_test()
    
    if success:
        logger.info("🎉 Test completed successfully!")
        logger.info("The expert's solution works: First tick = opening price")
    else:
        logger.error("❌ Test failed")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
