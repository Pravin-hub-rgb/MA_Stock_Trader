#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Trading Engine Module
Handles all live trading execution logic including triggers, entries, exits, and position management
"""

import time as time_module
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def process_reversal_tick(stock: 'ReversalStockState',
                         price: float,
                         timestamp: datetime,
                         reversal_monitor: 'ReversalMonitor',
                         paper_trader: 'PaperTrader',
                         current_time: time,
                         entry_time: time,
                         global_selected_symbols: set,
                         symbol: str) -> None:
    """
    Process a single tick for reversal trading logic - EXTRACTED FROM MAIN FILE

    Args:
        stock: The stock to process
        price: Current price
        timestamp: Current timestamp
        reversal_monitor: Monitor for trigger checking
        paper_trader: Paper trading handler
        current_time: Current market time
        entry_time: When entry is allowed
        global_selected_symbols: Selected stocks for trading
        symbol: Stock symbol (passed from tick handler)
    """

    # Process OOPS reversal logic (only if opening price is available from API)
    if stock and stock.situation == 'reversal_s2':
        # Check OOPS reversal conditions
        if reversal_monitor.check_oops_trigger(symbol, stock.open_price, stock.previous_close, price):
            if not stock.oops_triggered:
                stock.oops_triggered = True
                logger.info(f"TARGET {symbol}: OOPS reversal triggered - gap down + prev close cross")
                # Enter position immediately for OOPS
                stock.entry_high = price
                stock.entry_sl = price * 0.96  # 4% SL
                stock.enter_position(price, timestamp)
                paper_trader.log_entry(stock, price, timestamp)

    # Check violations for opened stocks (continuous monitoring)
    stock.check_low_violation()

    # Check entry signals only after entry time (only for selected stocks)
    if current_time >= entry_time and stock.symbol in global_selected_symbols:
        entry_signals = stock.monitor.check_entry_signals()

        for entry_stock in entry_signals:
            if entry_stock.symbol in global_selected_symbols:  # Only allow selected stocks to enter
                logger.info(f"ENTRY {entry_stock.symbol} entry triggered at Rs{price:.2f}, SL placed at Rs{entry_stock.entry_sl:.2f}")
                entry_stock.enter_position(price, timestamp)
                paper_trader.log_entry(entry_stock, price, timestamp)

        # Check Strong Start entry signals for reversal_s1
        for sel_stock in stock.monitor.stocks.values():
            if sel_stock.symbol in global_selected_symbols and sel_stock.situation in ['reversal_s1']:
                # Check Strong Start conditions
                if reversal_monitor.check_strong_start_trigger(sel_stock.symbol, sel_stock.open_price, sel_stock.previous_close, sel_stock.daily_low):
                    if not sel_stock.strong_start_triggered:
                        sel_stock.strong_start_triggered = True
                        logger.info(f"TARGET {sel_stock.symbol}: Strong Start triggered - gap up + open≈low")
                        # Enter position for Strong Start
                        sel_stock.entry_high = price
                        sel_stock.entry_sl = price * 0.96  # 4% SL
                        sel_stock.enter_position(price, timestamp)
                        paper_trader.log_entry(sel_stock, price, timestamp)

    # Check trailing stops and exit signals for entered positions
    if current_time >= entry_time:
        # Check for trailing stop adjustments (5% profit -> move SL to entry)
        for entered_stock in stock.monitor.stocks.values():
            if entered_stock.entered and entered_stock.entry_price and entered_stock.current_price:
                profit_pct = (entered_stock.current_price - entered_stock.entry_price) / entered_stock.entry_price
                if profit_pct >= 0.05:  # 5% profit
                    new_sl = entered_stock.entry_price  # Move SL to breakeven
                    if entered_stock.entry_sl < new_sl:
                        old_sl = entered_stock.entry_sl
                        entered_stock.entry_sl = new_sl
                        logger.info(f"TRAILING {entered_stock.symbol} trailing stop adjusted: Rs{old_sl:.2f} -> Rs{new_sl:.2f} (5% profit)")

        # Check exit signals (including updated trailing stops)
        exit_signals = stock.monitor.check_exit_signals()
        for exit_stock in exit_signals:
            pnl = (price - exit_stock.entry_price) / exit_stock.entry_price * 100
            logger.info(f"EXIT {exit_stock.symbol} exited at Rs{price:.2f}, PNL: {pnl:+.2f}%")
            exit_stock.exit_position(price, timestamp, "Stop Loss Hit")
            paper_trader.log_exit(exit_stock, price, timestamp, "Stop Loss Hit")


def execute_reversal_trading_cycle(stocks: Dict[str, 'ReversalStockState'],
                                  data_streamer: 'SimpleStockStreamer',
                                  reversal_monitor: 'ReversalMonitor',
                                  paper_trader: 'PaperTrader',
                                  entry_time: time,
                                  global_selected_symbols: set) -> None:
    """
    Execute the main trading cycle with modular trading logic

    Args:
        stocks: All monitored stocks
        data_streamer: Data streamer for ticks
        reversal_monitor: Monitor for trigger checking
        paper_trader: Paper trading handler
        entry_time: When entry is allowed
        global_selected_symbols: Selected stocks for trading
    """

    def modular_tick_handler(instrument_key: str, symbol: str, price: float, timestamp, ohlc_list=None):
        """Modular tick handler using trading engine"""
        stock = stocks.get(instrument_key)
        if not stock:
            return

        # Update stock price data
        stock.update_price(price, timestamp)

        # Process reversal trading logic
        current_time = datetime.now().time()
        process_reversal_tick(
            stock=stock,
            price=price,
            timestamp=timestamp,
            reversal_monitor=reversal_monitor,
            paper_trader=paper_trader,
            current_time=current_time,
            entry_time=entry_time,
            global_selected_symbols=global_selected_symbols
        )

    # Set the modular tick handler
    original_handler = data_streamer.tick_handler
    data_streamer.tick_handler = modular_tick_handler

    logger.info("TRADING ENGINE: Starting live trading execution")
    logger.info(f"TRADING ENGINE: Monitoring {len(global_selected_symbols)} selected stocks")

    try:
        # Run the trading cycle
        data_streamer.run()
    except KeyboardInterrupt:
        logger.info("TRADING ENGINE: Stopped by user")
    finally:
        # Restore original handler if needed
        data_streamer.tick_handler = original_handler


def get_trading_summary(stocks: Dict[str, 'ReversalStockState']) -> Dict:
    """
    Get trading execution summary

    Args:
        stocks: All stocks after trading

    Returns:
        Dict with trading summary
    """
    entered_positions = [s for s in stocks.values() if s.entered]
    exited_positions = [s for s in stocks.values() if s.exit_price is not None]

    total_pnl = sum(s.pnl for s in exited_positions if s.pnl is not None)

    return {
        'total_positions_taken': len(entered_positions),
        'positions_exited': len(exited_positions),
        'active_positions': len(entered_positions) - len(exited_positions),
        'total_pnl': total_pnl,
        'positions': [{
            'symbol': s.symbol,
            'entry_price': s.entry_price,
            'exit_price': s.exit_price,
            'pnl': s.pnl,
            'entry_time': s.entry_time.isoformat() if s.entry_time else None,
            'exit_time': s.exit_time.isoformat() if s.exit_time else None
        } for s in entered_positions]
    }


# Test function for development
def test_trading_engine():
    """Test function for trading engine module"""
    print("Testing trading engine module...")

    # This would be used for integration testing
    # Mock stocks, triggers, and trading scenarios would be created here

    print("Trading engine module test completed")


if __name__ == "__main__":
    test_trading_engine()
