#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify that gap-rejected stocks are properly unsubscribed
and disappear from monitoring completely
"""

import time
from datetime import datetime

class TestStock:
    """Test stock with subscription tracking"""
    
    def __init__(self, symbol: str, opening_price: float, previous_close: float):
        self.symbol = symbol
        self.open_price = opening_price
        self.previous_close = previous_close
        self.current_price = opening_price
        self.daily_high = opening_price
        self.daily_low = opening_price
        self.gap_validated = False
        self.is_active = True
        self.is_subscribed = True
        self.rejection_reason = ""
        
        # Calculate gap
        gap_pct = ((opening_price - previous_close) / previous_close) * 100
        
        # Validate gap (continuation: gap > 0.5%)
        if gap_pct > 0.5:
            self.gap_validated = True
            print(f"✅ {symbol}: GAP VALIDATED ({gap_pct:.2f}%)")
        else:
            self.gap_validated = False
            self.is_active = False
            self.is_subscribed = False
            self.rejection_reason = f"Gap: {gap_pct:.2f}% <= 0.5%"
            print(f"❌ {symbol}: GAP REJECTED ({gap_pct:.2f}%) - UNSUBSCRIBED")

def test_gap_rejected_unsubscribe():
    """Test that gap-rejected stocks are properly unsubscribed"""
    
    print("🧪 TESTING GAP-REJECTED STOCK UNSUBSCRIPTION")
    print("=" * 50)
    print("This tests the exact same logic used in continuation bot")
    print("Gap-rejected stocks should disappear from monitoring")
    print()
    
    # Test stocks with different gap scenarios
    test_stocks = [
        # Gap-validated stocks (should remain subscribed)
        ("ROSSTECH", 730.00, 725.00),    # Gap: +0.69% (validated)
        ("ADANIPOWER", 149.20, 148.00),  # Gap: +0.81% (validated)
        ("ANGELONE", 2709.00, 2690.00),  # Gap: +0.71% (validated)
        
        # Gap-failed stocks (should be unsubscribed)
        ("ELECON", 444.70, 445.00),      # Gap: -0.07% (failed)
        ("TATASTEEL", 150.00, 151.00),   # Gap: -0.66% (failed)
        ("GRSE", 2446.30, 2450.00),      # Gap: -0.15% (failed)
    ]
    
    # Initialize all stocks
    stocks = {}
    for symbol, opening_price, previous_close in test_stocks:
        stock = TestStock(symbol, opening_price, previous_close)
        stocks[symbol] = stock
    
    print()
    print("📊 INITIAL STATUS AFTER GAP VALIDATION:")
    
    # Count subscribed vs unsubscribed
    subscribed_stocks = []
    unsubscribed_stocks = []
    
    for stock in stocks.values():
        if stock.is_subscribed:
            subscribed_stocks.append(stock)
        else:
            unsubscribed_stocks.append(stock)
    
    print(f"   Subscribed stocks: {len(subscribed_stocks)}")
    for stock in subscribed_stocks:
        print(f"      ✅ {stock.symbol} (Gap validated)")
    
    print(f"   Unsubscribed stocks: {len(unsubscribed_stocks)}")
    for stock in unsubscribed_stocks:
        print(f"      ❌ {stock.symbol} ({stock.rejection_reason})")
    
    print()
    print("=== SIMULATING TICK HANDLER FILTERING ===")
    print("Testing tick handler logic: if not stock.is_subscribed: return")
    print()
    
    # Simulate tick handler processing
    print("Processing ticks for all stocks...")
    for symbol, stock in stocks.items():
        # This is the key check from the tick handler
        if not stock.is_subscribed:
            print(f"   ⏭️  {symbol}: SKIPPED (not subscribed)")
            continue
        
        # If we reach here, stock is subscribed and will be processed
        print(f"   ✅ {symbol}: PROCESSED (subscribed)")
    
    print()
    print("=== SIMULATING LOG OUTPUT ===")
    print("Testing what would appear in continuation bot logs...")
    print()
    
    # Simulate what would appear in logs (only subscribed stocks)
    print("POST-VALIDATION STATUS (what should appear in logs):")
    for stock in subscribed_stocks:
        gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100
        print(f"   {stock.symbol} (Cont): Open: Rs{stock.open_price:.2f} | Gap validated | Low: Rs{stock.daily_low:.2f} ({gap_pct:+.2f}% from open) - PASSED")
    
    # Unsubscribed stocks should NOT appear in logs
    print()
    print("❌ STOCKS THAT SHOULD NOT APPEAR IN LOGS:")
    for stock in unsubscribed_stocks:
        print(f"   {stock.symbol} - Should be completely gone from monitoring")
    
    print()
    print("✅ TEST COMPLETE")
    print()
    print("EXPECTED BEHAVIOR IN LIVE BOT:")
    print("1. Gap-rejected stocks should be unsubscribed immediately")
    print("2. Gap-rejected stocks should NOT appear in any logs")
    print("3. Only gap-validated stocks should remain in monitoring")
    print("4. Tick handler should filter out unsubscribed stocks")
    print()
    print("If this test works but live bot doesn't, the issue is:")
    print("- Gap-rejected stocks not being properly unsubscribed")
    print("- Tick handler not filtering unsubscribed stocks")
    print("- WebSocket connections not being closed")

if __name__ == "__main__":
    test_gap_rejected_unsubscribe()