# PART 4: Complete Integration Guide

## Overview
This document provides the complete integration of all parts into the main `run_reversal.py` flow, showing how everything works together.

---

## 1. Complete File Structure

After all changes, these files will be modified:

```
src/trading/live_trading/
├── reversal_stock_monitor.py  (Parts 1 & 2)
│   ├── StockState enum added
│   ├── ReversalStockState updated with state machine
│   ├── process_tick() and state handlers added
│   └── Unsubscribe helper methods added
│
├── run_reversal.py  (Parts 3 & 4)
│   ├── safe_unsubscribe() helper added
│   ├── Tick handler simplified
│   └── Unsubscribe logic at key phases
│
└── simple_data_streamer.py  (if needed)
    └── unsubscribe() method verified/added
```

---

## 2. Complete run_reversal.py Flow

Here's the complete flow with all integration points:

### Section 1: Imports and Helper Functions

**Location:** Top of file (after existing imports)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reversal Trading Bot - API-based Opening Prices
Dedicated bot for OOPS reversal trading using official opening prices from API
"""

import sys
import os
import time as time_module
from datetime import datetime, time, timedelta
import pytz
import psutil
import portalocker

# ... existing imports ...

# Add new imports
from reversal_stock_monitor import StockState  # NEW: Import StockState enum

# ... existing helper functions (kill_duplicate_processes, etc.) ...

def safe_unsubscribe(data_streamer, instrument_keys, reason):
    """
    Safely unsubscribe from instruments with error handling
    
    Args:
        data_streamer: SimpleStockStreamer instance
        instrument_keys: List of instrument keys to unsubscribe
        reason: Reason for unsubscribe (for logging)
    """
    if not instrument_keys:
        return
    
    try:
        data_streamer.unsubscribe(instrument_keys)
        print(f"[UNSUBSCRIBE] Removed {len(instrument_keys)} stocks - Reason: {reason}")
        
        # Log which stocks were unsubscribed
        for key in instrument_keys:
            stock = None
            # Find stock by instrument key to get symbol
            for s in data_streamer.stock_symbols.items():
                if s[0] == key:
                    print(f"   ✓ {s[1]}")
                    break
        
    except Exception as e:
        print(f"[UNSUBSCRIBE ERROR] Failed to unsubscribe: {e}")
        print(f"[UNSUBSCRIBE ERROR] Continuing with tick filtering for {len(instrument_keys)} stocks")

def log_subscription_status(monitor):
    """Log current subscription status for all stocks"""
    print("\n=== SUBSCRIPTION STATUS ===")
    
    by_state = {}
    for stock in monitor.stocks.values():
        state_name = stock.state.value
        if state_name not in by_state:
            by_state[state_name] = []
        by_state[state_name].append(stock.symbol)
    
    for state_name, symbols in sorted(by_state.items()):
        print(f"  {state_name.upper()}: {len(symbols)} stocks - {symbols}")
    
    subscribed = [s.symbol for s in monitor.stocks.values() if s.is_subscribed]
    print(f"\nACTIVELY SUBSCRIBED: {len(subscribed)} stocks - {subscribed}")
    print("=" * 50)
```

---

### Section 2: Tick Handler (SIMPLIFIED)

**Location:** Inside run_reversal_bot() function, around line 232

**Replace the entire tick_handler_reversal function with:**

```python
    # Reversal tick handler - simplified with state-based delegation
    def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
        """
        Simplified reversal tick handler
        Delegates all logic to individual stocks based on their state
        """
        # Get stock
        stock = monitor.stocks.get(instrument_key)
        if not stock:
            return
        
        # Early exit for unsubscribed stocks (safety check)
        if not stock.is_subscribed:
            return
        
        # Delegate to stock's own tick processor
        # Stock will handle its own entry/exit logic based on its state
        monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)
        
        # Handle paper trading logs
        # Check if stock just entered (entry_time matches current timestamp)
        if stock.entered and stock.entry_time and abs((stock.entry_time - timestamp).total_seconds()) < 1:
            paper_trader.log_entry(stock, stock.entry_price, timestamp)
            print(f"ENTRY {stock.symbol} entered at Rs{stock.entry_price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
        
        # Check if stock just exited (exit_time matches current timestamp)
        if stock.state == StockState.EXITED and stock.exit_time and abs((stock.exit_time - timestamp).total_seconds()) < 1:
            paper_trader.log_exit(stock, stock.exit_price, timestamp, "Stop Loss Hit")
            print(f"EXIT {stock.symbol} exited at Rs{stock.exit_price:.2f}, PNL: {stock.pnl:+.2f}%")
        
        # Check for newly exited stocks and unsubscribe
        exited_stocks = monitor.get_exited_stocks()
        if exited_stocks:
            safe_unsubscribe(data_streamer, exited_stocks, "position_closed")
            monitor.mark_stocks_unsubscribed(exited_stocks)
            
            # Log summary
            for key in exited_stocks:
                stock_obj = monitor.stocks.get(key)
                if stock_obj:
                    print(f"[CLOSED] {stock_obj.symbol} - Unsubscribed after exit")
```

**Key Points:**
- ✅ No more nested loops
- ✅ No more manual OOPS/Strong Start checking
- ✅ All logic delegated to stock.process_tick()
- ✅ Paper trader integration maintained
- ✅ Automatic unsubscribe after exit

---

### Section 3: IEP Fetch and Gap Validation (PHASE 1 UNSUBSCRIBE)

**Location:** Around line 195 (after IEP fetch)

**Current code ends with gap validation. Add after:**

```python
    # ... existing IEP fetch code ...
    
    if iep_prices:
        print("IEP FETCH COMPLETED SUCCESSFULLY")
        
        # Set opening prices and run gap validation
        for symbol in symbols:
            # Find the clean symbol for IEP lookup
            clean_symbol = symbol.split('-')[0] if '-' in symbol else symbol
            
            if clean_symbol in iep_prices:
                iep_price = iep_prices[clean_symbol]
                # Find stock by symbol
                stock = None
                for s in monitor.stocks.values():
                    if s.symbol == symbol:
                        stock = s
                        break
                
                if stock:
                    stock.set_open_price(iep_price)
                    print(f"Set opening price for {symbol}: Rs{iep_price:.2f}")
                    
                    # Run gap validation immediately (at 9:14:30)
                    if hasattr(stock, 'validate_gap'):
                        stock.validate_gap()
                        if stock.gap_validated:
                            print(f"Gap validated for {symbol}")
                        else:
                            print(f"Gap validation failed for {symbol}")
                else:
                    print(f"Stock not found for symbol: {symbol}")
            else:
                print(f"IEP price not found for symbol: {symbol}")
        
        # NEW: PHASE 1 UNSUBSCRIBE - GAP REJECTED STOCKS
        print("\n" + "=" * 55)
        print("PHASE 1: UNSUBSCRIBING GAP-REJECTED STOCKS")
        print("=" * 55)
        
        rejected_after_gap = monitor.get_rejected_stocks()
        
        if rejected_after_gap:
            safe_unsubscribe(data_streamer, rejected_after_gap, "gap_rejected")
            monitor.mark_stocks_unsubscribed(rejected_after_gap)
            print(f"\nUnsubscribed {len(rejected_after_gap)} gap-rejected stocks")
        else:
            print("\nNo stocks rejected at gap validation")
        
        # Show subscription status
        log_subscription_status(monitor)
    
    else:
        print("IEP FETCH FAILED - MANUAL OPENING PRICE CAPTURE REQUIRED")
        print("WARNING: Opening prices will need to be set manually or via alternative method")
```

---

### Section 4: Entry Time Preparation (PHASE 2 & 3 UNSUBSCRIBE)

**Location:** Around line 402 (in the "PREPARING ENTRIES" section)

**Replace the existing entry preparation code:**

```python
            # Prepare entries and select stocks
            print("\n=== PREPARING ENTRIES ===")
            
            # NEW: PHASE 2 - CHECK LOW VIOLATIONS AND UNSUBSCRIBE
            print("\n" + "=" * 55)
            print("PHASE 2: CHECKING LOW VIOLATIONS")
            print("=" * 55)
            
            # Final low violation check before selection
            monitor.check_violations()
            
            # Unsubscribe any stocks that violated low
            rejected_after_low = monitor.get_rejected_stocks()
            if rejected_after_low:
                safe_unsubscribe(data_streamer, rejected_after_low, "low_violation")
                monitor.mark_stocks_unsubscribed(rejected_after_low)
                print(f"Unsubscribed {len(rejected_after_low)} low-violated stocks")
            else:
                print("No low violations detected")
            
            # Show subscription status
            log_subscription_status(monitor)

            # Show current status after all validations
            print("\n=== POST-VALIDATION STATUS ===")
            for stock in monitor.stocks.values():
                if stock.is_subscribed:  # Only show still-subscribed stocks
                    open_status = f"Open: Rs{stock.open_price:.2f}" if stock.open_price else "No opening price"
                    
                    gap_pct = 0.0
                    if stock.open_price and stock.previous_close:
                        gap_pct = ((stock.open_price - stock.previous_close) / stock.previous_close) * 100
                    
                    gap_status = "Gap validated" if stock.gap_validated else f"Gap: {gap_pct:+.1f}%"
                    low_status = "Low checked" if stock.low_violation_checked else "Low not checked"
                    
                    situation_desc = {
                        'reversal_s1': 'Rev-U',
                        'reversal_s2': 'Rev-D',
                        'reversal_vip': 'VIP',
                        'reversal_tertiary': 'Tert'
                    }.get(stock.situation, stock.situation)
                    
                    print(f"   {stock.symbol} ({situation_desc}): {open_status} | {gap_status} | {low_status} | State: {stock.state.value}")

            # Prepare entry levels for qualified stocks
            monitor.prepare_entries()

            # Get qualified and select
            qualified_stocks = monitor.get_qualified_stocks()
            print(f"\nQualified stocks: {len(qualified_stocks)}")

            selected_stocks = selection_engine.select_stocks(qualified_stocks)
            print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

            # NEW: PHASE 3 - MARK SELECTED/UNSELECTED AND UNSUBSCRIBE
            print("\n" + "=" * 55)
            print("PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED")
            print("=" * 55)
            
            # Mark selected and non-selected stocks
            selected_keys = {stock.instrument_key for stock in selected_stocks}

            for stock in qualified_stocks:
                if stock.instrument_key in selected_keys:
                    # Selected stock
                    stock.mark_selected()
                    stock.entry_ready = True
                    print(f"✓ SELECTED: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")
                else:
                    # Not selected - mark for unsubscribe
                    stock.mark_not_selected()
                    print(f"✗ NOT SELECTED: {stock.symbol} (limited to {selection_engine.max_positions} positions)")

            # Unsubscribe non-selected stocks
            unselected_stocks = monitor.get_unselected_stocks()

            if unselected_stocks:
                safe_unsubscribe(data_streamer, unselected_stocks, "not_selected")
                monitor.mark_stocks_unsubscribed(unselected_stocks)
                print(f"\nUnsubscribed {len(unselected_stocks)} non-selected stocks")
            else:
                print("\nAll qualified stocks were selected")

            # Show final subscription status
            log_subscription_status(monitor)

            # Initialize selected_stocks for the tick handler
            global_selected_symbols = {stock.symbol for stock in selected_stocks}

            # Keep monitoring for entries, exits, and trailing stops
            print("\n=== MONITORING FOR ENTRY/EXIT SIGNALS ===")
```

---

### Section 5: Remove Old Entry/Exit Logic

**Location:** After the tick handler definition

**REMOVE these sections from the old code:**

1. **Remove the old entry signal check (lines ~283-289):**
   ```python
   # DELETE THIS - now handled in stock.process_tick()
   entry_signals = monitor.check_entry_signals()
   for stock in entry_signals:
       if stock.symbol in global_selected_symbols:
           print(f"ENTRY {stock.symbol} entry triggered at Rs{price:.2f}, SL placed at Rs{stock.entry_sl:.2f}")
           stock.enter_position(price, timestamp)
           paper_trader.log_entry(stock, price, timestamp)
   ```

2. **Remove the Strong Start loop (lines ~291-303):**
   ```python
   # DELETE THIS - now handled in stock.process_tick()
   for stock in monitor.stocks.values():
       if stock.situation in ['reversal_s1']:
           if reversal_monitor.check_strong_start_trigger(...):
               # ... entry logic ...
   ```

3. **Remove the old trailing stop logic (lines ~306-324):**
   ```python
   # DELETE THIS - now handled in stock._handle_exit_monitoring()
   if current_time >= ENTRY_TIME:
       for stock in monitor.stocks.values():
           if stock.entered and stock.entry_price and stock.current_price:
               profit_pct = (stock.current_price - stock.entry_price) / stock.entry_price
               if profit_pct >= 0.05:
                   # ... trailing stop logic ...
   ```

**All this logic is now handled inside `stock.process_tick()`!**

---

## 3. Update ReversalStockMonitor.process_tick()

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**This was covered in Part 2, but here's the complete version with paper_trader integration:**

```python
def process_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: list = None):
    """Process a price tick for a stock"""
    if instrument_key not in self.stocks:
        return
    
    stock = self.stocks[instrument_key]
    
    # Delegate to stock's own tick processor
    # This handles state-based routing and all entry/exit logic
    stock.process_tick(price, timestamp)
    
    # Set session start if this is the first tick
    if self.session_start_time is None:
        self.session_start_time = timestamp
```

---

## 4. Add Missing Dependencies to Stock Methods

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**The stock's entry check methods need access to reversal_monitor.**

**Option 1: Pass as parameter (Recommended)**

Update the tick handler to pass reversal_monitor:

```python
# In ReversalStockState.process_tick()
def process_tick(self, price: float, timestamp: datetime, reversal_monitor=None):
    """
    Process a tick for THIS stock only
    
    Args:
        price: Current price for THIS stock
        timestamp: Tick timestamp
        reversal_monitor: ReversalMonitor instance for trigger checks
    """
    # Always update price tracking
    self.update_price(price, timestamp)
    
    # Route to state-specific handlers
    if self.state == StockState.MONITORING_ENTRY:
        self._handle_entry_monitoring(price, timestamp, reversal_monitor)
    
    elif self.state == StockState.MONITORING_EXIT:
        self._handle_exit_monitoring(price, timestamp)
```

**Then update the monitor's process_tick:**

```python
def process_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: list = None, reversal_monitor=None):
    """Process a price tick for a stock"""
    if instrument_key not in self.stocks:
        return
    
    stock = self.stocks[instrument_key]
    
    # Delegate to stock's own tick processor with reversal_monitor
    stock.process_tick(price, timestamp, reversal_monitor)
    
    # Set session start if this is the first tick
    if self.session_start_time is None:
        self.session_start_time = timestamp
```

**And update the tick handler call:**

```python
# In tick_handler_reversal
monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list, reversal_monitor)
```

---

## 5. Verify SimpleStockStreamer.unsubscribe()

**File:** `src/trading/live_trading/simple_data_streamer.py`

**Make sure this method exists:**

```python
def unsubscribe(self, instrument_keys):
    """
    Unsubscribe from specific instruments
    
    Args:
        instrument_keys: List of instrument keys to unsubscribe
    """
    if not self.streamer:
        print("Cannot unsubscribe - streamer not connected")
        return
    
    if not instrument_keys:
        return
    
    try:
        self.streamer.unsubscribe(instrument_keys)
        print(f"[DATA STREAM] Unsubscribed from {len(instrument_keys)} instruments")
    except Exception as e:
        print(f"[DATA STREAM ERROR] Unsubscribe failed: {e}")
        raise
```

**If it doesn't exist, add it.**

---

## 6. Complete Integration Checklist

### Files Modified:
- [ ] `reversal_stock_monitor.py` - State machine, process_tick, unsubscribe helpers
- [ ] `run_reversal.py` - Simplified tick handler, unsubscribe phases
- [ ] `simple_data_streamer.py` - Verified unsubscribe() method exists

### Code Added:
- [ ] StockState enum
- [ ] ReversalStockState state transitions
- [ ] ReversalStockState.process_tick() with state routing
- [ ] _handle_entry_monitoring() and _handle_exit_monitoring()
- [ ] _check_oops_entry() and _check_strong_start_entry()
- [ ] Monitor helper methods (get_rejected_stocks, etc.)
- [ ] safe_unsubscribe() helper function
- [ ] log_subscription_status() helper function
- [ ] 4 phases of unsubscribe logic

### Code Removed:
- [ ] Old nested loop for Strong Start (lines 291-303)
- [ ] Old entry signal check loop (lines 283-289)
- [ ] Old trailing stop loop (lines 306-324)
- [ ] Old OOPS manual entry logic (lines 246-256)

### Testing Required:
- [ ] Gap validation triggers unsubscribe
- [ ] Low violation triggers unsubscribe
- [ ] Selection triggers unsubscribe of non-selected
- [ ] Exit triggers unsubscribe
- [ ] OOPS entry uses correct stock's price
- [ ] Strong Start entry uses correct stock's price
- [ ] Trailing SL adjusts at 5% profit
- [ ] Exit triggers at SL hit
- [ ] No cross-contamination between stocks

---

## 7. Expected Behavior After Integration

### Scenario: 15 stocks, only POONAWALLA qualifies

```
[8:52:11 am] Bot starts with 15 stocks
[9:14:30 am] IEP fetch and gap validation
              → 14 stocks rejected (wrong gap)
              → UNSUBSCRIBE 14 stocks
              → 1 stock remains: POONAWALLA
              
              SUBSCRIPTION STATUS:
              REJECTED: 14 stocks - [GODREJPROP, ANANTRAJ, ...]
              GAP_VALIDATED: 1 stock - [POONAWALLA]
              ACTIVELY SUBSCRIBED: 1 stock - [POONAWALLA]

[9:15:00 am] Market opens
              → Only POONAWALLA receives ticks
              
[9:16:00 am] Entry preparation
              → Low violation check: POONAWALLA passes
              → Qualified: 1 stock
              → Selected: 1 stock (POONAWALLA)
              → No unsubscribe needed (all qualified were selected)
              
              SUBSCRIPTION STATUS:
              REJECTED: 14 stocks - [...]
              SELECTED: 1 stock - [POONAWALLA]
              ACTIVELY SUBSCRIBED: 1 stock - [POONAWALLA]

[9:16:XX am] POONAWALLA ticks at 411.80
              → Strong Start conditions met
              → Entry triggered at 411.80 (CORRECT PRICE!)
              → State: MONITORING_EXIT
              
[9:XX:XX am] POONAWALLA moves to 432.40 (5% profit)
              → Trailing SL adjusted to 411.80 (breakeven)
              
[9:XX:XX am] POONAWALLA drops to 411.80
              → SL hit
              → Exit position
              → UNSUBSCRIBE POONAWALLA
              
              SUBSCRIPTION STATUS:
              REJECTED: 14 stocks - [...]
              EXITED: 1 stock - [POONAWALLA]
              ACTIVELY SUBSCRIBED: 0 stocks

End of day: 0 stocks subscribed, clean shutdown
```

---

## 8. Debugging Tips

### If entry price is wrong:
- Check: Is stock using `price` parameter or `stock.current_price`?
- Should use: `price` parameter (passed to process_tick)
- Log: Add print in _check_oops_entry and _check_strong_start_entry

### If unsubscribe doesn't work:
- Check: Does SimpleStockStreamer.unsubscribe() exist?
- Check: Are instrument_keys correct format?
- Check: Is data_streamer connected?
- Log: Add prints in safe_unsubscribe

### If stocks don't enter:
- Check: Stock state (should be MONITORING_ENTRY)
- Check: reversal_monitor trigger conditions
- Check: Is stock subscribed?
- Log: Add prints in _handle_entry_monitoring

### If trailing SL doesn't work:
- Check: Stock state (should be MONITORING_EXIT after entry)
- Check: Profit calculation
- Log: Add prints in _handle_exit_monitoring

---

## 9. Performance Metrics to Track

**Before optimization:**
- Tick events processed: ~1500/second (15 stocks × 100 ticks)
- Stocks looped per tick: 15
- Total loop iterations: ~22,500/second

**After optimization:**
- Tick events received: ~100/second (1 stock × 100 ticks after Phase 1)
- Stocks processed per tick: 1
- Total operations: ~100/second

**Improvement: 225x reduction in processing overhead**

---

## Next Steps

1. **Test in Paper Trading Mode**
   - Run with real market data
   - Verify unsubscribe timing
   - Confirm correct prices used

2. **Monitor Logs**
   - Check subscription status at each phase
   - Verify state transitions
   - Confirm no cross-contamination

3. **Optimize Further (Optional)**
   - Add state validation (prevent invalid transitions)
   - Add retry logic for failed unsubscribes
   - Add performance metrics logging

---

## Questions for Coder

1. Ready to start implementation?
2. Which part should we test first?
3. Need clarification on any section?
4. Should we add more logging for debugging?
