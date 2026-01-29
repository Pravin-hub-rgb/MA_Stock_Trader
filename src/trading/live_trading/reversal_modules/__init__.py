"""
Reversal Trading Modules

Modular implementation of the reversal trading bot architecture improvements.
This package contains specialized modules for state management, tick processing,
subscription management, and integration helpers.

Modules:
    state_machine: Stock state management and transitions
    tick_processor: Self-contained tick processing per stock
    subscription_manager: Dynamic unsubscribe functionality
    integration: Complete integration helpers and utilities
"""

from .state_machine import StockState
from .tick_processor import ReversalTickProcessor
from .subscription_manager import SubscriptionManager
from .integration import ReversalIntegration

__all__ = [
    'StockState',
    'ReversalTickProcessor', 
    'SubscriptionManager',
    'ReversalIntegration'
]