#!/usr/bin/env python3
"""
Token Validator for MA Stock Trader
Handles Upstox access token validation without affecting live trading data fetching
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class TokenValidator:
    """Handles Upstox access token validation"""

    def __init__(self, config_file: str = 'upstox_config.json'):
        self.config_file = config_file

    def validate_token(self, token: str) -> Dict:
        """
        Validate Upstox access token by testing LTP data access for hardcoded stocks
        """
        try:
            # Update config with the token first
            self._update_token_in_config(token)

            # Hardcoded top 10 stocks that are unlikely to ever be delisted
            test_symbols = [
                'RELIANCE',    # Reliance Industries Limited
                'TCS',         # Tata Consultancy Services
                'HDFCBANK',    # HDFC Bank Limited
                'INFY',        # Infosys Limited
                'ICICIBANK',   # ICICI Bank Limited
                'HINDUNILVR',  # Hindustan Unilever Limited
                'ITC',         # ITC Limited
                'SBIN',        # State Bank of India
                'BHARTIARTL',  # Bharti Airtel Limited
                'BAJFINANCE'   # Bajaj Finance Limited
            ]

            successful_tests = 0
            test_results = []

            # Test token by getting LTP data for sample stocks
            for symbol in test_symbols[:3]:  # Test up to 3 stocks for speed
                try:
                    # Use the upstox_fetcher to get LTP data (it handles the API calls properly)
                    from src.utils.upstox_fetcher import upstox_fetcher

                    ltp_data = upstox_fetcher.get_ltp_data(symbol)

                    if ltp_data and 'ltp' in ltp_data:
                        successful_tests += 1
                        test_results.append(f"OK {symbol}: LTP ₹{ltp_data['ltp']}")
                    else:
                        test_results.append(f"FAIL {symbol}: No LTP data")

                except Exception as e:
                    test_results.append(f"FAIL {symbol}: {str(e)}")

            # Token is valid if we can get LTP for at least 1 stock
            if successful_tests > 0:
                return {
                    'valid': True,
                    'successful_tests': successful_tests,
                    'total_tests': len(test_symbols[:3]),
                    'test_results': test_results,
                    'message': f'Token validated successfully ({successful_tests}/{len(test_symbols[:3])} stocks)',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'valid': False,
                    'error': 'Could not retrieve LTP data for any test stocks',
                    'test_results': test_results
                }

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {
                'valid': False,
                'error': f'Token validation failed: {str(e)}'
            }

    def _get_instrument_key(self, symbol: str) -> str:
        """Get instrument key for symbol using proper Upstox format"""
        # Known instrument keys for major stocks (from Upstox master data)
        INSTRUMENT_KEYS = {
            'RELIANCE': 'NSE_EQ|INE002A01018',
            'TCS': 'NSE_EQ|INE467B01029',
            'HDFCBANK': 'NSE_EQ|INE040A01034',
            'INFY': 'NSE_EQ|INE009A01021',
            'ICICIBANK': 'NSE_EQ|INE090A01021',
            'HINDUNILVR': 'NSE_EQ|INE030A01027',
            'ITC': 'NSE_EQ|INE154A01025',
            'SBIN': 'NSE_EQ|INE062A01020',
            'BHARTIARTL': 'NSE_EQ|INE397D01024',
            'BAJFINANCE': 'NSE_EQ|INE296A01024'
        }

        return INSTRUMENT_KEYS.get(symbol.upper(), f"NSE_EQ|{symbol}")

    def _update_token_in_config(self, token: str):
        """Update access token in config file"""
        try:
            # Load existing config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

            # Update token - use 'access_token' for upstox_config.json compatibility
            config['access_token'] = token

            # Save config (only create directories if config file is in a subdirectory)
            config_dir = os.path.dirname(self.config_file)
            if config_dir:  # Only create directories if config file is in a subdirectory
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            logger.info("Access token updated in upstox_config.json")

        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            raise

    def get_current_token(self) -> Dict:
        """Get current access token from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                token = config.get('access_token')
                return {
                    'token': token,
                    'exists': bool(token),
                    'masked': f"{'*' * 10}...{token[-4:]}" if token else None
                }
            return {'token': None, 'exists': False, 'masked': None}
        except Exception as e:
            logger.error(f"Failed to read current token: {e}")
            return {'token': None, 'exists': False, 'masked': None}

# Global instance
token_validator = TokenValidator()
