"""
Integration Module

Provides complete integration helpers and utilities for the reversal trading bot.
This module contains the main integration logic that ties together all the modules
and provides a clean interface for the main run_reversal.py script.
"""

from datetime import datetime
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class ReversalIntegration:
    """Main integration class for reversal trading bot"""
    
    def __init__(self, data_streamer, monitor, paper_trader=None):
        """
        Initialize integration with all required components
        
        Args:
            data_streamer: SimpleStockStreamer instance
            monitor: ReversalStockMonitor instance
            paper_trader: PaperTrader instance (optional)
        """
        self.data_streamer = data_streamer
        self.monitor = monitor
        self.paper_trader = paper_trader
        
        # Initialize modules
        from .subscription_manager import SubscriptionManager
        self.subscription_manager = SubscriptionManager(data_streamer, monitor)
        
        # Initialize tick processor for each stock
        self.tick_processors = {}
        for stock in monitor.stocks.values():
            from .tick_processor import ReversalTickProcessor
            self.tick_processors[stock.instrument_key] = ReversalTickProcessor(stock)
    
    def simplified_tick_handler(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: List = None, reversal_monitor=None):
        """
        Simplified reversal tick handler that delegates to modules
        
        Args:
            instrument_key: Stock instrument key
            symbol: Stock symbol
            price: Current price
            timestamp: Tick timestamp
            ohlc_list: OHLC data (optional)
            reversal_monitor: ReversalMonitor instance (optional)
        """
        # Get stock
        stock = self.monitor.stocks.get(instrument_key)
        if not stock:
            return
        
        # Early exit for unsubscribed stocks
        if not stock.is_subscribed:
            return
        
        # Get tick processor for this stock
        tick_processor = self.tick_processors.get(instrument_key)
        if not tick_processor:
            logger.warning(f"No tick processor found for {symbol}")
            return
        
        # Delegate to stock's own tick processor
        tick_processor.process_tick(price, timestamp, reversal_monitor)
        
        # Handle paper trading logs
        self._handle_paper_trading_logs(stock, price, timestamp)
        
        # REMOVED: unsubscribe_exited() call - this will be handled by phase methods at proper times
    
    def _handle_paper_trading_logs(self, stock, price: float, timestamp: datetime):
        """
        Handle paper trading logs for entry and exit events
        
        Args:
            stock: ReversalStockState instance
            price: Current price
            timestamp: Current timestamp
        """
        # Log paper trades if stock just entered
        if stock.entered and stock.entry_time and abs((stock.entry_time - timestamp).total_seconds()) < 1:
            if self.paper_trader:
                self.paper_trader.log_entry(stock, price, timestamp)
            try:
                print(f"ENTRY {stock.symbol} entered at Rs{stock.entry_price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
            except Exception as e:
                print(f"DEBUG ERROR in ENTRY logging for {stock.symbol}: {e}")
                print(f"DEBUG: entry_price={stock.entry_price}, entry_sl={stock.entry_sl}")
                print(f"ENTRY {stock.symbol} entered, SL placed")
            
            # ✅ CHECK IF BOTH POSITIONS ARE FILLED AND UNSUBSCRIBE REMAINING STOCKS
            self._check_and_unsubscribe_after_positions_filled()
        
        # Log paper exits if stock just exited
        # Import StockState from state_machine
        from .state_machine import StockState
        if stock.state == StockState.EXITED and stock.exit_time and abs((stock.exit_time - timestamp).total_seconds()) < 1:
            if self.paper_trader:
                self.paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")
            try:
                print(f"EXIT {stock.symbol} exited at Rs{stock.exit_price:.2f}, PNL: {stock.pnl:+.2f}%")
            except Exception as e:
                print(f"DEBUG ERROR in EXIT logging for {stock.symbol}: {e}")
                print(f"DEBUG: exit_price={stock.exit_price}, pnl={stock.pnl}")
                print(f"EXIT {stock.symbol} exited")
    
    def phase_1_unsubscribe_after_gap_validation(self):
        """Execute Phase 1: Unsubscribe after gap validation"""
        self.subscription_manager.unsubscribe_gap_rejected()
    
    def phase_2_unsubscribe_after_low_violation(self):
        """Execute Phase 2: Unsubscribe after low violation check"""
        self.subscription_manager.unsubscribe_low_violated()
    
    def phase_3_unsubscribe_after_selection(self, selected_stocks: List):
        """Execute Phase 3: Unsubscribe after selection"""
        self.subscription_manager.unsubscribe_non_selected(selected_stocks)
    
    def prepare_entries_and_select(self, selection_engine):
        """
        Prepare entries and select stocks using the integration
        
        Args:
            selection_engine: SelectionEngine instance
            
        Returns:
            List of selected stocks
        """
        # Prepare entry levels for qualified stocks
        self.monitor.prepare_entries()

        # Get qualified and select
        qualified_stocks = self.monitor.get_qualified_stocks()
        print(f"\nQualified stocks: {len(qualified_stocks)}")

        selected_stocks = selection_engine.select_stocks(qualified_stocks)
        print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

        return selected_stocks
    
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
            state_name = stock.state.value
            if state_name not in summary['by_state']:
                summary['by_state'][state_name] = 0
            summary['by_state'][state_name] += 1
            
            if stock.is_subscribed:
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
        # Count entered positions
        entered_positions = 0
        subscribed_stocks = []
        
        for stock in self.monitor.stocks.values():
            if stock.is_subscribed:
                subscribed_stocks.append(stock)
                if stock.entered:
                    entered_positions += 1
        
        # If we have 2 entered positions and more than 2 subscribed stocks,
        # unsubscribe the remaining ones
        if entered_positions >= 2 and len(subscribed_stocks) > 2:
            remaining_stocks = [stock for stock in subscribed_stocks if not stock.entered]
            
            if remaining_stocks:
                remaining_keys = [stock.instrument_key for stock in remaining_stocks]
                print(f"\n=== UNSUBSCRIBING REMAINING STOCKS AFTER 2 POSITIONS FILLED ===")
                print(f"Unsubscribing {len(remaining_stocks)} remaining stocks: {[s.symbol for s in remaining_stocks]}")
                
                self.subscription_manager.safe_unsubscribe(remaining_keys, "positions_filled")
                self.subscription_manager.mark_stocks_unsubscribed(remaining_keys)
                
                self.subscription_manager.log_subscription_status()
    
    def cleanup(self):
        """Clean up all subscriptions at end of day"""
        print("\n=== CLEANUP: UNSUBSCRIBING ALL STOCKS ===")
        
        # Get all subscribed stocks
        subscribed_keys = []
        for key, stock in self.monitor.stocks.items():
            if stock.is_subscribed:
                subscribed_keys.append(key)
        
        if subscribed_keys:
            self.subscription_manager.safe_unsubscribe(subscribed_keys, "end_of_day")
            self.subscription_manager.mark_stocks_unsubscribed(subscribed_keys)
            print(f"Unsubscribed {len(subscribed_keys)} stocks at end of day")
        else:
            print("No stocks to unsubscribe")
        
        self.log_final_subscription_status()


def create_integration(data_streamer, monitor, paper_trader=None):
    """
    Factory function to create integration instance
    
    Args:
        data_streamer: SimpleStockStreamer instance
        monitor: ReversalStockMonitor instance
        paper_trader: PaperTrader instance (optional)
        
    Returns:
        ReversalIntegration instance
    """
    return ReversalIntegration(data_streamer, monitor, paper_trader)


def log_performance_metrics(integration: ReversalIntegration):
    """
    Log performance metrics for the trading session
    
    Args:
        integration: ReversalIntegration instance
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