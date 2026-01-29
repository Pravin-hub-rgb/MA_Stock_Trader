#!/usr/bin/env python3
"""
Test script for extended reversal scanner (3-15 days with green_days <= 3 cap)
"""

import sys
import os
sys.path.append('src')

import pandas as pd
from src.scanner.reversal_analyzer import ReversalAnalyzer

def test_extended_pattern_rules():
    """Test the new pattern rules for periods 3-15"""
    print("🧪 Testing Extended Reversal Pattern Rules (3-15 days)")
    print("=" * 60)

    analyzer = ReversalAnalyzer(None, {'min_decline_percent': 0.13})

    # Test data with all red days (first day red)
    data = pd.DataFrame({
        'open': [100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30],
        'close': [95, 90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 25],
        'volume': [2000000] * 15
    })

    print("Test Data: All red days (declining), first day is red")
    print()

    for period in range(3, 16):
        if len(data) >= period:
            period_data = data.tail(period)
            red_days = sum(1 for _, row in period_data.iterrows() if row['close'] < row['open'])
            green_days = period - red_days

            result = analyzer._check_pattern_logic(red_days, green_days, period, period_data)
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"Period {period}: {red_days} red, {green_days} green → {status}")

    print()

def test_green_day_cap():
    """Test that green_days <= 3 for periods 8-15"""
    print("🧪 Testing Green Day Cap (≤3 for periods 8-15)")
    print("=" * 60)

    analyzer = ReversalAnalyzer(None, {'min_decline_percent': 0.13})

    # Test cases with varying green days
    test_cases = [
        (10, 7, 3),  # 10 days: 7 red, 3 green (should pass)
        (10, 6, 4),  # 10 days: 6 red, 4 green (should fail)
        (12, 9, 3),  # 12 days: 9 red, 3 green (should pass)
        (12, 8, 4),  # 12 days: 8 red, 4 green (should fail)
        (15, 12, 3), # 15 days: 12 red, 3 green (should pass)
        (15, 11, 4), # 15 days: 11 red, 4 green (should fail)
    ]

    for period, red_days, green_days in test_cases:
        # Create test data (first day red)
        data = pd.DataFrame({
            'open': [100] * period,
            'close': [99] * period,  # All red by default
            'volume': [2000000] * period
        })

        # Make some days green
        for i in range(green_days):
            data.loc[period - 1 - i, 'close'] = 101  # Close > Open = green

        period_data = data
        result = analyzer._check_pattern_logic(red_days, green_days, period, period_data)
        status = "✅ PASS" if result else "❌ FAIL"
        expected = "PASS" if green_days <= 3 else "FAIL"
        print(f"Period {period}: {red_days} red, {green_days} green → {status} (expected {expected})")

    print()

def test_first_day_must_be_red():
    """Test that first day of period must be red"""
    print("🧪 Testing First Day Must Be Red Rule")
    print("=" * 60)

    analyzer = ReversalAnalyzer(None, {'min_decline_percent': 0.13})

    # Test data where first day of period is green (should fail)
    # For period=3, first day is data.iloc[-3] (third from end, index 2)
    data_green_first = pd.DataFrame({
        'open': [90, 95, 100, 95, 90],
        'close': [95, 90, 105, 90, 85],  # Index 2: close=105 > open=100 = green
        'volume': [2000000] * 5
    })

    # Test data where first day is red (should pass for period 3)
    data_red_first = pd.DataFrame({
        'open': [100, 95, 90, 85, 80],  # First day: open=100, close=95 (red)
        'close': [95, 90, 85, 80, 75],
        'volume': [2000000] * 5
    })

    test_cases = [
        ("Green first day", data_green_first, False),
        ("Red first day", data_red_first, True),
    ]

    for desc, test_data, should_pass in test_cases:
        period = 3
        period_data = test_data.tail(period)
        red_days = sum(1 for _, row in period_data.iterrows() if row['close'] < row['open'])
        green_days = period - red_days

        result = analyzer._check_pattern_logic(red_days, green_days, period, period_data)
        status = "✅ PASS" if result else "❌ FAIL"
        expected = "PASS" if should_pass else "FAIL"
        print(f"{desc}: {red_days} red, {green_days} green → {status} (expected {expected})")

    print()

if __name__ == "__main__":
    test_extended_pattern_rules()
    test_green_day_cap()
    test_first_day_must_be_red()
    print("🎉 All extended reversal tests completed!")
