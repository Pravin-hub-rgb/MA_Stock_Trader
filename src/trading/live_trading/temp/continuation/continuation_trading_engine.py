#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Trading Engine Module
Handles all live trading execution logic for continuation trading
"""

import time as time_module
from datetime import datetime, time
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def process_continuation_tick(stock: 'ContinuationStockState',
                            price: float,
                            timestamp: datetime,
                            vah_dict: Dict[str, float],
                            paper_trader: 'PaperTrader',
                            current_time: time,
                            entry_time: time) -> None:
    """
    Process a single tick for continuation trading logic

    Args:
        stock: The stock to process
        price: Current price
        timestamp: Current timestamp
        vah_dict: Dict of symbol -> VAH values
        paper_trader: Paper trading handler
        current_time: Current market time
        entry_time: When entry is allowed
    """

    # Get VAH for this stock
    vah = vah_dict.get(stock.symbol)
    if not vah:
        return  # No VAH calculated for this stock

    # Check entry signals only after entry time (VAH-based entries for continuation)
    if current_time >= entry_time and stock.symbol in vah_dict:
        # Check entry signal (price crosses above VAH)
        if stock.check_entry_signal(price, vah):
            logger.info(f"ENTRY {stock.symbol} entry triggered at Rs{price:.2f} (VAH: Rs{vah:.2f})")
            stock.enter_position(price, timestamp)
            paper_trader.log_entry(stock, price, timestamp)

    # Check exit signals for entered positions
    if current_time >= entry_time:
        # Check for trailing stop adjustments (5% profit -> move SL to entry)
        for entered_stock in [stock]:  # Process current stock
            if entered_stock.entered and entered_stock.entry_price and entered_stock.current_price:
                profit_pct = (entered_stock.current_price - entered_stock.entry_price) / entered_stock.entry_price
                if profit_pct >= 0.05:  # 5% profit
                    new_sl = entered_stock.entry_price  # Move SL to breakeven
                    if entered_stock.entry_sl < new_sl:
                        old_sl = entered_stock.entry_sl
                        entered_stock.entry_sl = new_sl
                        logger.info(f"TRAILING {entered_stock.symbol} trailing stop adjusted: Rs{old_sl:.2f} -> Rs{new_sl:.2f} (5% profit)")

        # Check exit signals (stop loss hits)
        if stock.entered and stock.check_exit_signal(price):
            pnl = (price - stock.entry_price) / stock.entry_price * 100
            logger.info(f"EXIT {stock.symbol} exited at Rs{price:.2f}, PNL: {pnl:+.2f}%")
            stock.exit_position(price, timestamp, "Stop Loss Hit")
            paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")


def execute_continuation_trading_cycle(stocks: Dict[str, 'ContinuationStockState'],
                                     data_streamer: 'SimpleStockStreamer',
                                     vah_dict: Dict[str, float],
                                     paper_trader: 'PaperTrader',
                                     entry_time: time) -> None:
    """
    Execute the main trading cycle with modular continuation trading logic

    Args:
        stocks: All monitored stocks
        data_streamer: Data streamer for ticks
        vah_dict: Dict of symbol -> VAH values
        paper_trader: Paper trading handler
        entry_time: When entry is allowed
    """

    def modular_continuation_tick_handler(instrument_key: str, symbol: str, price: float, timestamp, ohlc_list=None):
        """Modular tick handler using continuation trading engine"""
        stock = stocks.get(instrument_key)
        if not stock:
            return

        # Update stock price data
        stock.update_price(price, timestamp)

        # Process continuation trading logic
        current_time = datetime.now().time()
        process_continuation_tick(
            stock=stock,
            price=price,
            timestamp=timestamp,
            vah_dict=vah_dict,
            paper_trader=paper_trader,
            current_time=current_time,
            entry_time=entry_time
        )

    # Set the modular tick handler
    original_handler = data_streamer.tick_handler
    data_streamer.tick_handler = modular_continuation_tick_handler

    logger.info("CONTINUATION TRADING ENGINE: Starting live trading execution")
    vah_count = len([v for v in vah_dict.values() if v is not None])
    logger.info(f"CONTINUATION TRADING ENGINE: Monitoring with {vah_count} VAH levels")

    try:
        # Run the trading cycle
        data_streamer.run()
    except KeyboardInterrupt:
        logger.info("CONTINUATION TRADING ENGINE: Stopped by user")
    finally:
        # Restore original handler if needed
        data_streamer.tick_handler = original_handler


def get_continuation_trading_summary(stocks: Dict[str, 'ContinuationStockState'],
                                   vah_dict: Dict[str, float]) -> Dict:
    """
    Get continuation trading execution summary

    Args:
        stocks: All stocks after trading
        vah_dict: VAH values used for trading

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
        'vah_levels_used': len(vah_dict),
        'positions': [{
            'symbol': s.symbol,
            'entry_price': s.entry_price,
            'exit_price': s.exit_price,
            'vah_level': vah_dict.get(s.symbol),
            'pnl': s.pnl,
            'entry_time': s.entry_time.isoformat() if s.entry_time else None,
            'exit_time': s.exit_time.isoformat() if s.exit_time else None
        } for s in entered_positions]
    }


def validate_vah_trading_setup(stocks: Dict[str, 'ContinuationStockState'],
                              vah_dict: Dict[str, float]) -> Dict[str, bool]:
    """
    Validate that VAH trading setup is correct

    Args:
        stocks: Dict of stocks
        vah_dict: Dict of VAH values

    Returns:
        Dict of validation results
    """
    validation_results = {}

    for stock in stocks.values():
        symbol = stock.symbol
        vah = vah_dict.get(symbol)

        # Check if continuation stock has VAH
        if stock.situation == 'continuation':
            has_vah = vah is not None and isinstance(vah, (int, float)) and vah > 0
            validation_results[symbol] = has_vah

            if not has_vah:
                logger.warning(f"VAH VALIDATION: {symbol} missing VAH level (situation: {stock.situation})")
        else:
            # Non-continuation stocks don't need VAH
            validation_results[symbol] = True

    return validation_results


# Test function for development
def test_continuation_trading_engine():
    """Test function for continuation trading engine module"""
    print("Testing continuation trading engine module...")

    # Mock VAH data
    mock_vah_dict = {
        'RELIANCE': 2450.50,
        'TCS': 3200.75,
        'INFY': 1650.25
    }

    print(f"Mock VAH data: {mock_vah_dict}")

    # Test validation
    validation = validate_vah_trading_setup({}, mock_vah_dict)
    print(f"VAH validation: {validation}")

    print("Continuation trading engine module test completed")


if __name__ == "__main__":
    test_continuation_trading_engine()
