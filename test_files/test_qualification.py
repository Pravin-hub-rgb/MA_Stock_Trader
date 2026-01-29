#!/usr/bin/env python3
"""
Test Stock Qualification Logic
Simulates ticks to test the qualification and entry logic
"""

import sys
import os
from datetime import datetime
import pytz

# Add src to path
sys.path.append('src')
sys.path.append('src/trading/live_trading')

def test_qualification_logic():
    """Test the stock qualification and entry logic"""

    print("🧪 TESTING STOCK QUALIFICATION LOGIC")
    print("=" * 50)

    from stock_monitor import StockMonitor
    from rule_engine import RuleEngine
    from selection_engine import SelectionEngine
    from paper_trader import PaperTrader

    # Create components
    monitor = StockMonitor()
    selection_engine = SelectionEngine()
    paper_trader = PaperTrader()

    IST = pytz.timezone('Asia/Kolkata')

    # Test stocks with known previous closes
    test_stocks = [
        ('BSE', 'NSE_EQ|INE118H01025', 2706.30),
        ('INFY', 'NSE_EQ|INE009A01021', 1639.00),
        ('TCS', 'NSE_EQ|INE467B01029', 3255.80),
    ]

    print("📋 Adding test stocks...")
    for symbol, instrument_key, prev_close in test_stocks:
        monitor.add_stock(symbol, instrument_key, prev_close)
        print(f"   ✅ {symbol}: Previous close ₹{prev_close:.2f}")

    print("\n📊 Simulating market open ticks...")

    # Simulate opening ticks (what would happen at 9:15)
    opening_prices = {
        'BSE': 2780.00,    # +2.7% gap up (should qualify)
        'INFY': 1630.00,   # -0.6% gap down (should reject)
        'TCS': 3240.00,    # -0.5% gap down (should reject)
    }

    qualified_count = 0
    for symbol, instrument_key, prev_close in test_stocks:
        if symbol in opening_prices:
            price = opening_prices[symbol]
            timestamp = datetime.now(IST)

            print(f"\n📈 First tick for {symbol}: ₹{price:.2f}")

            # Process the tick (this sets opening price and validates gap)
            monitor.process_tick(instrument_key, symbol, price, timestamp)

            stock = monitor.stocks[instrument_key]
            if stock.gap_up_validated:
                print(f"   ✅ QUALIFIED: Gap up {((price-prev_close)/prev_close*100):+.1f}%")
                qualified_count += 1
            else:
                print(f"   ❌ REJECTED: Gap validation failed")
                print(f"      Reason: {stock.rejection_reason}")

    print(f"\n🎯 Qualification Summary: {qualified_count} stocks qualified")

    # Simulate some price movement during confirmation window (for low violation check)
    print("\n⚖️ Simulating price movement during confirmation window...")
    # BSE stays above the 1% low violation threshold
    monitor.process_tick('NSE_EQ|INE118H01025', 'BSE', 2775.00, datetime.now(IST))  # Still above 1% threshold
    monitor.process_tick('NSE_EQ|INE118H01025', 'BSE', 2778.00, datetime.now(IST))  # Still above 1% threshold

    # Check violations (manually for BSE since time check won't work in test)
    bse_stock = monitor.stocks['NSE_EQ|INE118H01025']
    if bse_stock.check_low_violation():
        print("   ✅ BSE passed low violation check")
    else:
        print("   ❌ BSE failed low violation check")

    # Prepare entries for qualified stocks
    print("\n🎯 Preparing entry levels...")
    monitor.prepare_entries()

    qualified_stocks = monitor.get_qualified_stocks()
    selected_stocks = selection_engine.select_stocks(qualified_stocks)

    print(f"Qualified stocks: {len(qualified_stocks)}")
    print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

    for stock in selected_stocks:
        stock.entry_ready = True
        print(f"🎯 Ready to trade: {stock.symbol}")
        print(f"   📈 Gap: ₹{stock.previous_close:.2f} → ₹{stock.open_price:.2f} ({((stock.open_price-stock.previous_close)/stock.previous_close*100):+.1f}%)")
        print(f"   🎯 Entry: ₹{stock.entry_high:.2f}, SL: ₹{stock.entry_sl:.2f}")

    # Simulate entry signal
    print("\n💰 Simulating entry signal...")

    # Simulate a tick that breaks the entry level
    entry_price = 2785.00  # Above entry high of 2780
    timestamp = datetime.now(IST)

    print(f"📈 Price update: BSE ₹{entry_price:.2f}")

    # Process the tick
    monitor.process_tick('NSE_EQ|INE118H01025', 'BSE', entry_price, timestamp)

    # Check for entry signals
    entry_signals = monitor.check_entry_signals()
    for stock in entry_signals:
        print(f"🎯 ENTRY SIGNAL TRIGGERED: {stock.symbol} at ₹{entry_price:.2f}")
        print(f"💰 EXECUTING ENTRY: {stock.symbol} at ₹{entry_price:.2f}")
        print(f"   Target: ₹{stock.entry_high:.2f}, SL: ₹{stock.entry_sl:.2f}")

        # Execute entry
        stock.enter_position(entry_price, timestamp)
        paper_trader.log_entry(stock, entry_price, timestamp)
        print(f"✅ ENTRY EXECUTED: {stock.symbol} at ₹{entry_price:.2f}")

    # Show position status
    for stock in monitor.stocks.values():
        if stock.entered:
            pnl = (stock.current_price - stock.entry_price) / stock.entry_price * 100
            print(f"\n📊 POSITION STATUS: {stock.symbol}")
            print(f"   Entry: ₹{stock.entry_price:.2f}")
            print(f"   Current: ₹{stock.current_price:.2f}")
            print(f"   P&L: {pnl:+.2f}%")

    # Cleanup
    summary = monitor.get_summary()
    paper_trader.log_session_summary(summary)
    paper_trader.export_trades_csv()
    paper_trader.close()

    print(f"\n🎉 TEST COMPLETED!")
    print(f"Session Summary: {summary}")

if __name__ == "__main__":
    test_qualification_logic()