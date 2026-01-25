#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-Market IEP Module for Upstox
Handles Indicative Equilibrium Price (IEP) fetching for pre-market opening prices
"""

import logging
import time
from datetime import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PreMarketIEPManager:
    """Manages pre-market IEP fetching for multiple symbols"""
    
    def __init__(self, upstox_fetcher):
        """
        Initialize with UpstoxFetcher instance
        
        Args:
            upstox_fetcher: Instance of UpstoxFetcher for API calls
        """
        self.upstox_fetcher = upstox_fetcher
    
    def fetch_iep_batch(self, symbols: List[str]) -> Dict[str, float]:
        """
        Fetch IEP (Indicative Equilibrium Price) for multiple symbols at once
        
        Args:
            symbols: List of stock symbols to fetch IEP for
            
        Returns:
            Dictionary mapping symbol to IEP price
        """
        if not symbols:
            logger.warning("No symbols provided for IEP fetch")
            return {}
        
        logger.info(f"Fetching IEP for {len(symbols)} symbols: {symbols}")
        
        # Get instrument keys for all symbols
        keys = []
        symbol_map = {}
        for symbol in symbols:
            key = self.upstox_fetcher.get_instrument_key(symbol)
            if key:
                keys.append(key)
                symbol_map[key] = symbol
        
        if not keys:
            logger.error("No valid instrument keys found for IEP fetch")
            return {}
        
        # Make batch API call for IEP
        iep_prices = self._fetch_iep_from_api(keys, symbol_map)
        
        logger.info(f"Successfully fetched IEP for {len(iep_prices)} symbols")
        return iep_prices
    
    def _fetch_iep_from_api(self, instrument_keys: List[str], symbol_map: Dict[str, str]) -> Dict[str, float]:
        """
        Fetch IEP data from Upstox API using batch request
        
        Args:
            instrument_keys: List of instrument keys
            symbol_map: Mapping from instrument key to symbol
            
        Returns:
            Dictionary mapping symbol to IEP price
        """
        iep_dict = {}
        
        try:
            # Use the same endpoint as get_opening_price but for batch
            url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={','.join(instrument_keys)}"
            headers = {
                "Accept": "application/json",
                "Api-Version": "2.0",
                "Authorization": f"Bearer {self.upstox_fetcher.access_token}"
            }
            
            # Use requests directly like the existing get_opening_price method
            import requests
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Handle encoding properly to avoid charmap issues
                try:
                    response_data = response.json()
                except UnicodeDecodeError:
                    # Fallback: decode with utf-8 explicitly
                    response_data = response.content.decode('utf-8', errors='ignore')
                    import json
                    response_data = json.loads(response_data)
                
                if response_data.get('status') == 'success':
                    data = response_data.get('data', {})
                    
                    for response_key, quote_data in data.items():
                        # Try to get symbol from response data first
                        symbol = quote_data.get('symbol')
                        
                        # If not found, try to map from our symbol_map using response_key
                        if not symbol:
                            symbol = symbol_map.get(response_key)
                        
                        # If still not found, try to extract from response_key (NSE_EQ:SYMBOL format)
                        if not symbol and ':' in response_key:
                            symbol = response_key.split(':')[1]
                        
                        if symbol:
                            # Use last_price for current price (IEP during pre-market)
                            iep = quote_data.get('last_price') or quote_data.get('open')
                            if iep:
                                iep_dict[symbol] = float(iep)
                                logger.info(f"IEP for {symbol}: Rs{iep:.2f}")
                            else:
                                logger.warning(f"No IEP data found for {symbol}")
                else:
                    logger.error(f"API response error: {response_data}")
            else:
                logger.error(f"API request failed with status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching IEP from API: {e}")
            # Fallback: try individual fetching for each symbol
            logger.info("Falling back to individual symbol fetching...")
            for symbol in symbol_map.values():
                try:
                    price = self.get_iep_for_symbol(symbol)
                    if price:
                        iep_dict[symbol] = price
                        logger.info(f"IEP for {symbol} (individual): Rs{price:.2f}")
                except Exception as fallback_error:
                    logger.error(f"Individual fetch failed for {symbol}: {fallback_error}")
        
        return iep_dict
    
    def get_iep_for_symbol(self, symbol: str) -> Optional[float]:
        """
        Fetch IEP for a single symbol (fallback method)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            IEP price or None if not found
        """
        try:
            instrument_key = self.upstox_fetcher.get_instrument_key(symbol)
            if not instrument_key:
                logger.error(f"No instrument key found for {symbol}")
                return None
            
            # Use existing get_opening_price method but ensure it's called during pre-market
            return self.upstox_fetcher.get_opening_price(symbol)
            
        except Exception as e:
            logger.error(f"Error fetching IEP for {symbol}: {e}")
            return None
    
