#!/usr/bin/env python3
"""
Test with multiple NSE stocks to verify the fix works broadly
"""

import sys
import os
import logging
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.data_fetcher import data_fetcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_multiple_stocks():
    """Test with multiple NSE stocks"""
    logger = logging.getLogger(__name__)
    
    # Test with a few known NSE stocks
    test_symbols = [
        "RELIANCE.NS",
        "TCS.NS", 
        "INFY.NS",
        "HDFCBANK.NS",
        "ITC.NS"
    ]
    
    logger.info(f"Testing {len(test_symbols)} NSE stocks")
    
    for symbol in test_symbols:
        logger.info(f"\n=== Testing {symbol} ===")
        
        try:
            # Get historical data
            end_date = date.today().strftime('%Y-%m-%d')
            start_date = (date.today().replace(month=1, day=1)).strftime('%Y-%m-%d')
            
            logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
            data = data_fetcher.fetch_historical_data(symbol, start_date, end_date)
            
            if data.empty:
                logger.error(f"No data found for {symbol}")
                continue
            
            logger.info(f"✅ Successfully fetched {len(data)} days of data")
            
            # Calculate technical indicators
            data_with_indicators = data_fetcher.calculate_technical_indicators(data)
            
            if data_with_indicators.empty:
                logger.error(f"Failed to calculate indicators for {symbol}")
                continue
            
            logger.info("✅ Technical indicators calculated successfully")
            
            # Show latest data
            latest = data_with_indicators.iloc[-1]
            logger.info(f"Latest close: {latest['close']:.2f}")
            logger.info(f"Latest volume: {latest['volume']:,}")
            logger.info(f"Latest VWAP: {latest['vwap']:.2f}")
            
        except Exception as e:
            logger.error(f"Error testing {symbol}: {e}")
    
    logger.info(f"\n=== Test completed ===")
    logger.info("If you see ✅ marks above, the data fetching is working correctly!")

if __name__ == "__main__":
    test_multiple_stocks()
