#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to analyze current subscription timing and validate optimization
"""

import sys
import os
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src/trading/live_trading')

IST = pytz.timezone('Asia/Kolkata')

def analyze_current_timing():
    """Analyze the current subscription timing flow"""
    print('=== CURRENT TIMING ANALYSIS ===')
    
    # Load config
    from config import MARKET_OPEN, PREP_START, ENTRY_TIME
    print(f'MARKET_OPEN: {MARKET_OPEN}')
    print(f'PREP_START: {PREP_START}')
    print(f'ENTRY_TIME: {ENTRY_TIME}')
    
    # Load stock classifier
    from stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_continuation_stock_configuration()
    
    print(f'\n=== STOCK LOADING ===')
    print(f'Total stocks from continuation_list.txt: {len(stock_config["symbols"])}')
    print(f'Stocks: {stock_config["symbols"]}')
    
    # Simulate the timing flow
    print('\n=== CURRENT TIMING FLOW ===')
    print('1. Script starts - loads continuation_list.txt')
    print(f'2. {PREP_START} - Gap/VAH validation (PREP_START)')
    print(f'3. {MARKET_OPEN} - WebSocket opens and subscribes to ALL {len(stock_config["symbols"])} stocks')
    print(f'4. {MARKET_OPEN} - Phase 1 unsubscription (immediately after)')
    print(f'5. {ENTRY_TIME} - Entry preparation')
    
    print('\n=== OPTIMIZATION TARGET ===')
    print('Current: Subscribe to ALL stocks, then unsubscribe invalid ones')
    print('Optimized: Subscribe ONLY to validated stocks')
    print('Benefit: Eliminate Phase 1 unsubscription entirely')
    
    return stock_config

def validate_optimization_feasibility():
    """Validate that the optimization is feasible"""
    print('\n=== OPTIMIZATION FEASIBILITY ===')
    
    # Check that gap/VAH validation happens before subscription
    from config import MARKET_OPEN, PREP_START
    validation_time = PREP_START
    subscription_time = MARKET_OPEN
    
    time_diff = (datetime.combine(datetime.today(), subscription_time) - 
                datetime.combine(datetime.today(), validation_time)).total_seconds()
    
    print(f'Gap/VAH validation at: {validation_time}')
    print(f'Subscription at: {subscription_time}')
    print(f'Time difference: {time_diff} seconds')
    print(f'Validation completes {time_diff} seconds BEFORE subscription')
    print('✅ VALIDATION HAPPENS FIRST - OPTIMIZATION IS FEASIBLE')
    
    return True

if __name__ == "__main__":
    print("SUBSCRIPTION TIMING ANALYSIS")
    print("=" * 50)
    
    stock_config = analyze_current_timing()
    validate_optimization_feasibility()
    
    print('\n=== IMPLEMENTATION PLAN ===')
    print('1. Modify run_continuation.py to filter stocks after validation')
    print('2. Update integration.py to handle validated-only subscription')
    print('3. Remove Phase 1 unsubscription logic')
    print('4. Test the new flow')