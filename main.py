#!/usr/bin/env python3
"""
MA Stock Trader - Main Application Entry Point
"""

import sys
import os
import logging
import argparse
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scanner.gui import ScannerGUI
from src.scanner.scanner import scanner
from src.utils.database import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/ma_trader.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_scanner_cli(scan_type: str, scan_date: str = None):
    """Run scanner from command line"""
    if scan_date:
        try:
            scan_date = date.fromisoformat(scan_date)
        except ValueError:
            logger.error("Invalid date format. Use YYYY-MM-DD format.")
            return False
    else:
        scan_date = date.today()
    
    logger.info(f"Running {scan_type} scan for {scan_date}")
    
    if scan_type.lower() == 'continuation':
        results = scanner.run_continuation_scan(scan_date)
    elif scan_type.lower() == 'reversal':
        results = scanner.run_reversal_scan(scan_date)
    else:
        logger.error(f"Invalid scan type: {scan_type}")
        return False
    
    logger.info(f"Found {len(results)} candidates")
    
    # Display results
    for i, result in enumerate(results[:10]):  # Show top 10
        print(f"{i+1}. {result['symbol']}: Score {result['score']}")
        print(f"   Notes: {result['notes']}")
        print()
    
    return True


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='MA Stock Trader')
    parser.add_argument('--mode', choices=['gui', 'cli'], default='gui',
                       help='Run mode: gui or cli')
    parser.add_argument('--scan-type', choices=['continuation', 'reversal'],
                       help='Scan type for CLI mode')
    parser.add_argument('--date', 
                       help='Scan date in YYYY-MM-DD format (default: today)')
    
    args = parser.parse_args()
    
    if args.mode == 'gui':
        # Run GUI application
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = ScannerGUI()
        window.show()
        sys.exit(app.exec())
    
    elif args.mode == 'cli':
        # Run CLI mode
        if not args.scan_type:
            parser.error("--scan-type is required for CLI mode")
        
        success = run_scanner_cli(args.scan_type, args.date)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
