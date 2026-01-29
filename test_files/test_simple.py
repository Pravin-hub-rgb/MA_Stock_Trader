#!/usr/bin/env python3
"""
Simple test to verify the scanner works with a single stock
"""

import sys
import os
import logging
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.data_fetcher import data_fetcher
from src.scanner.scanner import scanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_single_stock():
    """Test with a single known stock"""
    logger = logging.getLogger(__name__)
    
    try:
        # Test with a known NSE stock
        symbol = "RELIANCE.NS"  # Reliance Industries (NSE stock)
        logger.info(f"Testing with {symbol}")
        
        # Get historical data
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today().replace(day=1)).strftime('%Y-%m-%d')  # This month
        
        logger.info(f"Fetching data from {start_date} to {end_date}")
        data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
        
        if data.empty:
            logger.error(f"No data found for {symbol}")
            return False
        
        logger.info(f"Fetched {len(data)} days of data")
        
        # Calculate technical indicators
        logger.info("Calculating technical indicators...")
        data = data_fetcher.calculate_technical_indicators(data)
        
        if data.empty:
            logger.error("Failed to calculate technical indicators")
            return False
        
        logger.info("Technical indicators calculated successfully")
        
        # Check latest data
        latest = data.iloc[-1]
        logger.info(f"Latest close: {latest['close']}")
        logger.info(f"Latest ADR: {latest['adr']}")
        logger.info(f"Latest ADR %: {latest['adr_percent']}")
        logger.info(f"Latest MA angle: {latest['ma_angle']}")
        
        # Test scanner with this stock
        logger.info("Testing scanner with this stock...")
        result = scanner._analyze_continuation_setup(symbol, date.today())
        
        if result:
            logger.info(f"Scanner result: {result}")
            return True
        else:
            logger.info("No scanner result (may be filtered out)")
            return True
            
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_single_stock()
    sys.exit(0 if success else 1)
