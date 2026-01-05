#!/usr/bin/env python3
"""
Test the scanner with a small batch of NSE stocks
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

def test_scanner_small():
    """Test scanner with a small batch of stocks"""
    logger = logging.getLogger(__name__)
    
    # Test with just 5 stocks to start
    test_symbols = [
        "RELIANCE.NS",
        "TCS.NS", 
        "INFY.NS",
        "HDFCBANK.NS",
        "ITC.NS"
    ]
    
    logger.info(f"Testing scanner with {len(test_symbols)} stocks")
    
    try:
        # Run continuation scan
        logger.info("Running continuation scan...")
        candidates = scanner.run_continuation_scan(date.today())
        
        if candidates:
            logger.info(f"🎉 Found {len(candidates)} continuation candidates!")
            for candidate in candidates:
                logger.info(f"  - {candidate['symbol']}: {candidate['notes']}")
        else:
            logger.info("No continuation candidates found (this is normal)")
        
        # Run reversal scan
        logger.info("Running reversal scan...")
        reversal_candidates = scanner.run_reversal_scan(date.today())
        
        if reversal_candidates:
            logger.info(f"🎉 Found {len(reversal_candidates)} reversal candidates!")
            for candidate in reversal_candidates:
                logger.info(f"  - {candidate['symbol']}: {candidate['notes']}")
        else:
            logger.info("No reversal candidates found (this is normal)")
            
        logger.info("✅ Scanner test completed successfully!")
        
    except Exception as e:
        logger.error(f"Scanner test failed: {e}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    success = test_scanner_small()
    sys.exit(0 if success else 1)
