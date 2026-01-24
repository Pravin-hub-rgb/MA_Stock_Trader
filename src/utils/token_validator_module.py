#!/usr/bin/env python3
"""
Dedicated Token Validator Module for MA Stock Trader
Independent token validation system with real-time config reloading
"""

import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TokenValidatorModule:
    """Dedicated token validation system with real-time config reloading"""
    
    def __init__(self, config_file: str = 'upstox_config.json'):
        self.config_file = config_file
        self._config_manager = None
        self._initialize_config_manager()
    
    def _initialize_config_manager(self):
        """Initialize config manager for real-time config access"""
        try:
            from .token_config_manager import token_config_manager
            self._config_manager = token_config_manager
            logger.info("Token validator initialized with real-time config manager")
        except ImportError:
            logger.error("Could not import token_config_manager. Using fallback.")
            self._config_manager = None
    
    def validate_token(self, token: str) -> Dict:
        """
        Validate Upstox access token by testing LTP data access for hardcoded stocks
        Always uses the latest token from config file
        """
        try:
            # Update config with the token first
            if self._config_manager:
                success = self._config_manager.update_token(token)
                if not success:
                    return {
                        'valid': False,
                        'error': 'Failed to update token in config file'
                    }
            
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
    
    def get_current_token_status(self) -> Dict:
        """Get current token status from config file"""
        try:
            if self._config_manager:
                status = self._config_manager.get_status()
                return {
                    'token': status.get('token'),  # Return real token
                    'exists': status.get('exists'),
                    'masked': status.get('masked_token'),  # Return masked token
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
    
    
    def update_token_in_config(self, token: str) -> Dict:
        """Update token in config file"""
        try:
            if self._config_manager:
                success = self._config_manager.update_token(token)
                if success:
                    return {
                        'success': True,
                        'message': 'Token updated successfully',
                        'status': self.get_current_token_status()
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to update token in config file'
                    }
            else:
                # Fallback to direct file update
                try:
                    config = {}
                    if os.path.exists(self.config_file):
                        with open(self.config_file, 'r') as f:
                            config = json.load(f)
                    
                    config['access_token'] = token
                    
                    with open(self.config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    logger.info("Access token updated in config file")
                    return {
                        'success': True,
                        'message': 'Token updated successfully',
                        'status': self.get_current_token_status()
                    }
                except Exception as e:
                    logger.error(f"Failed to update config: {e}")
                    return {
                        'success': False,
                        'message': f'Failed to update config: {str(e)}'
                    }
        except Exception as e:
            logger.error(f"Failed to update token: {e}")
            return {
                'success': False,
                'message': f'Failed to update token: {str(e)}'
            }

# Global instance
token_validator_module = TokenValidatorModule()