#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Timing Module
Handles pre-market timing logic and coordination for continuation bot
"""

import logging
import time as time_module
from datetime import datetime, time
import pytz
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ContinuationTimingManager:
    """Manages timing coordination for continuation bot pre-market sequence"""
    
    def __init__(self, config):
        """
        Initialize with configuration
        
        Args:
            config: Configuration module with timing settings
        """
        self.config = config
        self.IST = pytz.timezone('Asia/Kolkata')
    
    def schedule_iep_fetch(self, symbols: List[str], iep_manager, monitor) -> bool:
        """
        Execute IEP fetch immediately (timing handled by caller)
        
        Args:
            symbols: List of continuation stock symbols
            iep_manager: PreMarketIEPManager instance
            monitor: StockMonitor instance
            
        Returns:
            True if IEP fetch completed successfully, False otherwise
        """
        logger.info("=== PRE-MARKET IEP FETCH SEQUENCE ===")
        
        # Execute IEP fetch immediately
        return self._execute_iep_fetch(symbols, iep_manager, monitor)
    
    def _execute_iep_fetch(self, symbols: List[str], iep_manager, monitor) -> bool:
        """
        Execute IEP fetch and coordinate gap validation
        
        Args:
            symbols: List of continuation stock symbols
            iep_manager: PreMarketIEPManager instance
            monitor: StockMonitor instance
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("=== PRE-MARKET IEP FETCH SEQUENCE ===")
        
        # 1. Fetch IEP for all continuation stocks
        logger.info(f"Fetching IEP for {len(symbols)} continuation stocks...")
        iep_prices = iep_manager.fetch_iep_batch(symbols)
        
        if not iep_prices:
            logger.error("No IEP prices fetched, continuing with fallback...")
            return False
        
        # 2. Set opening prices for all stocks
        logger.info("Setting opening prices from IEP...")
        for symbol, iep_price in iep_prices.items():
            # Find stock by symbol - check both instrument_key and symbol
            stock = None
            for s in monitor.stocks.values():
                if s.symbol == symbol:
                    stock = s
                    break
            
            if stock:
                stock.set_open_price(iep_price)
                logger.info(f"Set opening price for {symbol}: ₹{iep_price:.2f}")
            else:
                logger.warning(f"Stock not found for symbol: {symbol}")
        
        # 3. Run gap validation immediately
        logger.info("Running gap validation...")
        qualified_stocks = self._run_gap_validation(monitor, iep_prices)
        
        # 4. Update status display
        self._update_status_display(monitor, iep_prices, qualified_stocks)
        
        logger.info(f"Pre-market sequence completed: {len(qualified_stocks)} stocks qualified")
        return True
    
    def _run_gap_validation(self, monitor, iep_prices: Dict[str, float]) -> List:
        """
        Run gap validation for all stocks with IEP-based opening prices
        
        Args:
            monitor: StockMonitor instance
            iep_prices: Dictionary of symbol -> IEP price
            
        Returns:
            List of qualified stocks
        """
        qualified_stocks = []
        
        for stock in monitor.stocks.values():
            if stock.symbol in iep_prices:
                # Validate gap using IEP as opening price
                if hasattr(stock, 'validate_gap'):
                    stock.validate_gap()
                
                if stock.gap_validated:
                    qualified_stocks.append(stock)
                    logger.info(f"Gap validated for {stock.symbol}")
                else:
                    logger.info(f"Gap validation failed for {stock.symbol}")
        
        return qualified_stocks
    
    def _update_status_display(self, monitor, iep_prices: Dict[str, float], qualified_stocks: List):
        """
        Update status display with pre-market IEP information
        
        Args:
            monitor: StockMonitor instance
            iep_prices: Dictionary of symbol -> IEP price
            qualified_stocks: List of qualified stocks
        """
        logger.info("=== PRE-MARKET STATUS ===")
        
        for stock in monitor.stocks.values():
            symbol = stock.symbol
            iep_price = iep_prices.get(symbol, "No IEP")
            
            if stock.previous_close:
                gap_pct = ((iep_price - stock.previous_close) / stock.previous_close) * 100 if iep_price != "No IEP" else 0
                gap_status = f"Gap: {gap_pct:+.2f}%" if iep_price != "No IEP" else "No IEP"
            else:
                gap_status = "No prev close"
            
            gap_validated = "Gap validated" if stock.gap_validated else "Gap not validated"
            qualified = "QUALIFIED" if stock in qualified_stocks else "NOT QUALIFIED"
            
            logger.info(f"   {symbol}: IEP = {iep_price if iep_price != 'No IEP' else 'No IEP'} | {gap_status} | {gap_validated} | {qualified}")
    
    def wait_for_market_open(self) -> bool:
        """
        Wait for market open and log status
        
        Returns:
            True if market opened successfully, False if interrupted
        """
        market_open = self.config.MARKET_OPEN
        current_time = datetime.now(self.IST).time()
        
        if current_time >= market_open:
            logger.info("Already past market open time")
            return True
        
        market_datetime = datetime.combine(datetime.now(self.IST).date(), market_open)
        market_datetime = self.IST.localize(market_datetime)
        current_datetime = datetime.now(self.IST)
        wait_seconds = (market_datetime - current_datetime).total_seconds()
        
        if wait_seconds > 0:
            logger.info(f"Waiting {wait_seconds:.0f} seconds for market open...")
            time_module.sleep(wait_seconds)
        
        logger.info("MARKET OPEN! Starting live monitoring...")
        return True
    
    def get_current_time_info(self) -> Dict:
        """
        Get current time information for logging
        
        Returns:
            Dictionary with time information
        """
        current_time = datetime.now(self.IST).time()
        current_datetime = datetime.now(self.IST)
        
        return {
            'current_time': current_time,
            'current_datetime': current_datetime,
            'ist': self.IST,
            'prep_start': self.config.PREP_START,
            'market_open': self.config.MARKET_OPEN,
            'entry_time': self.config.ENTRY_TIME
        }