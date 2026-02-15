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

    def unsubscribe_gap_and_vah_rejected(self):
        """
        Phase 1: Unsubscribe stocks that failed gap validation or VAH validation
        Called immediately after gap validation at 9:14:30
        
        Follows reversal bot pattern: Fully unsubscribe rejected stocks
        so they disappear from monitoring completely
        """
        gap_vah_rejected = []
        gap_failed_stocks = []
        vah_failed_stocks = []
        
        for stock in self.monitor.stocks.values():
            if stock.instrument_key in self.subscribed_keys:
                # Check if stock failed gap validation
                gap_failed = not stock.gap_validated
                
                # Check if stock failed VAH validation (continuation only)
                vah_failed = False
                if stock.situation == 'continuation':
                    # Check if stock has opening price and VAH price, and if opening is below VAH
                    if (hasattr(stock, 'open_price') and stock.open_price is not None and 
                        hasattr(stock, 'vah_price') and stock.vah_price is not None):
                        if stock.open_price < stock.vah_price:
                            vah_failed = True
                
                if gap_failed or vah_failed:
                    gap_vah_rejected.append(stock)
                    if gap_failed:
                        gap_failed_stocks.append(stock)
                    if vah_failed:
                        vah_failed_stocks.append(stock)
        
        if gap_vah_rejected:
            rejected_keys = [stock.instrument_key for stock in gap_vah_rejected]
            print(f"\n=== PHASE 1: UNSUBSCRIBING GAP+VAH REJECTED STOCKS ===")
            print(f"Unsubscribing {len(gap_vah_rejected)} stocks: {[s.symbol for s in gap_vah_rejected]}")
            
            # Log individual stock unsubscriptions with detailed reasons
            print(f"\nSTOCKS BEING UNSUBSCRIBED:")
            for stock in gap_vah_rejected:
                reason = ""
                if not stock.gap_validated:
                    reason = "Gap validation failed"
                elif (stock.situation == 'continuation' and 
                      hasattr(stock, 'open_price') and stock.open_price is not None and 
                      hasattr(stock, 'vah_price') and stock.vah_price is not None and
                      stock.open_price < stock.vah_price):
                    reason = f"VAH validation failed (Opening price {stock.open_price:.2f} < VAH {stock.vah_price:.2f})"
                
                print(f"   UNSUBSCRIBING {stock.symbol} - Reason: {reason}")
            
            # Log breakdown by rejection type
            if gap_failed_stocks:
                print(f"\nGAP VALIDATION FAILED ({len(gap_failed_stocks)} stocks):")
                for stock in gap_failed_stocks:
                    print(f"   - {stock.symbol}")
            
            if vah_failed_stocks:
                print(f"\nVAH VALIDATION FAILED ({len(vah_failed_stocks)} stocks):")
                for stock in vah_failed_stocks:
                    print(f"   - {stock.symbol} (Open: {stock.open_price:.2f}, VAH: {stock.vah_price:.2f})")
            
            # Show remaining subscribed stocks
            remaining_subscribed = [stock for stock in self.monitor.stocks.values() 
                                  if stock.instrument_key in self.subscribed_keys and stock not in gap_vah_rejected]
            if remaining_subscribed:
                print(f"\nSTOCKS REMAINING SUBSCRIBED ({len(remaining_subscribed)} stocks):")
                for stock in remaining_subscribed:
                    print(f"   - {stock.symbol}")
            else:
                print(f"\nNO STOCKS REMAINING SUBSCRIBED - All stocks rejected")
            
            # Follow reversal bot pattern: Fully unsubscribe rejected stocks
            self.safe_unsubscribe(rejected_keys, "gap_vah_rejected")
            self.mark_stocks_unsubscribed(rejected_keys)
            
            self.log_subscription_status()

    def unsubscribe_low_and_volume_failed(self):
        """
        Phase 2: Unsubscribe stocks that failed low violation check or volume validation
        Called at 9:20 after all validations are complete
        """
        low_volume_failed = []
        
        for stock in self.monitor.stocks.values():
            if stock.instrument_key in self.subscribed_keys:
                # Check if stock failed low violation check
                low_failed = stock.low_violation_checked and not stock.is_active
                
                # Check if stock failed volume validation (continuation only)
                volume_failed = False
                if stock.situation == 'continuation':
                    volume_failed = stock.volume_validated and not stock.is_active
                
                if low_failed or volume_failed:
                    low_volume_failed.append(stock)
        
        if low_volume_failed:
            failed_keys = [stock.instrument_key for stock in low_volume_failed]
            logger.info(f"\n=== PHASE 2: UNSUBSCRIBING LOW+VOLUME FAILED STOCKS ===")
            logger.info(f"Unsubscribing {len(low_volume_failed)} stocks: {[s.symbol for s in low_volume_failed]}")
            
            self.safe_unsubscribe(failed_keys, "low_volume_failed")
            self.mark_stocks_unsubscribed(failed_keys)
            
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
                stock.is_subscribed = False  # CRITICAL FIX: Set is_subscribed to False
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