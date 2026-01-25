#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Gap Validation Module
Handles gap calculation and Phase 1 rejection logic for reversal stocks
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def validate_gaps_after_opening_prices(stocks: Dict[str, 'ReversalStockState'],
                                     opening_prices: Dict[str, float]) -> List['ReversalStockState']:
    """
    Phase 1: Gap validation and initial rejection logic

    Args:
        stocks: Dict of instrument_key -> ReversalStockState
        opening_prices: Dict of symbol -> opening_price

    Returns:
        List of qualified stocks (passed gap validation)
    """
    qualified_stocks = []
    rejected_stocks = []

    logger.info("PHASE 1: Starting gap validation for reversal stocks...")

    for instrument_key, stock in stocks.items():
        symbol = stock.symbol

        # Check if we have opening price for this stock
        if symbol not in opening_prices:
            # Reject stocks with missing opening prices
            stock.reject(f"No opening price data available")
            rejected_stocks.append(stock)
            logger.warning(f"❌ {symbol}: REJECTED - No opening price data available")
            continue

        open_price = opening_prices[symbol]

        # Set opening price and validate gap
        stock.set_open_price(open_price)
        stock.validate_gap()

        # Check if stock passed gap validation
        if stock.is_active:
            qualified_stocks.append(stock)
            gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close * 100)
            logger.info(f"✅ {symbol}: Gap validated ({gap_pct:+.1f}%) - QUALIFIED")
        else:
            rejected_stocks.append(stock)
            logger.info(f"❌ {symbol}: REJECTED - {stock.rejection_reason}")

    # Summary logging
    logger.info(f"GAP VALIDATION COMPLETE: {len(qualified_stocks)} qualified, {len(rejected_stocks)} rejected")

    if qualified_stocks:
        logger.info("QUALIFIED STOCKS:")
        for stock in qualified_stocks:
            gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close * 100)
            candidate_type = stock.get_candidate_type()
            logger.info(f"   {stock.symbol}: {candidate_type} - Gap: {gap_pct:+.1f}%")

    if rejected_stocks:
        logger.info("REJECTED STOCKS:")
        for stock in rejected_stocks:
            logger.info(f"   {stock.symbol}: {stock.rejection_reason}")

    return qualified_stocks


def get_gap_validation_summary(stocks: Dict[str, 'ReversalStockState']) -> Dict:
    """
    Get summary of gap validation results

    Args:
        stocks: Dict of instrument_key -> ReversalStockState

    Returns:
        Dict with validation summary
    """
    total_stocks = len(stocks)
    qualified = [s for s in stocks.values() if s.is_active and s.gap_validated]
    rejected = [s for s in stocks.values() if not s.is_active]

    return {
        'total_stocks': total_stocks,
        'qualified_count': len(qualified),
        'rejected_count': len(rejected),
        'qualified_stocks': [s.symbol for s in qualified],
        'rejected_stocks': [{'symbol': s.symbol, 'reason': s.rejection_reason} for s in rejected]
    }


# Test function for development
def test_gap_validation():
    """Test function for gap validation module"""
    print("Testing gap validation module...")

    # This would be used for unit testing
    # Mock stocks and opening prices would be created here

    print("Gap validation module test completed")


if __name__ == "__main__":
    test_gap_validation()
