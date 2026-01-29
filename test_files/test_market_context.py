#!/usr/bin/env python3
"""
Test script for the new market-context-based OOPS execution logic
"""

import sys
import os
sys.path.append('src')

from trading.live_trading.reversal_monitor import ReversalMonitor
from datetime import time

def test_market_context_logic():
    """Test the market context execution logic"""
    print("🚀 Testing Market Context Execution Logic\n")

    monitor = ReversalMonitor()

    # Load watchlist
    success = monitor.load_watchlist()
    if not success:
        print("❌ Failed to load watchlist")
        return

    # Rank stocks
    monitor.rank_stocks_by_quality()

    print("\n" + "="*60)
    print("TESTING MARKET CONTEXT SCENARIOS")
    print("="*60)

    # Test 1: Multiple OOPS candidates (gap down day)
    print("\n🎯 SCENARIO 1: MULTIPLE OOPS CANDIDATES (GAP DOWN DAY)")
    market_data_scenario1 = {
        'MEESHO': {'open': 150.0, 'prev_close': 164.29, 'ltp': 166.0, 'low': 149.0},  # 8.5% gap down
        'ORIENTTECH': {'open': 330.0, 'prev_close': 368.50, 'ltp': 372.0, 'low': 329.0},  # 10.5% gap down
        'ELECON': {'open': 410.0, 'prev_close': 395.95, 'ltp': 415.0, 'low': 408.0},  # 3.6% gap up
        'GVT&D': {'open': 2420.0, 'prev_close': 2796.00, 'ltp': 2440.0, 'low': 2410.0},  # 13.4% gap down
    }

    current_time = time(9, 30)  # After Strong Start window
    monitor.reset_daily_state()
    monitor.execute_market_context_logic(market_data_scenario1, current_time)

    # Test 2: Single OOPS candidate (mixed day)
    print("\n🔄 SCENARIO 2: SINGLE OOPS CANDIDATE (MIXED DAY)")
    market_data_scenario2 = {
        'MEESHO': {'open': 170.0, 'prev_close': 164.29, 'ltp': 168.0, 'low': 169.0},  # 3.3% gap up (Strong Start)
        'ORIENTTECH': {'open': 330.0, 'prev_close': 368.50, 'ltp': 372.0, 'low': 329.0},  # 10.5% gap down (OOPS)
        'ELECON': {'open': 410.0, 'prev_close': 395.95, 'ltp': 415.0, 'low': 408.0},  # 3.6% gap up (Strong Start)
    }

    monitor.reset_daily_state()
    monitor.execute_market_context_logic(market_data_scenario2, current_time)

    # Test 3: No OOPS candidates (gap up day)
    print("\n📈 SCENARIO 3: NO OOPS CANDIDATES (GAP UP DAY)")
    market_data_scenario3 = {
        'MEESHO': {'open': 170.0, 'prev_close': 164.29, 'ltp': 168.0, 'low': 169.0},  # 3.3% gap up (Strong Start)
        'ELECON': {'open': 410.0, 'prev_close': 395.95, 'ltp': 415.0, 'low': 408.0},  # 3.6% gap up (Strong Start)
    }

    current_time_strong_start = time(9, 18)  # During Strong Start window
    monitor.reset_daily_state()
    monitor.execute_market_context_logic(market_data_scenario3, current_time_strong_start)

    print("\n✅ All market context scenarios tested!")

if __name__ == "__main__":
    test_market_context_logic()
