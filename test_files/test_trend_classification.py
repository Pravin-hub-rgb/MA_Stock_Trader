#!/usr/bin/env python3
"""
Test script for debugging trend classification issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
import logging
from datetime import datetime
from src.scanner.reversal_analyzer import ReversalAnalyzer
from src.utils.database import db
from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_atherenerg_classification():
    """Test the trend classification for ATHERENERG"""
    try:
        # Initialize analyzer
        filter_engine = None  # We'll create a minimal one if needed
        reversal_params = {
            'decline_days': [3, 8],
            'min_decline_percent': 0.13
        }

        analyzer = ReversalAnalyzer(filter_engine, reversal_params)

        # Get data for ATHERENERG
        symbol = 'ATHERENERG'
        # Use cache manager to get data - load 40-50 days for proper MA calculation
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=50)
        data = cache_manager.get_data_for_date_range(symbol, start_date, end_date)

        if data is None or len(data) == 0:
            logger.error(f"No data found for {symbol}")
            return

        logger.info(f"Retrieved {len(data)} days of data for {symbol}")

        # Test the classification
        result = analyzer.analyze_reversal_setup(symbol, None, data)

        if result:
            logger.info(f"✅ {symbol} qualified as reversal candidate")
            logger.info(f"Period: {result['period']} days")
            logger.info(f"Red days: {result['red_days']}")
            logger.info(f"Green days: {result['green_days']}")
            logger.info(f"Decline: {result['decline_percent']*100:.2f}%")
            logger.info(f"Trend: {result['trend_context']}")

            # Debug the trend classification
            period = result['period']
            oldest_day_index = len(data) - period
            oldest_day_data = data.iloc[oldest_day_index]

            logger.info(f"\n🔍 Trend Classification Debug:")
            logger.info(f"Oldest day index: {oldest_day_index}")
            logger.info(f"Oldest day date: {oldest_day_data.name}")
            logger.info(f"Oldest day close: {oldest_day_data['close']}")

            # Calculate MA values
            ma_at_oldest = data['close'].rolling(20).mean().iloc[oldest_day_index]
            ma_5_days_earlier = data['close'].rolling(20).mean().iloc[oldest_day_index - 5]

            logger.info(f"MA_20 at oldest day: {ma_at_oldest:.2f}")
            logger.info(f"MA_20 5 days earlier: {ma_5_days_earlier:.2f}")
            logger.info(f"Comparison: {ma_at_oldest:.2f} > {ma_5_days_earlier:.2f} = {ma_at_oldest > ma_5_days_earlier}")

            # Show recent MA trend
            recent_ma = data['close'].rolling(20).mean().tail(10)
            logger.info(f"\n📈 Recent MA_20 trend (last 10 days):")
            for i, ma_val in enumerate(recent_ma):
                logger.info(f"  Day {i}: {ma_val:.2f}")

        else:
            logger.info(f"❌ {symbol} did not qualify as reversal candidate")

    except Exception as e:
        logger.error(f"Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()

def test_multiple_symbols():
    """Test trend classification on multiple symbols"""
    symbols_to_test = ['ATHERENERG', 'RELIANCE', 'TATAMOTORS', 'HDFCLIFE']

    for symbol in symbols_to_test:
        logger.info(f"\n{'='*50}")
        logger.info(f"Testing {symbol}")
        logger.info('='*50)

        try:
            # Initialize analyzer
            filter_engine = None
            reversal_params = {
                'decline_days': [3, 8],
                'min_decline_percent': 0.13
            }

            analyzer = ReversalAnalyzer(filter_engine, reversal_params)

            # Get data - load 40-50 days for proper MA calculation
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=50)
            data = cache_manager.get_data_for_date_range(symbol, start_date, end_date)

            if data is None or len(data) < 25:  # Need enough data for MA_20
                logger.warning(f"Not enough data for {symbol}")
                continue

            # Test classification
            result = analyzer.analyze_reversal_setup(symbol, None, data)

            if result:
                logger.info(f"✅ {symbol}: {result['trend_context']} - {result['decline_percent']*100:.2f}% decline over {result['period']} days")
            else:
                logger.info(f"❌ {symbol}: No reversal pattern found")

        except Exception as e:
            logger.error(f"Error with {symbol}: {e}")

def main():
    """Main test function"""
    logger.info("Starting trend classification testing...")
    logger.info("="*60)

    # Test specific case
    test_atherenerg_classification()

    # Test multiple symbols
    test_multiple_symbols()

    logger.info("\n" + "="*60)
    logger.info("Testing complete")

if __name__ == "__main__":
    main()