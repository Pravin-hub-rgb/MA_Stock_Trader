#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation Volume Validation Module
Handles volume validation requirements for continuation trading
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def validate_volume_requirements(stocks: Dict[str, 'ContinuationStockState'],
                               volume_baselines: Dict[str, float] = None) -> Dict[str, bool]:
    """
    Validate volume requirements for continuation stocks

    Args:
        stocks: Dict of instrument_key -> ContinuationStockState
        volume_baselines: Optional dict of symbol -> volume baseline

    Returns:
        Dict of symbol -> validation result (True if passes, False if fails)
    """
    logger.info("VOLUME VALIDATION: Starting volume requirement checks")

    validation_results = {}

    for stock in stocks.values():
        if stock.situation != 'continuation':
            # Only validate continuation stocks
            validation_results[stock.symbol] = True
            continue

        # Check if stock has volume validation capability
        if hasattr(stock, 'check_volume_validation'):
            try:
                is_valid = stock.check_volume_validation()
                validation_results[stock.symbol] = is_valid

                if is_valid:
                    logger.info(f"VOLUME VALIDATION: ✅ {stock.symbol} passes volume requirements")
                else:
                    logger.info(f"VOLUME VALIDATION: ❌ {stock.symbol} fails volume requirements - {stock.rejection_reason}")

            except Exception as e:
                logger.error(f"VOLUME VALIDATION: Error checking {stock.symbol}: {e}")
                validation_results[stock.symbol] = False
        else:
            # If stock doesn't have volume validation, assume it passes
            logger.warning(f"VOLUME VALIDATION: {stock.symbol} has no volume validation method")
            validation_results[stock.symbol] = True

    passed_count = sum(1 for result in validation_results.values() if result)
    total_count = len(validation_results)

    logger.info(f"VOLUME VALIDATION: Complete - {passed_count}/{total_count} stocks pass volume requirements")

    return validation_results


def get_volume_validation_summary(stocks: Dict[str, 'ContinuationStockState']) -> Dict:
    """
    Get summary of volume validation results

    Args:
        stocks: Dict of stocks after volume validation

    Returns:
        Dict with validation summary
    """
    total_stocks = len(stocks)
    validated_stocks = [s for s in stocks.values() if hasattr(s, 'volume_validated')]
    passed_stocks = [s for s in stocks.values() if getattr(s, 'volume_validated', False)]

    return {
        'total_stocks': total_stocks,
        'stocks_with_validation': len(validated_stocks),
        'passed_validation': len(passed_stocks),
        'failed_validation': len(validated_stocks) - len(passed_stocks),
        'passed_stocks': [{'symbol': s.symbol, 'volume_validated': s.volume_validated} for s in passed_stocks],
        'failed_stocks': [{'symbol': s.symbol, 'reason': getattr(s, 'rejection_reason', 'Volume validation failed')}
                         for s in validated_stocks if not getattr(s, 'volume_validated', False)]
    }


def check_volume_threshold(symbol: str,
                          current_volume: float,
                          baseline_volume: float,
                          threshold_multiplier: float = 0.8) -> bool:
    """
    Check if current volume meets threshold requirements

    Args:
        symbol: Stock symbol
        current_volume: Current trading volume
        baseline_volume: Baseline volume requirement
        threshold_multiplier: Multiplier for threshold (default 0.8 = 80%)

    Returns:
        True if volume meets threshold, False otherwise
    """
    if baseline_volume <= 0:
        logger.warning(f"VOLUME THRESHOLD: Invalid baseline volume for {symbol}: {baseline_volume}")
        return False

    threshold = baseline_volume * threshold_multiplier
    meets_threshold = current_volume >= threshold

    if meets_threshold:
        logger.info(f"VOLUME THRESHOLD: ✅ {symbol} meets threshold - {current_volume:.0f} >= {threshold:.0f}")
    else:
        logger.info(f"VOLUME THRESHOLD: ❌ {symbol} below threshold - {current_volume:.0f} < {threshold:.0f}")

    return meets_threshold


def update_volume_validation_status(stocks: Dict[str, 'ContinuationStockState'],
                                  validation_results: Dict[str, bool]) -> None:
    """
    Update volume validation status on stock objects

    Args:
        stocks: Dict of stocks to update
        validation_results: Dict of symbol -> validation result
    """
    for stock in stocks.values():
        if stock.symbol in validation_results:
            stock.volume_validated = validation_results[stock.symbol]
            if not validation_results[stock.symbol]:
                stock.rejection_reason = "Volume validation failed"
                stock.is_active = False


# Test function for development
def test_volume_validation():
    """Test function for volume validation module"""
    print("Testing volume validation module...")

    # Mock stock objects
    class MockStock:
        def __init__(self, symbol, situation='continuation'):
            self.symbol = symbol
            self.situation = situation
            self.volume_validated = None
            self.rejection_reason = None
            self.is_active = True

        def check_volume_validation(self):
            # Mock validation logic
            is_valid = self.symbol.startswith('VALID')
            self.volume_validated = is_valid  # Set the attribute
            if not is_valid:
                self.rejection_reason = "Mock validation failed"
            return is_valid

    # Create mock stocks
    mock_stocks = {
        'STOCK1': MockStock('VALID_STOCK1'),
        'STOCK2': MockStock('VALID_STOCK2'),
        'STOCK3': MockStock('INVALID_STOCK'),
        'STOCK4': MockStock('OTHER_STOCK', 'reversal')  # Non-continuation
    }

    # Test validation
    results = validate_volume_requirements(mock_stocks)
    print(f"Validation results: {results}")

    # Update status on stocks
    update_volume_validation_status(mock_stocks, results)

    # Test summary
    summary = get_volume_validation_summary(mock_stocks)
    print(f"Validation summary: {summary}")

    # Test threshold checking
    threshold_result = check_volume_threshold('TEST', 100000, 80000, 0.8)
    print(f"Threshold test: {threshold_result}")

    print("Volume validation module test completed")


if __name__ == "__main__":
    test_volume_validation()
