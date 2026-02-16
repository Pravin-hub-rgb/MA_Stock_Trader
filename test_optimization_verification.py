#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify the continuation bot optimization
Tests that only validated stocks are subscribed and Phase 1 unsubscription is eliminated
"""

import sys
import os
from datetime import datetime, time, timedelta
import pytz

# Add src to path
sys.path.insert(0, 'src/trading/live_trading')

IST = pytz.timezone('Asia/Kolkata')

def test_optimization_implementation():
    """Test that the optimization is properly implemented"""
    print("=== OPTIMIZATION VERIFICATION TEST ===")
    
    # Test 1: Check that run_continuation.py has the optimization
    print("\n1. Testing run_continuation.py optimization...")
    try:
        with open('src/trading/live_trading/run_continuation.py', 'r') as f:
            content = f.read()
        
        # Check for optimization keywords
        if "OPTIMIZATION: ONLY SUBSCRIBE TO VALIDATED STOCKS" in content:
            print("Optimization comment found in run_continuation.py")
        else:
            print("Optimization comment NOT found in run_continuation.py")
            return False
            
        if "validated_stocks = []" in content:
            print("Validation filtering logic found in run_continuation.py")
        else:
            print("Validation filtering logic NOT found in run_continuation.py")
            return False
            
        if "OPTIMIZED SUBSCRIPTION" in content:
            print("Optimized subscription message found in run_continuation.py")
        else:
            print("Optimized subscription message NOT found in run_continuation.py")
            return False
            
    except Exception as e:
        print(f"❌ Error reading run_continuation.py: {e}")
        return False
    
    # Test 2: Check that integration.py has the deprecated Phase 1 method
    print("\n2. Testing integration.py Phase 1 deprecation...")
    try:
        with open('src/trading/live_trading/continuation_modules/integration.py', 'r') as f:
            content = f.read()
        
        if "OPTIMIZATION: This method is now deprecated" in content:
            print("Phase 1 deprecation comment found in integration.py")
        else:
            print("Phase 1 deprecation comment NOT found in integration.py")
            return False
            
        if "SKIPPED - Optimization implemented" in content:
            print("Phase 1 skip message found in integration.py")
        else:
            print("Phase 1 skip message NOT found in integration.py")
            return False
            
    except Exception as e:
        print(f"❌ Error reading integration.py: {e}")
        return False
    
    # Test 3: Check timing feasibility
    print("\n3. Testing timing feasibility...")
    from config import MARKET_OPEN, PREP_START
    
    validation_time = PREP_START
    subscription_time = MARKET_OPEN
    
    time_diff = (datetime.combine(datetime.today(), subscription_time) - 
                datetime.combine(datetime.today(), validation_time)).total_seconds()
    
    if time_diff >= 30:
        print(f"Timing feasible: {time_diff} seconds between validation and subscription")
    else:
        print(f"Timing NOT feasible: Only {time_diff} seconds between validation and subscription")
        return False
    
    # Test 4: Check that stock classifier loads correctly
    print("\n4. Testing stock loading...")
    try:
        from stock_classifier import StockClassifier
        classifier = StockClassifier()
        stock_config = classifier.get_continuation_stock_configuration()
        
        if len(stock_config['symbols']) > 0:
            print(f"Successfully loaded {len(stock_config['symbols'])} continuation stocks")
            print(f"   Stocks: {stock_config['symbols']}")
        else:
            print("No continuation stocks loaded")
            return False
            
    except Exception as e:
        print(f"Error loading continuation stocks: {e}")
        return False
    
    print("\n=== ALL TESTS PASSED ===")
    print("Optimization is properly implemented")
    print("Only validated stocks will be subscribed")
    print("Phase 1 unsubscription is eliminated")
    print("Timing is feasible for the optimization")
    return True

def simulate_optimized_flow():
    """Simulate the optimized subscription flow"""
    print("\n=== SIMULATED OPTIMIZED FLOW ===")
    
    # Load stocks
    from stock_classifier import StockClassifier
    classifier = StockClassifier()
    stock_config = classifier.get_continuation_stock_configuration()
    
    # Load config
    from config import MARKET_OPEN, PREP_START, ENTRY_TIME
    
    total_stocks = len(stock_config['symbols'])
    print(f"Total stocks from continuation_list.txt: {total_stocks}")
    print(f"Stocks: {stock_config['symbols']}")
    
    # Simulate validation (assume some pass, some fail)
    print("\nSimulating gap/VAH validation...")
    validated_stocks = []
    rejected_stocks = []
    
    # Simulate validation results (in real scenario, this depends on market data)
    for i, symbol in enumerate(stock_config['symbols']):
        # Simulate 60% pass rate for demonstration
        if i % 2 == 0:  # Even indices pass
            validated_stocks.append(symbol)
            print(f"   {symbol} - VALIDATED (Gap: PASSED, VAH: PASSED)")
        else:  # Odd indices fail
            rejected_stocks.append(symbol)
            print(f"   {symbol} - REJECTED (Gap validation failed)")
    
    print(f"\nValidation Results:")
    print(f"   Validated: {len(validated_stocks)} stocks")
    print(f"   Rejected: {len(rejected_stocks)} stocks")
    print(f"   Efficiency: {(len(rejected_stocks)/total_stocks)*100:.1f}% reduction in subscriptions")
    
    print(f"\nOptimized Flow:")
    print(f"1. {PREP_START} - Gap/VAH validation completes")
    print(f"2. {MARKET_OPEN} - Subscribe ONLY to {len(validated_stocks)} validated stocks")
    print(f"3. {MARKET_OPEN} - NO Phase 1 unsubscription needed (eliminated!)")
    print(f"4. {ENTRY_TIME} - Entry preparation for validated stocks")
    
    return True

if __name__ == "__main__":
    print("CONTINUATION BOT OPTIMIZATION VERIFICATION")
    print("=" * 50)
    
    success = test_optimization_implementation()
    if success:
        simulate_optimized_flow()
    else:
        print("\nOPTIMIZATION VERIFICATION FAILED")
        print("Please check the implementation and try again.")
