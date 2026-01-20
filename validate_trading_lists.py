#!/usr/bin/env python3
"""
Trading Lists Validation Script
Validates continuation_list.txt and reversal_list.txt for live trading readiness
Checks Upstox instrument keys and LTP data retrieval
"""

import os
import sys
import logging
from typing import Dict, List, Tuple
from datetime import datetime
import pytz

# Add src to path for imports
sys.path.append('src')

from utils.upstox_fetcher import UpstoxFetcher

# Setup logging
logging.basicConfig(
    level=logging.CRITICAL,  # Suppress all errors/warnings from upstox_fetcher
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class TradingListValidator:
    """Validates trading lists for live trading readiness"""

    def __init__(self):
        self.upstox_fetcher = UpstoxFetcher()
        self.results = {
            'continuation': {},
            'reversal': {}
        }

    def read_trading_list(self, file_path: str) -> List[Tuple[str, str]]:
        """Read stock symbols from trading list file

        Returns:
            List of tuples: (display_symbol, clean_symbol)
            display_symbol: symbol as written in file (with -TREND_PERIOD suffixes)
            clean_symbol: symbol without suffixes for Upstox validation
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                # Split by comma and clean up
                raw_symbols = [s.strip() for s in content.split(',') if s.strip()]

                processed_symbols = []
                for raw_symbol in raw_symbols:
                    # Handle reversal list suffixes (-uNUMBER, -dNUMBER) or simple (-u, -d)
                    if '-' in raw_symbol:
                        # Split on the last '-' to handle formats like SYMBOL-u6, SYMBOL-d14
                        parts = raw_symbol.rsplit('-', 1)
                        if len(parts) == 2:
                            clean_symbol = parts[0]  # Everything before the last -
                            display_symbol = raw_symbol
                        else:
                            # Fallback for any edge cases
                            clean_symbol = raw_symbol
                            display_symbol = raw_symbol
                    else:
                        # Continuation list - no suffix
                        clean_symbol = raw_symbol
                        display_symbol = raw_symbol

                    processed_symbols.append((display_symbol, clean_symbol))

                return processed_symbols
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []

    def validate_stock(self, symbol: str) -> Tuple[bool, str]:
        """Validate a single stock - only Upstox checks"""
        try:
            # Get instrument key
            instrument_key = self.upstox_fetcher.get_instrument_key(symbol)
            if not instrument_key:
                return False, "No instrument key"

            # Get LTP data
            ltp_data = self.upstox_fetcher.get_ltp_data(symbol)
            if ltp_data and 'ltp' in ltp_data and ltp_data['ltp'] is not None:
                ltp = float(ltp_data['ltp'])
                cp = ltp_data.get('cp', 'N/A')
                return True, f"₹{ltp:.2f}"
            else:
                return False, "No LTP data"

        except Exception as e:
            return False, f"Error: {str(e)[:30]}..."

    def validate_list(self, list_name: str, file_path: str) -> List[Tuple[str, bool, str]]:
        """Validate all stocks in a trading list"""
        symbol_tuples = self.read_trading_list(file_path)
        if not symbol_tuples:
            return []

        results = []
        for display_symbol, clean_symbol in symbol_tuples:
            is_valid, price_info = self.validate_stock(clean_symbol)
            results.append((display_symbol, is_valid, price_info))

        return results

    def print_results(self):
        """Print final validation results"""
        print(f"\n{'='*60}")
        print("TRADING LISTS VALIDATION REPORT")
        print(f"{'='*60}")
        print(f"Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")

        # Continuation list
        continuation_results = self.validate_list('continuation', 'src/trading/continuation_list.txt')
        if continuation_results:
            print("CONTINUATION LIST:")
            valid_count = 0
            for symbol, is_valid, price in continuation_results:
                status = "✅" if is_valid else "❌"
                print(f"  {status} {symbol}: {price}")
                if is_valid:
                    valid_count += 1
            print(f"Valid: {valid_count}/{len(continuation_results)}\n")

        # Reversal list
        reversal_results = self.validate_list('reversal', 'src/trading/reversal_list.txt')
        if reversal_results:
            print("REVERSAL LIST:")
            valid_count = 0
            for symbol, is_valid, price in reversal_results:
                status = "✅" if is_valid else "❌"
                print(f"  {status} {symbol}: {price}")
                if is_valid:
                    valid_count += 1
            print(f"Valid: {valid_count}/{len(reversal_results)}\n")

        # Summary
        total_stocks = len(continuation_results) + len(reversal_results)
        total_valid = sum(1 for _, valid, _ in continuation_results if valid) + sum(1 for _, valid, _ in reversal_results if valid)

        print(f"{'='*60}")
        print(f"OVERALL SUMMARY: {total_valid}/{total_stocks} stocks valid ({(total_valid/total_stocks*100):.1f}%)")

        if total_valid == total_stocks:
            print("✅ ALL STOCKS READY FOR LIVE TRADING")
        else:
            print("⚠️  CHECK FAILED STOCKS ABOVE")

def main():
    """Main entry point"""
    validator = TradingListValidator()
    validator.print_results()

if __name__ == "__main__":
    main()
