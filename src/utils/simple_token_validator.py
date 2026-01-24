#!/usr/bin/env python3
"""
Simple Token Validator for MA Stock Trader
Makes direct HTTP requests to Upstox API for token validation
No dependencies on UpstoxFetcher or SDK
"""

import json
import os
import logging
import requests
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SimpleTokenValidator:
    """Simple token validator that makes direct HTTP requests to Upstox API"""
    
    def __init__(self, config_file: str = 'upstox_config.json'):
        self.config_file = config_file
        self._config_manager = None
        self._initialize_config_manager()
    
    def _initialize_config_manager(self):
        """Initialize config manager for real-time token access"""
        try:
            from .token_config_manager import token_config_manager
            self._config_manager = token_config_manager
            logger.info("SimpleTokenValidator initialized with real-time config manager")
        except ImportError:
            logger.error("Could not import token_config_manager. Using fallback.")
            self._config_manager = None
    
    def _get_current_token(self) -> Optional[str]:
        """Get current token from config manager"""
        if self._config_manager:
            return self._config_manager.get_token()
        else:
            # Fallback to direct file reading
            try:
                if os.path.exists(self.config_file):
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                    return config.get('access_token')
            except Exception as e:
                logger.error(f"Failed to read token: {e}")
            return None
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate Upstox access token by testing LTP data access for hardcoded stocks
        Makes direct HTTP requests to Upstox API
        """
        try:
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

            # Test token by making direct HTTP requests to Upstox API
            for symbol in test_symbols[:3]:  # Test up to 3 stocks for speed
                try:
                    # Use direct HTTP request to Upstox LTP API
                    instrument_key = f"NSE_EQ:{symbol.upper()}"
                    url = f"https://api.upstox.com/v3/market-quote/ltp?instrument_key={instrument_key}"
                    headers = {
                        "Accept": "application/json",
                        "Authorization": f"Bearer {token}"
                    }

                    response = requests.get(url, headers=headers, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            # Check if we got valid LTP data
                            data_dict = data.get('data', {})
                            instrument_data = data_dict.get(instrument_key, {})
                            
                            if instrument_data and 'last_price' in instrument_data:
                                successful_tests += 1
                                test_results.append(f"OK {symbol}: LTP ₹{instrument_data['last_price']}")
                            else:
                                test_results.append(f"FAIL {symbol}: No LTP data")
                        else:
                            test_results.append(f"FAIL {symbol}: API error - {data.get('message', 'Unknown error')}")
                    else:
                        test_results.append(f"FAIL {symbol}: HTTP {response.status_code}")

                except requests.exceptions.Timeout:
                    test_results.append(f"FAIL {symbol}: Timeout")
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
    
    def get_current_token_status(self) -> Dict:
        """Get current token status from config file"""
        try:
            if self._config_manager:
                status = self._config_manager.get_status()
                return {
                    'token': status.get('masked_token'),
                    'exists': status.get('exists'),
                    'masked': status.get('masked_token'),
                    'is_valid': status.get('is_valid'),
                    'last_modified': status.get('last_modified'),
                    'has_api_key': status.get('has_api_key'),
                    'has_api_secret': status.get('has_api_secret')
                }
            else:
                # Fallback to direct file reading
                if os.path.exists(self.config_file):
                    with open(self.config_file, 'r') as f:
                        config = json.load(f)
                    token = config.get('access_token')
                    return {
                        'token': token,
                        'exists': bool(token),
                        'masked': f"{'*' * 10}...{token[-4:]}" if token else None,
                        'is_valid': bool(token and config.get('api_key') and config.get('api_secret')),
                        'last_modified': None,
                        'has_api_key': bool(config.get('api_key')),
                        'has_api_secret': bool(config.get('api_secret'))
                    }
                return {
                    'token': None,
                    'exists': False,
                    'masked': None,
                    'is_valid': False,
                    'last_modified': None,
                    'has_api_key': False,
                    'has_api_secret': False
                }
        except Exception as e:
            logger.error(f"Failed to read current token status: {e}")
            return {
                'token': None,
                'exists': False,
                'masked': None,
                'is_valid': False,
                'last_modified': None,
                'has_api_key': False,
                'has_api_secret': False
            }

# Global instance
simple_token_validator = SimpleTokenValidator()