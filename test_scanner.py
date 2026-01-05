#!/usr/bin/env python3
"""
Test script for MA Stock Trader Scanner
"""

import sys
import os
import logging
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scanner.scanner import scanner
from src.utils.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_scanner():
    """Test the scanner functionality"""
    logger = logging.getLogger(__name__)
    
    logger.info("Starting scanner test...")
    
    try:
        # Test 1: Run continuation scan
        logger.info("Running continuation scan...")
        continuation_results = scanner.run_continuation_scan(date.today())
        
        logger.info(f"Continuation scan completed. Found {len(continuation_results)} candidates")
        for result in continuation_results[:5]:  # Show top 5
            logger.info(f"  {result['symbol']}: Score {result['score']}, Notes: {result['notes']}")
        
        # Test 2: Run reversal scan
        logger.info("Running reversal scan...")
        reversal_results = scanner.run_reversal_scan(date.today())
        
        logger.info(f"Reversal scan completed. Found {len(reversal_results)} candidates")
        for result in reversal_results[:5]:  # Show top 5
            logger.info(f"  {result['symbol']}: Score {result['score']}, Notes: {result['notes']}")
        
        # Test 3: Check database
        logger.info("Checking database...")
        scan_results = db.get_scan_results(days=1)
        logger.info(f"Database contains {len(scan_results)} scan results from today")
        
        # Test 4: Create watchlists
        logger.info("Creating watchlists...")
        
        # Create continuation candidates watchlist
        continuation_wl_id = db.create_watchlist("Continuation Candidates", "continuation_candidates")
        for result in continuation_results[:10]:  # Add top 10
            db.add_to_watchlist(
                continuation_wl_id, 
                result['stock_id'], 
                scan_source="continuation_scan",
                manual_notes=f"Score: {result['score']}"
            )
        
        # Create reversal candidates watchlist
        reversal_wl_id = db.create_watchlist("Reversal Candidates", "reversal_candidates")
        for result in reversal_results[:10]:  # Add top 10
            db.add_to_watchlist(
                reversal_wl_id, 
                result['stock_id'], 
                scan_source="reversal_scan",
                manual_notes=f"Score: {result['score']}"
            )
        
        # Create next day trades watchlist
        next_day_wl_id = db.create_watchlist("Next Day Trades", "next_day_trades")
        
        logger.info("Watchlists created successfully")
        
        # Test 5: Get watchlists
        watchlists = db.get_watchlists()
        logger.info(f"Created {len(watchlists)} watchlists")
        for wl in watchlists:
            logger.info(f"  {wl['name']} ({wl['type']}): {wl['id']}")
        
        logger.info("Scanner test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Scanner test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_scanner()
    sys.exit(0 if success else 1)
