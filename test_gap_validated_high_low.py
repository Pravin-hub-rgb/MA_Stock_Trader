#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify high/low tracking for gap-validated stocks
Simulates the exact scenario where gap-validated stocks should update high/low properly
"""

import time
import random
from datetime import datetime

class TestGapValidatedStock:
    """Test stock that simulates gap-validated stock behavior"""
    
    def __init__(self, symbol: str, opening_price: float, previous_close: float):
        self.symbol = symbol
        self.open_price = opening_price
        self.previous_close = previous_close
        self.current_price = opening_price
        self.daily_high = opening_price
        self.daily_low = opening_price
        self.last_update = None
        self.gap_validated = False
        self.is_active = True
        self.is_subscribed = True
        
        # Calculate gap
        gap_pct = ((opening_price - previous_close) / previous_close) * 100
        print(f"=== INITIALIZING {symbol} ===")
        print(f"Previous Close: Rs{previous_close:.2f}")
        print(f"Opening Price:  Rs{opening_price:.2f}")
        print(f"Gap:           {gap_pct:+.2f}%")
        
        # Validate gap (continuation: gap > 0.5%)
        if gap_pct > 0.5:
            self.gap_validated = True
            print(f"✅ GAP VALIDATED: {gap_pct:.2f}% > 0.5%")
        else:
            self.gap_validated = False
            print(f"❌ GAP FAILED: {gap_pct:.2f}% <= 0.5%")
        
        print(f"Initial High: Rs{self.daily_high:.2f}")
        print(f"Initial Low:  Rs{self.daily_low:.2f}")
        print()

    def update_price(self, price: float, timestamp: datetime):
        """Update price and track high/low - same logic as live bot"""
        self.current_price = price
        self.last_update = timestamp
        
        # Track high updates
        if price > self.daily_high:
            old_high = self.daily_high
            self.daily_high = price
            print(f"📈 HIGH UPDATED: {self.symbol} {old_high:.2f} → {price:.2f} ({price - old_high:+.2f})")
        
        # Track low updates  
        if price < self.daily_low:
            old_low = self.daily_low
            self.daily_low = price
            print(f"📉 LOW UPDATED: {self.symbol} {old_low:.2f} → {price:.2f} ({price - old_low:+.2f})")
        
        # Show current status
        gap_from_open = ((price - self.open_price) / self.open_price) * 100
        print(f"   {self.symbol}: Price={price:.2f}, High={self.daily_high:.2f}, Low={self.daily_low:.2f}, Gap={gap_from_open:+.2f}%")

    def get_status(self):
        """Get final status - same as live bot"""
        gap_from_open = ((self.daily_low - self.open_price) / self.open_price) * 100
        return {
            'symbol': self.symbol,
            'previous_close': self.previous_close,
            'open_price': self.open_price,
            'current_price': self.current_price,
            'daily_high': self.daily_high,
            'daily_low': self.daily_low,
            'gap_from_open': gap_from_open,
            'gap_validated': self.gap_validated
        }

def simulate_gap_validated_scenario():
    """Test scenario with gap-validated stocks that should update high/low"""
    
    print("🧪 TESTING GAP-VALIDATED STOCKS HIGH/LOW TRACKING")
    print("=" * 60)
    print("This simulates gap-validated stocks that should continue receiving ticks")
    print("and updating high/low values properly")
    print()
    
    # Test stocks with different gap scenarios
    test_stocks = [
        # Gap-validated stocks (should continue monitoring)
        ("ROSSTECH", 730.00, 725.00),    # Gap: +0.69% (validated)
        ("ADANIPOWER", 149.20, 148.00),  # Gap: +0.81% (validated)
        ("ANGELONE", 2709.00, 2690.00),  # Gap: +0.71% (validated)
        
        # Gap-failed stocks (should be unsubscribed)
        ("ELECON", 444.70, 445.00),      # Gap: -0.07% (failed)
        ("TATASTEEL", 150.00, 151.00),   # Gap: -0.66% (failed)
    ]
    
    gap_validated_stocks = []
    gap_failed_stocks = []
    
    # Initialize all stocks
    for symbol, opening_price, previous_close in test_stocks:
        stock = TestGapValidatedStock(symbol, opening_price, previous_close)
        
        if stock.gap_validated:
            gap_validated_stocks.append(stock)
        else:
            gap_failed_stocks.append(stock)
    
    print(f"📊 INITIAL STATUS:")
    print(f"   Gap-validated stocks: {len(gap_validated_stocks)}")
    print(f"   Gap-failed stocks:    {len(gap_failed_stocks)}")
    print()
    
    # Simulate Phase 1: Unsubscribe gap-failed stocks
    print("=== PHASE 1: UNSUBSCRIBING GAP-FAILED STOCKS ===")
    for stock in gap_failed_stocks:
        stock.is_active = False
        stock.is_subscribed = False
        print(f"❌ UNSUBSCRIBED: {stock.symbol} (gap failed)")
    print()
    
    # Simulate monitoring window for gap-validated stocks only
    print("=== MONITORING WINDOW: GAP-VALIDATED STOCKS ONLY ===")
    print("Simulating 60 seconds of price movement for gap-validated stocks...")
    
    for stock in gap_validated_stocks:
        print(f"\n🚀 MONITORING {stock.symbol} (Gap-validated)")
        print("-" * 40)
        
        # Simulate price movement for gap-validated stock
        prices = simulate_price_movement(stock.open_price, duration_seconds=30, tick_interval=1.0)
        
        # Process each price tick (only for gap-validated stocks)
        for i, price in enumerate(prices):
            timestamp = datetime.now()
            stock.update_price(price, timestamp)
            
            # Show progress
            if (i + 1) % 5 == 0:
                print(f"   Progress: {i + 1}/{len(prices)} ticks processed")
        
        # Final status for this stock
        print(f"\n🏁 FINAL STATUS FOR {stock.symbol}:")
        status = stock.get_status()
        print(f"   Previous Close: Rs{status['previous_close']:.2f}")
        print(f"   Opening Price:  Rs{status['open_price']:.2f}")
        print(f"   Final Price:    Rs{status['current_price']:.2f}")
        print(f"   Daily High:     Rs{status['daily_high']:.2f}")
        print(f"   Daily Low:      Rs{status['daily_low']:.2f}")
        
        # Calculate low violation (same logic as live bot)
        low_gap = status['gap_from_open']
        low_violation_threshold = -1.0  # 1% below open
        
        print(f"   Low Gap:        {low_gap:+.2f}%")
        print(f"   Violation Thresh: {low_violation_threshold:+.2f}%")
        
        if low_gap < low_violation_threshold:
            print(f"   ❌ LOW VIOLATION: {low_gap:.2f}% < {low_violation_threshold:.2f}%")
        else:
            print(f"   ✅ LOW PASSED: {low_gap:.2f}% >= {low_violation_threshold:.2f}%")
        
        print()
        print(f"📊 SUMMARY: {stock.symbol} had {len(prices)} price updates")
        print(f"   High changed: {status['daily_high'] != status['open_price']}")
        print(f"   Low changed:  {status['daily_low'] != status['open_price']}")
        print()

def simulate_price_movement(base_price: float, duration_seconds: int = 30, tick_interval: float = 1.0):
    """Simulate realistic price movement"""
    prices = []
    current_price = base_price
    
    for i in range(int(duration_seconds / tick_interval)):
        # Random walk simulation
        change_pct = random.uniform(-0.005, 0.005)  # ±0.5%
        current_price = current_price * (1 + change_pct)
        prices.append(round(current_price, 2))
    
    return prices

if __name__ == "__main__":
    print("🎯 GAP-VALIDATED STOCKS HIGH/LOW TRACKING TEST")
    print("Testing the exact same logic used in continuation bot")
    print()
    
    # Run the test
    simulate_gap_validated_scenario()
    
    print("✅ TEST COMPLETE")
    print()
    print("EXPECTED BEHAVIOR IN LIVE BOT:")
    print("1. Gap-failed stocks should be unsubscribed immediately (disappear from logs)")
    print("2. Gap-validated stocks should continue receiving ticks")
    print("3. Gap-validated stocks should show updated high/low values")
    print("4. Low violation check should use actual low, not opening price")
    print()
    print("If this test works but live bot doesn't, the issue is:")
    print("- Gap-failed stocks not being unsubscribed properly")
    print("- OHLC data not being processed correctly")
    print("- Timing issue with when update_price() is called")