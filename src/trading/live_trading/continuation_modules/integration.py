#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Integration Module

Provides complete integration helpers and utilities for the continuation trading bot.
This module contains the main integration logic that ties together all the modules
and provides a clean interface for the main run_continuation.py script.
"""

import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class ContinuationIntegration:
    """Main integration class for continuation trading bot"""
    
    def __init__(self, data_streamer, monitor, paper_trader=None):
        """
        Initialize integration with all required components
        
        Args:
            data_streamer: SimpleStockStreamer instance
            monitor: StockMonitor instance
            paper_trader: PaperTrader instance (optional)
        """
        self.data_streamer = data_streamer
        self.monitor = monitor
        self.paper_trader = paper_trader
        
        # Initialize modules
        from .subscription_manager import ContinuationSubscriptionManager
        self.subscription_manager = ContinuationSubscriptionManager(data_streamer, monitor)
        
        # Initialize tick processor for each stock
        self.tick_processors = {}
        for stock in monitor.stocks.values():
            from .tick_processor import ContinuationTickProcessor
            self.tick_processors[stock.instrument_key] = ContinuationTickProcessor(stock)
    
    def simplified_tick_handler(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: List = None):
        """
        Simplified continuation tick handler that delegates to modules
        
        Args:
            instrument_key: Stock instrument key
            symbol: Stock symbol
            price: Current price
            timestamp: Tick timestamp
            ohlc_list: OHLC data (optional)
        """
        
        # Get stock
        stock = self.monitor.stocks.get(instrument_key)
        if not stock:
            return
        
        # Early exit for unsubscribed stocks (follow reversal bot pattern)
        # This ensures gap-rejected stocks disappear completely from monitoring
        if not stock.is_subscribed:
            return
        
        # Process OHLC data first (for reliable opening price and high/low tracking)
        if ohlc_list:
            self.monitor.process_candle_data(instrument_key, symbol, ohlc_list)
        
        # Early exit for rejected stocks (don't process tick data)
        if not stock.is_active:
            return
        
        # Get tick processor for this stock
        tick_processor = self.tick_processors.get(instrument_key)
        if not tick_processor:
            logger.warning(f"No tick processor found for {symbol}")
            return
        
        # Delegate to stock's own tick processor
        tick_processor.process_tick(price, timestamp)
        
        # Handle paper trading logs
        self._handle_paper_trading_logs(stock, price, timestamp)
        
        # Check if both positions are filled and unsubscribe remaining stocks
        self._check_and_unsubscribe_after_positions_filled()
    
    def _handle_paper_trading_logs(self, stock, price: float, timestamp: datetime):
        """
        Handle paper trading logs for entry and exit events
        
        Args:
            stock: StockState instance
            price: Current price
            timestamp: Current timestamp
        """
        # Log paper trades if stock just entered (only log once using entry_logged flag)
        if stock.entered and not stock.entry_logged and stock.entry_time:
            stock.entry_logged = True  # Mark as logged to prevent duplicates
            if self.paper_trader:
                self.paper_trader.log_entry(stock, price, timestamp)
            try:
                print(f"ENTRY {stock.symbol} entered at Rs{stock.entry_price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
            except Exception as e:
                print(f"DEBUG ERROR in ENTRY logging for {stock.symbol}: {e}")
                print(f"DEBUG: entry_price={stock.entry_price}, entry_sl={stock.entry_sl}")
                print(f"ENTRY {stock.symbol} entered, SL placed")
        
        # Log paper exits if stock just exited
        if stock.exit_time and abs((stock.exit_time - timestamp).total_seconds()) < 1:
            if self.paper_trader:
                self.paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")
            try:
                print(f"EXIT {stock.symbol} exited at Rs{stock.exit_price:.2f}, PNL: {stock.pnl:+.2f}%")
            except Exception as e:
                print(f"DEBUG ERROR in EXIT logging for {stock.symbol}: {e}")
                print(f"DEBUG: exit_price={stock.exit_price}, pnl={stock.pnl}")
                print(f"EXIT {stock.symbol} exited")
    
    def prepare_and_subscribe(self, instrument_keys: List[str]):
        """
        Prepare entries and subscribe to all stocks
        
        Args:
            instrument_keys: List of instrument keys to subscribe
        """
        # Subscribe to all stocks initially
        self.subscription_manager.subscribe_all(instrument_keys)
        
        # Prepare entry levels for qualified stocks
        self.monitor.prepare_entries()
        
        # Log subscription status
        self.subscription_manager.log_subscription_status()
        
        # FIX: Update data streamer's active instruments to match validated stocks
        # This fixes the subscription tracking discrepancy
        self.data_streamer.update_active_instruments(instrument_keys)

    def phase_1_unsubscribe_after_gap_and_vah(self):
        """
        Phase 1: Unsubscribe stocks that failed gap validation or VAH validation
        Called immediately after gap validation at 9:14:30
        
        OPTIMIZATION: This method is now deprecated since we only subscribe to validated stocks
        The subscription filtering happens in run_continuation.py before this method is called
        """
        print("\n=== PHASE 1: UNSUBSCRIBING GAP+VAH REJECTED STOCKS ===")
        print("SKIPPED - Optimization implemented: Only validated stocks are subscribed")
        print("Gap/VAH validation filtering happens before subscription in run_continuation.py")
        
        # Log current subscription status for debugging
        self.subscription_manager.log_subscription_status()

    def phase_2_unsubscribe_after_low_and_volume(self):
        """
        Phase 2: Unsubscribe stocks that failed low violation check or volume validation
        Called at 9:20 after all validations are complete
        """
        self.subscription_manager.unsubscribe_low_and_volume_failed()
    
    def log_final_subscription_status(self):
        """Log final subscription status"""
        self.subscription_manager.log_subscription_status()
    
    def get_subscription_summary(self) -> dict:
        """
        Get summary of current subscription status
        
        Returns:
            Dictionary with subscription counts by state
        """
        summary = {
            'total_stocks': len(self.monitor.stocks),
            'subscribed': 0,
            'unsubscribed': 0,
            'by_state': {}
        }
        
        for stock in self.monitor.stocks.values():
            state_name = "subscribed" if stock.instrument_key in self.subscription_manager.subscribed_keys else "unsubscribed"
            if state_name not in summary['by_state']:
                summary['by_state'][state_name] = 0
            summary['by_state'][state_name] += 1
            
            if stock.instrument_key in self.subscription_manager.subscribed_keys:
                summary['subscribed'] += 1
            else:
                summary['unsubscribed'] += 1
        
        return summary
    
    def _check_and_unsubscribe_after_positions_filled(self):
        """
        Check if both positions are filled and unsubscribe remaining stocks
        This implements the first-come-first-serve logic where unsubscription
        only happens after both slots are occupied.
        """
        self.subscription_manager.unsubscribe_remaining_after_positions_filled()
    
    def cleanup(self):
        """Clean up all subscriptions at end of day"""
        print("\n=== CLEANUP: UNSUBSCRIBING ALL STOCKS ===")
        self.subscription_manager.cleanup_all()


def create_integration(data_streamer, monitor, paper_trader=None):
    """
    Factory function to create integration instance
    
    Args:
        data_streamer: SimpleStockStreamer instance
        monitor: StockMonitor instance
        paper_trader: PaperTrader instance (optional)
        
    Returns:
        ContinuationIntegration instance
    """
    return ContinuationIntegration(data_streamer, monitor, paper_trader)


def log_performance_metrics(integration: ContinuationIntegration):
    """
    Log performance metrics for the trading session
    
    Args:
        integration: ContinuationIntegration instance
    """
    summary = integration.get_subscription_summary()
    
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS SUMMARY")
    print("=" * 60)
    print(f"Total stocks monitored: {summary['total_stocks']}")
    print(f"Actively subscribed: {summary['subscribed']}")
    print(f"Unsubscribed: {summary['unsubscribed']}")
    
    print("\nStocks by state:")
    for state, count in summary['by_state'].items():
        print(f"  {state.upper()}: {count}")
    
    # Calculate efficiency metrics
    if summary['total_stocks'] > 0:
        efficiency = (summary['total_stocks'] - summary['subscribed']) / summary['total_stocks'] * 100
        print(f"\nSubscription efficiency: {efficiency:.1f}% reduction in active subscriptions")
    
    print("=" * 60)