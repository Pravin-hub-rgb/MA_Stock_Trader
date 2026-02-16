"""
Subscription Manager Module

Implements dynamic unsubscribe functionality for reversal trading stocks to manage
WebSocket subscriptions based on stock states. This module provides helper functions
and methods to unsubscribe from rejected, unselected, and exited stocks.
"""

from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class SubscriptionManager:
    """Manages WebSocket subscriptions for reversal trading stocks"""
    
    def __init__(self, data_streamer, monitor):
        """
        Initialize subscription manager
        
        Args:
            data_streamer: SimpleStockStreamer instance
            monitor: ReversalStockMonitor instance
        """
        self.data_streamer = data_streamer
        self.monitor = monitor
    
    def subscribe_all(self, instrument_keys: List[str]):
        """
        Subscribe to all instruments and update tracking
        
        Args:
            instrument_keys: List of instrument keys to subscribe to
        """
        try:
            if self.data_streamer.streamer:
                self.data_streamer.streamer.subscribe(instrument_keys, "full")
            print(f"Subscribed to {len(instrument_keys)} instruments in 'full' mode")
        except Exception as e:
            print(f"Subscribe error: {e}")
    
    def safe_unsubscribe(self, instrument_keys: List[str], reason: str):
        """
        Safely unsubscribe from instruments with error handling
        
        Args:
            instrument_keys: List of instrument keys to unsubscribe
            reason: Reason for unsubscribe (for logging)
        """
        if not instrument_keys:
            return
        
        try:
            # Remove from active instruments list so they won't be re-subscribed on reconnection
            for key in instrument_keys:
                if key in self.data_streamer.active_instruments:
                    self.data_streamer.active_instruments.remove(key)
            
            # Call Upstox unsubscribe if streamer is available
            if self.data_streamer.streamer:
                self.data_streamer.streamer.unsubscribe(instrument_keys)
            
            print(f"Unsubscribed {len(instrument_keys)} stocks - Reason: {reason}")
            print(f"Active instruments remaining: {len(self.data_streamer.active_instruments)}")
            
            # Log which stocks were unsubscribed
            for key in instrument_keys:
                stock = self.monitor.stocks.get(key)
                if stock:
                    print(f"   ✓ {stock.symbol}")
                else:
                    print(f"   ✓ {key}")
            
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            print(f"Continuing with tick filtering for {len(instrument_keys)} stocks")
    
    def get_rejected_stocks(self) -> List[str]:
        """
        Get list of rejected stock instrument keys
        
        Returns:
            List of instrument keys for stocks in REJECTED state
        """
        from .state_machine import StockState
        
        rejected_keys = []
        
        for instrument_key, stock in self.monitor.stocks.items():
            if stock.state == StockState.REJECTED and stock.is_subscribed:
                rejected_keys.append(instrument_key)
        
        return rejected_keys
    
    def get_unselected_stocks(self) -> List[str]:
        """
        Get list of not selected stock instrument keys
        
        Returns:
            List of instrument keys for stocks in NOT_SELECTED state
        """
        from .state_machine import StockState
        
        unselected_keys = []
        
        for instrument_key, stock in self.monitor.stocks.items():
            if stock.state == StockState.NOT_SELECTED and stock.is_subscribed:
                unselected_keys.append(instrument_key)
        
        return unselected_keys
    
    def get_exited_stocks(self) -> List[str]:
        """
        Get list of exited stock instrument keys
        
        Returns:
            List of instrument keys for stocks in EXITED state
        """
        from .state_machine import StockState
        
        exited_keys = []
        
        for instrument_key, stock in self.monitor.stocks.items():
            if stock.state == StockState.EXITED and stock.is_subscribed:
                exited_keys.append(instrument_key)
        
        return exited_keys
    
    def mark_stocks_unsubscribed(self, instrument_keys: List[str]):
        """
        Mark stocks as unsubscribed after successful unsubscribe
        
        Args:
            instrument_keys: List of instrument keys that were unsubscribed
        """
        for instrument_key in instrument_keys:
            if instrument_key in self.monitor.stocks:
                stock = self.monitor.stocks[instrument_key]
                stock.is_subscribed = False
                # Import StockState from state_machine
                from .state_machine import StockState
                stock.state = StockState.UNSUBSCRIBED
                logger.info(f"[{stock.symbol}] Marked as UNSUBSCRIBED")
    
    def unsubscribe_gap_rejected(self):
        """Unsubscribe stocks rejected during gap validation"""
        print("\n" + "=" * 55)
        print("PHASE 1: UNSUBSCRIBING GAP-REJECTED STOCKS")
        print("=" * 55)
        
        rejected_after_gap = self.get_rejected_stocks()
        
        if rejected_after_gap:
            self.safe_unsubscribe(rejected_after_gap, "gap_rejected")
            self.mark_stocks_unsubscribed(rejected_after_gap)
            print(f"\nUnsubscribed {len(rejected_after_gap)} gap-rejected stocks")
        else:
            print("\nNo stocks rejected at gap validation")
        
        self.log_subscription_status()
    
    def unsubscribe_low_violated(self):
        """Unsubscribe stocks that violated low after entry time"""
        print("\n" + "=" * 55)
        print("PHASE 2: CHECKING LOW VIOLATIONS")
        print("=" * 55)
        
        # Final low violation check before selection
        self.monitor.check_violations()
        
        # Unsubscribe any stocks that violated low
        rejected_after_low = self.get_rejected_stocks()
        if rejected_after_low:
            self.safe_unsubscribe(rejected_after_low, "low_violation")
            self.mark_stocks_unsubscribed(rejected_after_low)
            print(f"Unsubscribed {len(rejected_after_low)} low-violated stocks")
        else:
            print("No low violations detected")
        
        self.log_subscription_status()
    
    def unsubscribe_non_selected(self, selected_stocks: List):
        """Unsubscribe stocks not selected during selection phase"""
        print("\n" + "=" * 55)
        print("PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED")
        print("=" * 55)
        
        # Mark selected and non-selected stocks
        selected_keys = {stock.instrument_key for stock in selected_stocks}

        for stock in self.monitor.stocks.values():
            if stock.instrument_key in selected_keys:
                # Selected stock
                stock.mark_selected()
                stock.entry_ready = True
                print(f"SELECTED: {stock.symbol}")
            else:
                # Not selected - mark for unsubscribe
                stock.mark_not_selected()
                print(f"NOT SELECTED: {stock.symbol} (limited to {len(selected_stocks)} positions)")

        # Unsubscribe non-selected stocks
        unselected_stocks = self.get_unselected_stocks()

        if unselected_stocks:
            self.safe_unsubscribe(unselected_stocks, "not_selected")
            self.mark_stocks_unsubscribed(unselected_stocks)
            print(f"\nUnsubscribed {len(unselected_stocks)} non-selected stocks")
        else:
            print("\nAll qualified stocks were selected")

        self.log_subscription_status()
    
    def unsubscribe_exited(self):
        """Unsubscribe stocks that have exited positions"""
        exited_stocks = self.get_exited_stocks()
        if exited_stocks:
            self.safe_unsubscribe(exited_stocks, "position_closed")
            self.mark_stocks_unsubscribed(exited_stocks)
            
            # Log summary
            for key in exited_stocks:
                stock = self.monitor.stocks.get(key)
                if stock:
                    print(f"[CLOSED] {stock.symbol} - Unsubscribed after exit")
    
    def log_subscription_status(self):
        """Log current subscription status for all stocks"""
        print("\n=== SUBSCRIPTION STATUS ===")
        
        # Import StockState from state_machine
        from .state_machine import StockState
        
        by_state = {}
        for stock in self.monitor.stocks.values():
            state_name = stock.state.value
            if state_name not in by_state:
                by_state[state_name] = []
            by_state[state_name].append(stock.symbol)
        
        for state_name, symbols in sorted(by_state.items()):
            print(f"  {state_name.upper()}: {len(symbols)} stocks - {symbols}")

        subscribed = [s.symbol for s in self.monitor.stocks.values() if s.is_subscribed]
        print(f"\nACTIVELY SUBSCRIBED: {len(subscribed)} stocks - {subscribed}")
        
        print("=" * 50)


def safe_unsubscribe(data_streamer, instrument_keys: List[str], reason: str):
    """
    Standalone helper function for safe unsubscribe
    
    Args:
        data_streamer: SimpleStockStreamer instance
        instrument_keys: List of instrument keys to unsubscribe
        reason: Reason for unsubscribe (for logging)
    """
    if not instrument_keys:
        return
    
    try:
        data_streamer.unsubscribe(instrument_keys)
        print(f"[UNSUBSCRIBE] Removed {len(instrument_keys)} stocks - Reason: {reason}")
        
        # Log which stocks were unsubscribed
        for key in instrument_keys:
            print(f"   ✓ {key}")
        
    except Exception as e:
        print(f"[UNSUBSCRIBE ERROR] Failed to unsubscribe: {e}")
        print(f"[UNSUBSCRIBE ERROR] Continuing with tick filtering for {len(instrument_keys)} stocks")