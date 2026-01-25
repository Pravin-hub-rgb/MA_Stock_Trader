#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Continuation VAH Calculation Module
Handles Volume Area Histogram (VAH) calculations for continuation trading
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def calculate_vah_for_continuation_stocks(symbols: List[str],
                                        volume_profile_calculator: 'VolumeProfileCalculator') -> Dict[str, float]:
    """
    Calculate VAH (Volume Area Histogram) for continuation stocks

    Args:
        symbols: List of stock symbols to calculate VAH for
        volume_profile_calculator: The volume profile calculator instance

    Returns:
        Dict mapping symbol -> VAH value
    """
    logger.info(f"VAH CALCULATION: Starting for {len(symbols)} continuation stocks")

    vah_dict = {}

    if not symbols:
        logger.warning("VAH CALCULATION: No continuation symbols provided")
        return vah_dict

    try:
        # Calculate VAH using the volume profile calculator
        result = volume_profile_calculator.calculate_vah_for_stocks(symbols)
        vah_dict = result if result else {}

        logger.info(f"VAH CALCULATION: Successfully calculated for {len(vah_dict)} stocks")

        return vah_dict

    except Exception as e:
        logger.error(f"VAH CALCULATION: Error during calculation: {e}")
        return {}


def save_vah_results_to_file(vah_dict: Dict[str, float],
                           mode: str = 'continuation') -> bool:
    """
    Save VAH calculation results to vah_results.json for frontend display

    Args:
        vah_dict: Dict of symbol -> VAH values
        mode: Trading mode (continuation, reversal, etc.)

    Returns:
        bool: True if saved successfully, False otherwise
    """
    if not vah_dict:
        logger.warning("VAH SAVE: No VAH data to save")
        return False

    try:
        vah_results = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode,
            'results': vah_dict,
            'summary': f"{len(vah_dict)} stocks calculated"
        }

        with open('vah_results.json', 'w') as f:
            json.dump(vah_results, f, indent=2)

        logger.info(f"VAH SAVE: Results saved to vah_results.json for {len(vah_dict)} stocks")
        return True

    except Exception as e:
        logger.error(f"VAH SAVE: Error saving results: {e}")
        return False


def print_vah_results(vah_dict: Dict[str, float]) -> None:
    """
    Print VAH calculation results for UI visibility

    Args:
        vah_dict: Dict of symbol -> VAH values
    """
    if not vah_dict:
        print("VAH CALCULATION RESULTS: No results to display")
        return

    print("VAH CALCULATION RESULTS:")
    for symbol, vah in vah_dict.items():
        print(f"[OK] {symbol}: Upper Range (VAH) = Rs{vah:.2f}")
    print(f"Summary: {len(vah_dict)} stocks successfully calculated")


def get_vah_for_symbol(symbol: str, vah_dict: Dict[str, float]) -> Optional[float]:
    """
    Get VAH value for a specific symbol

    Args:
        symbol: Stock symbol
        vah_dict: Dict of symbol -> VAH values

    Returns:
        VAH value or None if not found
    """
    return vah_dict.get(symbol)


def validate_vah_data(vah_dict: Dict[str, float]) -> Dict[str, bool]:
    """
    Validate VAH data for reasonableness

    Args:
        vah_dict: Dict of symbol -> VAH values

    Returns:
        Dict of symbol -> validation result
    """
    validation_results = {}

    for symbol, vah in vah_dict.items():
        # Basic validation: VAH should be positive and reasonable
        is_valid = isinstance(vah, (int, float)) and vah > 0 and vah < 100000  # Reasonable price range
        validation_results[symbol] = is_valid

        if not is_valid:
            logger.warning(f"VAH VALIDATION: Invalid VAH value for {symbol}: {vah}")

    return validation_results


# Test function for development
def test_vah_calculation():
    """Test function for VAH calculation module"""
    print("Testing VAH calculation module...")

    # Mock test data
    test_symbols = ['RELIANCE', 'TCS', 'INFY']
    mock_vah_dict = {
        'RELIANCE': 2450.50,
        'TCS': 3200.75,
        'INFY': 1650.25
    }

    print(f"Mock VAH data: {mock_vah_dict}")

    # Test save functionality
    if save_vah_results_to_file(mock_vah_dict, 'test'):
        print("✅ VAH save test passed")
    else:
        print("❌ VAH save test failed")

    # Test print functionality
    print_vah_results(mock_vah_dict)

    # Test validation
    validation = validate_vah_data(mock_vah_dict)
    print(f"Validation results: {validation}")

    print("VAH calculation module test completed")


if __name__ == "__main__":
    test_vah_calculation()
