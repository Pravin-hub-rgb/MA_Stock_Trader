#!/usr/bin/env python3
"""
Test the simplified continuation scan with just 5 target stocks
"""

import sys
import os
import logging
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scanner.scanner import scanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_continuation_simple():
    """Test continuation scan with just 5 target stocks"""
    logger = logging.getLogger(__name__)
    
    # Test with just our 5 target stocks
    test_symbols = [
        "RELIANCE.NS",
        "TCS.NS", 
        "INFY.NS",
        "HDFCBANK.NS",
        "ITC.NS"
    ]
    
    logger.info(f"Testing continuation scan with {len(test_symbols)} target stocks")
    
    try:
        # Run continuation scan manually for each stock
        qualified_stocks = []
        
        for symbol in test_symbols:
            logger.info(f"Analyzing {symbol}...")
            
            try:
                result = scanner._analyze_continuation_setup(symbol, date.today())
                
                if result:
                    qualified_stocks.append(result)
                    logger.info(f"✅ {symbol} - ₹{result['price']:.2f}")
                else:
                    logger.info(f"❌ {symbol} - Did not qualify")
                    
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        # Display results
        logger.info(f"\n=== RESULTS ===")
        if qualified_stocks:
            logger.info(f"Found {len(qualified_stocks)} qualified stocks:")
            for stock in qualified_stocks:
                logger.info(f"  {stock['symbol']} - ₹{stock['price']:.2f}")
        else:
            logger.info("No stocks qualified the base filters")
            
        logger.info("✅ Continuation scan test completed!")
        
    except Exception as e:
        logger.error(f"Continuation scan test failed: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_continuation_simple()
    sys.exit(0 if success else 1)
