#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Waiting Window Monitor Module
Handles continuous monitoring during 9:15:05 → 9:19:00 waiting window
"""

import time as time_module
from datetime import datetime
from typing import Dict, List, Callable, Optional
import logging

logger = logging.getLogger(__name__)

def monitor_waiting_window(stocks: Dict[str, 'ReversalStockState'],
                          data_streamer: 'SimpleStockStreamer',
                          end_time: time,
                          tick_handler: Callable = None) -> Dict[str, 'ReversalStockState']:
    """
    Monitor stocks during the waiting window (9:15:05 → 9:19:00)

    Args:
        stocks: Dict of instrument_key -> ReversalStockState
        data_streamer: The data streamer object
        end_time: When to stop monitoring (ENTRY_TIME)
        tick_handler: Original tick handler to restore

    Returns:
        Updated stocks dict with monitoring results
    """
    logger.info("WAITING WINDOW: Starting continuous monitoring phase")

    # Track monitoring statistics
    monitoring_stats = {
        'ticks_processed': 0,
        'violations_detected': 0,
        'start_time': datetime.now(),
        'end_time': None
    }

    def waiting_window_tick_handler(instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list=None):
        """Custom tick handler for waiting window monitoring"""
        nonlocal monitoring_stats

        monitoring_stats['ticks_processed'] += 1

        # Get the stock
        stock = stocks.get(instrument_key)
        if not stock:
            return

        # Update price tracking for entry trigger preparation
        stock.update_price(price, timestamp)

        # Check low violation (Phase 2 rejection)
        if stock.check_low_violation():
            # Stock passed low violation check
            pass
        else:
            # Stock failed low violation check (rejected)
            monitoring_stats['violations_detected'] += 1
            logger.info(f"WAITING WINDOW VIOLATION: {symbol} rejected - {stock.rejection_reason}")

        # Log progress every 10 ticks
        if monitoring_stats['ticks_processed'] % 10 == 0:
            active_count = len([s for s in stocks.values() if s.is_active])
            logger.info(f"WAITING WINDOW: {monitoring_stats['ticks_processed']} ticks, {active_count} stocks active, {monitoring_stats['violations_detected']} violations")

    # Store original tick handler
    original_tick_handler = data_streamer.tick_handler

    # Override with waiting window handler
    data_streamer.tick_handler = waiting_window_tick_handler

    logger.info(f"WAITING WINDOW: Monitoring until {end_time}...")
    logger.info("WAITING WINDOW: Tracking daily highs and checking low violations...")

    try:
        # Monitor until end time
        while datetime.now().time() < end_time:
            # Small sleep to prevent busy waiting
            time_module.sleep(0.1)

        monitoring_stats['end_time'] = datetime.now()

        # Calculate monitoring duration
        duration = monitoring_stats['end_time'] - monitoring_stats['start_time']

        logger.info("WAITING WINDOW: Monitoring complete")
        logger.info(f"WAITING WINDOW STATS: {monitoring_stats['ticks_processed']} ticks processed in {duration.total_seconds():.1f}s")
        logger.info(f"WAITING WINDOW STATS: {monitoring_stats['violations_detected']} low violations detected")

        # Log final stock status
        active_stocks = [s for s in stocks.values() if s.is_active]
        logger.info(f"WAITING WINDOW RESULT: {len(active_stocks)} stocks remain active for entry preparation")

        for stock in active_stocks:
            gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close * 100)
            logger.info(f"  ✓ {stock.symbol}: Gap {gap_pct:+.1f}%, High: Rs{stock.daily_high:.2f}, Low: Rs{stock.daily_low:.2f}")

    except Exception as e:
        logger.error(f"WAITING WINDOW ERROR: {e}")
        monitoring_stats['error'] = str(e)

    finally:
        # Always restore original tick handler
        data_streamer.tick_handler = original_tick_handler
        logger.info("WAITING WINDOW: Original tick handler restored")

    return stocks


def prepare_entry_triggers(stocks: Dict[str, 'ReversalStockState']) -> Dict[str, 'ReversalStockState']:
    """
    Prepare entry trigger levels based on waiting window highs

    Args:
        stocks: Dict of stocks after waiting window monitoring

    Returns:
        Updated stocks with entry triggers set
    """
    logger.info("ENTRY PREP: Setting entry trigger levels from waiting window highs")

    prepared_count = 0

    for stock in stocks.values():
        if stock.is_active and stock.open_price is not None:
            # Entry trigger is set to the daily high reached during waiting window
            # This ensures we enter on a breakout above the highest point in the window
            stock.entry_high = stock.daily_high

            # Stop loss is 4% below entry high
            stock.entry_sl = stock.entry_high * 0.96

            prepared_count += 1

            logger.info(f"ENTRY PREP: {stock.symbol} - Trigger: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f}")

    logger.info(f"ENTRY PREP: Prepared entry triggers for {prepared_count} stocks")

    return stocks


def get_waiting_window_summary(stocks: Dict[str, 'ReversalStockState']) -> Dict:
    """
    Get summary of waiting window monitoring results

    Args:
        stocks: Dict of stocks after waiting window

    Returns:
        Dict with monitoring summary
    """
    total_stocks = len(stocks)
    active_stocks = [s for s in stocks.values() if s.is_active]
    rejected_stocks = [s for s in stocks.values() if not s.is_active and s.rejection_reason and 'Low violation' in s.rejection_reason]

    return {
        'total_stocks': total_stocks,
        'active_stocks_count': len(active_stocks),
        'violations_count': len(rejected_stocks),
        'active_stocks': [{'symbol': s.symbol, 'entry_trigger': s.entry_high, 'stop_loss': s.entry_sl} for s in active_stocks],
        'rejected_stocks': [{'symbol': s.symbol, 'reason': s.rejection_reason} for s in rejected_stocks]
    }


# Test function for development
def test_waiting_window_monitor():
    """Test function for waiting window monitor"""
    print("Testing waiting window monitor module...")

    # This would be used for integration testing
    # Mock stocks, data streamer, and timing would be created here

    print("Waiting window monitor module test completed")


if __name__ == "__main__":
    test_waiting_window_monitor()
