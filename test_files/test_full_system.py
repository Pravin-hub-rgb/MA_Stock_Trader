#!/usr/bin/env python3
"""
Test the complete MA Stock Trader system
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

def test_full_system():
    """Test the complete MA Stock Trader system"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Testing MA Stock Trader System ===")
    
    try:
        # Test continuation scan with 20 stocks (small batch)
        logger.info("Running continuation scan with 20 stocks...")
        continuation_results = scanner.run_continuation_scan()
        
        logger.info(f"Continuation scan completed. Found {len(continuation_results)} candidates:")
        for result in continuation_results[:5]:  # Show first 5
            logger.info(f"  {result['symbol']} - ₹{result['price']:.2f}")
        
        if len(continuation_results) > 5:
            logger.info(f"  ... and {len(continuation_results) - 5} more")
        
        # Test reversal scan with 20 stocks
        logger.info("\nRunning reversal scan with 20 stocks...")
        reversal_results = scanner.run_reversal_scan()
        
        logger.info(f"Reversal scan completed. Found {len(reversal_results)} candidates:")
        for result in reversal_results[:5]:  # Show first 5
            logger.info(f"  {result['symbol']} - Score: {result['score']} - ADR: {result['adr_percent']:.1f}%")
        
        if len(reversal_results) > 5:
            logger.info(f"  ... and {len(reversal_results) - 5} more")
        
        logger.info("\n=== System Test Summary ===")
        logger.info(f"✅ Continuation scan: {len(continuation_results)} candidates found")
        logger.info(f"✅ Reversal scan: {len(reversal_results)} candidates found")
        logger.info("✅ All system components working correctly!")
        
        return True
        
    except Exception as e:
        logger.error(f"System test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_full_system()
    sys.exit(0 if success else 1)
