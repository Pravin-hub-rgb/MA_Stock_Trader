#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Tick Processor Module

Implements self-contained tick processing for continuation trading stocks
to eliminate cross-contamination and nested loops. Each stock processes only
its own ticks using its own price data and state-based routing.
"""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ContinuationTickProcessor:
    """Handles tick processing for individual continuation stocks"""
    
    def __init__(self, stock):
        """
        Initialize tick processor for a specific stock
        
        Args:
            stock: StockState instance from continuation_stock_monitor
        """
        self.stock = stock
    
    def process_tick(self, price: float, timestamp: datetime):
        """
        Process a tick for THIS stock only with real-time high/low tracking
        
        Args:
            price: Current price for THIS stock
            timestamp: Tick timestamp
        """
        # DEBUG: Check if ticks are reaching the tick processor
        print(f"[TICK PROCESSOR] {timestamp.strftime('%H:%M:%S')} - {self.stock.symbol}: Processing tick Rs{price:.2f}")
        
        # Always update price tracking regardless of state
        self.stock.update_price(price, timestamp)
        
        # Real-time high/low tracking for continuation stocks
        # This should be called for all active stocks to update entry levels
        if self.stock.is_active:
            self._track_entry_levels(price, timestamp)
        
        # Route to state-specific handlers
        if self.stock.is_active and self.stock.entry_ready and not self.stock.entered:
            self._handle_entry_monitoring(price, timestamp)
        
        elif self.stock.entered:
            self._handle_exit_monitoring(price, timestamp)
        
        # Other states don't need tick processing:
        # - Not active: Rejected or not monitoring
        # - Not entry ready: Waiting for entry time
        # - Already entered: Handled by exit monitoring

    def _track_entry_levels(self, price: float, timestamp: datetime):
        """
        Track entry levels for continuation stocks
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        # DEBUG: Log the tracking process
        print(f"[TRACKING] {timestamp.strftime('%H:%M:%S')} - {self.stock.symbol}: Price Rs{price:.2f}, Daily High: Rs{self.stock.daily_high:.2f}, Open: Rs{self.stock.open_price:.2f}")
        
        # Always update daily high/low tracking
        self.stock.daily_high = max(self.stock.daily_high, price)
        self.stock.daily_low = min(self.stock.daily_low, price)
        
        # For continuation stocks, entry high should be the daily high
        # This allows tracking of actual price movement during the session
        if self.stock.daily_high > 0:  # Ensure we have a valid high
            new_entry_high = self.stock.daily_high
            new_entry_sl = new_entry_high * (1 - 0.04)  # 4% SL
            
            # Update entry levels if they've changed
            if (self.stock.entry_high is None or 
                new_entry_high != self.stock.entry_high or
                new_entry_sl != self.stock.entry_sl):
                self.stock.entry_high = new_entry_high
                self.stock.entry_sl = new_entry_sl
                self.stock.entry_ready = True
                print(f"[TRACKING] {timestamp.strftime('%H:%M:%S')} - {self.stock.symbol}: Updated Entry High: Rs{self.stock.entry_high:.2f}, SL: Rs{self.stock.entry_sl:.2f}")
                logger.info(f"[{self.stock.symbol}] Continuation entry updated - High: {self.stock.entry_high:.2f}, SL: {self.stock.entry_sl:.2f}")

    def _handle_entry_monitoring(self, price: float, timestamp: datetime):
        """
        Handle entry monitoring for continuation stocks
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        # DEBUG: Add state validation logging
        logger.info(f"[{self.stock.symbol}] Entry monitoring - Current state: active={self.stock.is_active}, Entry ready: {self.stock.entry_ready}, Entered: {self.stock.entered}")
        
        # Only process entries if stock is in correct state and ready
        if not self.stock.is_active:
            logger.info(f"[{self.stock.symbol}] Skipping entry - not active")
            return
        
        if not self.stock.entry_ready:
            logger.info(f"[{self.stock.symbol}] Skipping entry - not entry ready")
            return
            
        if self.stock.entered:
            logger.info(f"[{self.stock.symbol}] Skipping entry - already entered")
            return

        # Continuation entry logic - Enter when price crosses above entry_high
        if self.stock.entry_high is not None and price >= self.stock.entry_high:
            # Enter position
            self.stock.enter_position(price, timestamp)
            
            logger.info(f"[{self.stock.symbol}] CONTINUATION TRIGGERED at {price:.2f} - Entered position")

    def _handle_exit_monitoring(self, price: float, timestamp: datetime):
        """
        Handle exit monitoring (trailing SL + exit signals)
        
        Args:
            price: Current price for THIS stock
            timestamp: Current timestamp
        """
        if not self.stock.entered or self.stock.entry_price is None:
            return
        
        # Calculate current profit percentage
        profit_pct = (price - self.stock.entry_price) / self.stock.entry_price
        
        # Trailing SL: Move SL to entry when 5% profit
        if profit_pct >= 0.05 and self.stock.entry_sl < self.stock.entry_price:
            old_sl = self.stock.entry_sl
            self.stock.entry_sl = self.stock.entry_price  # Move to breakeven
            logger.info(f"[{self.stock.symbol}] Trailing SL adjusted: Rs{old_sl:.2f} → Rs{self.stock.entry_sl:.2f} (5% profit reached)")
        
        # Check exit signal: SL hit
        if price <= self.stock.entry_sl:
            pnl = profit_pct * 100
            self.stock.exit_position(price, timestamp, "Stop Loss Hit")
            logger.info(f"[{self.stock.symbol}] EXIT at Rs{price:.2f}, PNL: {pnl:+.2f}%")