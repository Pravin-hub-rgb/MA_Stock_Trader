#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Subscription Manager Module

Handles dynamic subscription management for continuation trading bot.
Implements first-come-first-serve logic where stocks are unsubscribed
after 2 positions are filled.
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ContinuationSubscriptionManager:
    """Manages dynamic subscription for continuation trading"""
    
    def __init__(self, data_streamer, monitor):
        """
        Initialize subscription manager
        
        Args:
            data_streamer: SimpleStockStreamer instance
            monitor: StockMonitor instance
        """
        self.data_streamer = data_streamer
        self.monitor = monitor
        self.subscribed_keys = set()
    
    def subscribe_all(self, instrument_keys: List[str]):
        """Subscribe to all continuation stocks initially"""
        if not instrument_keys:
            return
        
        logger.info(f"Subscribing to {len(instrument_keys)} continuation stocks")
        
        # Subscribe to all stocks initially - the data streamer handles subscription in on_open()
        # We just track which stocks we want to be subscribed to
        for key in instrument_keys:
            if key not in self.subscribed_keys:
                self.subscribed_keys.add(key)
                logger.info(f"Marked {key} for subscription (will be subscribed when connected)")
    
    def unsubscribe_remaining_after_positions_filled(self):
        """
        Unsubscribe remaining stocks after 2 positions are filled
        Implements first-come-first-serve logic
        """
        # Count entered positions
        entered_positions = 0
        subscribed_stocks = []
        
        for stock in self.monitor.stocks.values():
            if stock.instrument_key in self.subscribed_keys:
                subscribed_stocks.append(stock)
                if stock.entered:
                    entered_positions += 1
        
        # If we have 2 entered positions and more than 2 subscribed stocks,
        # unsubscribe the remaining ones
        if entered_positions >= 2 and len(subscribed_stocks) > 2:
            remaining_stocks = [stock for stock in subscribed_stocks if not stock.entered]
            
            if remaining_stocks:
                remaining_keys = [stock.instrument_key for stock in remaining_stocks]
                logger.info(f"\n=== UNSUBSCRIBING REMAINING STOCKS AFTER 2 POSITIONS FILLED ===")
                logger.info(f"Unsubscribing {len(remaining_stocks)} remaining stocks: {[s.symbol for s in remaining_stocks]}")
                
                self.safe_unsubscribe(remaining_keys, "positions_filled")
                self.mark_stocks_unsubscribed(remaining_keys)
                
                self.log_subscription_status()
    
    def safe_unsubscribe(self, instrument_keys: List[str], reason: str = "manual"):
        """
        Safely unsubscribe from stocks with error handling
        
        Args:
            instrument_keys: List of instrument keys to unsubscribe
            reason: Reason for unsubscription (for logging)
        """
        if not instrument_keys:
            return
        
        try:
            # Unsubscribe from all keys at once
            self.data_streamer.unsubscribe(instrument_keys)
            
            # Remove from our tracking set
            for key in instrument_keys:
                if key in self.subscribed_keys:
                    self.subscribed_keys.discard(key)
                    logger.info(f"Unsubscribed from {key} ({reason})")
                    
        except Exception as e:
            logger.error(f"Error unsubscribing from {len(instrument_keys)} instruments: {e}")
    
    def mark_stocks_unsubscribed(self, instrument_keys: List[str]):
        """
        Mark stocks as unsubscribed in the monitor
        
        Args:
            instrument_keys: List of instrument keys to mark as unsubscribed
        """
        for key in instrument_keys:
            stock = self.monitor.stocks.get(key)
            if stock:
                stock.is_active = False
                stock.rejection_reason = "Unsubscribed after 2 positions filled"
                logger.info(f"Marked {stock.symbol} as unsubscribed")
    
    def log_subscription_status(self):
        """Log current subscription status"""
        logger.info("\n=== SUBSCRIPTION STATUS ===")
        
        total_stocks = len(self.monitor.stocks)
        subscribed_count = len(self.subscribed_keys)
        unsubscribed_count = total_stocks - subscribed_count
        
        logger.info(f"Total stocks: {total_stocks}")
        logger.info(f"Subscribed: {subscribed_count}")
        logger.info(f"Unsubscribed: {unsubscribed_count}")
        
        # Log by state
        state_counts = {}
        for stock in self.monitor.stocks.values():
            state = "subscribed" if stock.instrument_key in self.subscribed_keys else "unsubscribed"
            if state not in state_counts:
                state_counts[state] = 0
            state_counts[state] += 1
            
            # Log individual stock status
            status = "SUBSCRIBED" if stock.instrument_key in self.subscribed_keys else "UNSUBSCRIBED"
            logger.info(f"   {stock.symbol}: {status}")
        
        logger.info("=== END SUBSCRIPTION STATUS ===")
    
    def cleanup_all(self):
        """Clean up all subscriptions at end of day"""
        logger.info("\n=== CLEANUP: UNSUBSCRIBING ALL STOCKS ===")
        
        if self.subscribed_keys:
            self.safe_unsubscribe(list(self.subscribed_keys), "end_of_day")
            self.mark_stocks_unsubscribed(list(self.subscribed_keys))
            logger.info(f"Unsubscribed {len(self.subscribed_keys)} stocks at end of day")
            self.subscribed_keys.clear()
        else:
            logger.info("No stocks to unsubscribe")
        
        self.log_subscription_status()