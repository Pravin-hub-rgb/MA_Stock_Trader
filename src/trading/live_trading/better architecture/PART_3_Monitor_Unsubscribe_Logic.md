# PART 3: Monitor Unsubscribe Logic Guide

## Overview
This document guides the implementation of dynamic unsubscribe functionality in the `ReversalStockMonitor` class to manage WebSocket subscriptions based on stock states.

---

## 1. Add safe_unsubscribe() Helper Function

**File:** `src/trading/live_trading/run_reversal.py`

**Location:** Add near the top of the file, before run_reversal_bot()

```python
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
            print(f"   ✓ {key}")
        
    except Exception as e:
        print(f"[UNSUBSCRIBE ERROR] Failed to unsubscribe: {e}")
        print(f"[UNSUBSCRIBE ERROR] Continuing with tick filtering for {len(instrument_keys)} stocks")
        
        # Fallback: Mark as unsubscribed in code (filtered in tick handler)
        # The tick handler already checks stock.is_subscribed
```

**Why a helper function?**
- Error handling in one place
- Consistent logging
- Easy to test
- Can add retry logic later if needed

---

## 2. Add Unsubscribe Methods to ReversalStockMonitor

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**Add these methods to the `ReversalStockMonitor` class:**

### Method 1: get_rejected_stocks()

```python
def get_rejected_stocks(self) -> List[str]:
    """
    Get list of rejected stock instrument keys
    
    Returns:
        List of instrument keys for stocks in REJECTED state
    """
    rejected_keys = []
    
    for instrument_key, stock in self.stocks.items():
        if stock.state == StockState.REJECTED and stock.is_subscribed:
            rejected_keys.append(instrument_key)
    
    return rejected_keys
```

### Method 2: get_unselected_stocks()

```python
def get_unselected_stocks(self) -> List[str]:
    """
    Get list of not selected stock instrument keys
    
    Returns:
        List of instrument keys for stocks in NOT_SELECTED state
    """
    unselected_keys = []
    
    for instrument_key, stock in self.stocks.items():
        if stock.state == StockState.NOT_SELECTED and stock.is_subscribed:
            unselected_keys.append(instrument_key)
    
    return unselected_keys
```

### Method 3: get_exited_stocks()

```python
def get_exited_stocks(self) -> List[str]:
    """
    Get list of exited stock instrument keys
    
    Returns:
        List of instrument keys for stocks in EXITED state
    """
    exited_keys = []
    
    for instrument_key, stock in self.stocks.items():
        if stock.state == StockState.EXITED and stock.is_subscribed:
            exited_keys.append(instrument_key)
    
    return exited_keys
```

### Method 4: mark_stocks_unsubscribed()

```python
def mark_stocks_unsubscribed(self, instrument_keys: List[str]):
    """
    Mark stocks as unsubscribed after successful unsubscribe
    
    Args:
        instrument_keys: List of instrument keys that were unsubscribed
    """
    for instrument_key in instrument_keys:
        if instrument_key in self.stocks:
            stock = self.stocks[instrument_key]
            stock.is_subscribed = False
            stock.state = StockState.UNSUBSCRIBED
            logger.info(f"[{stock.symbol}] Marked as UNSUBSCRIBED")
```

---

## 3. Update run_reversal.py Main Flow

**File:** `src/trading/live_trading/run_reversal.py`

### Phase 1: Unsubscribe After Gap Validation (9:14:30)

**Location:** After IEP fetch and gap validation (around line 228)

**Current code:**
```python
if iep_prices:
    print("IEP FETCH COMPLETED SUCCESSFULLY")
    
    # Set opening prices and run gap validation
    for symbol in symbols:
        # ... set opening prices ...
        
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
```

**Add after the gap validation loop:**

```python
    # UNSUBSCRIBE REJECTED STOCKS AFTER GAP VALIDATION
    print("\n=== UNSUBSCRIBING GAP-REJECTED STOCKS ===")
    rejected_after_gap = monitor.get_rejected_stocks()
    
    if rejected_after_gap:
        safe_unsubscribe(data_streamer, rejected_after_gap, "gap_rejected")
        monitor.mark_stocks_unsubscribed(rejected_after_gap)
        print(f"Unsubscribed {len(rejected_after_gap)} gap-rejected stocks")
    else:
        print("No stocks rejected at gap validation")
    
    # Show remaining subscribed stocks
    subscribed_count = sum(1 for s in monitor.stocks.values() if s.is_subscribed)
    print(f"Remaining subscribed stocks: {subscribed_count}")
```

---

### Phase 2: Unsubscribe After Low Violation Check (During 9:15-9:16)

**Location:** In the tick handler or at entry time, we need to check for low violations

**Current approach:** The `check_violations()` method is called in the tick handler

**Update the tick handler to unsubscribe after low violation:**

```python
# In tick_handler_reversal function, add after monitor.process_tick():

# Check for newly rejected stocks (low violation)
rejected_after_low = monitor.get_rejected_stocks()
if rejected_after_low:
    safe_unsubscribe(data_streamer, rejected_after_low, "low_violation")
    monitor.mark_stocks_unsubscribed(rejected_after_low)
```

**Better approach:** Add a dedicated check at entry time (9:16:00)

Add this code block **BEFORE** the "PREPARING ENTRIES" section:

```python
# At entry time, check low violations one final time
print("\n=== CHECKING LOW VIOLATIONS ===")
monitor.check_violations()

# Unsubscribe any stocks that violated low
rejected_after_low = monitor.get_rejected_stocks()
if rejected_after_low:
    safe_unsubscribe(data_streamer, rejected_after_low, "low_violation")
    monitor.mark_stocks_unsubscribed(rejected_after_low)
    print(f"Unsubscribed {len(rejected_after_low)} low-violated stocks")

# Show remaining stocks
subscribed_count = sum(1 for s in monitor.stocks.values() if s.is_subscribed)
print(f"Remaining subscribed stocks: {subscribed_count}")
```

---

### Phase 3: Unsubscribe After Selection (9:16:00)

**Location:** After selection logic (around line 436)

**Current code:**
```python
qualified_stocks = monitor.get_qualified_stocks()
print(f"Qualified stocks: {len(qualified_stocks)}")

selected_stocks = selection_engine.select_stocks(qualified_stocks)
print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

# Mark selected stocks as ready
for stock in selected_stocks:
    stock.entry_ready = True
    print(f"READY to trade: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")
```

**Add after marking selected stocks:**

```python
qualified_stocks = monitor.get_qualified_stocks()
print(f"Qualified stocks: {len(qualified_stocks)}")

selected_stocks = selection_engine.select_stocks(qualified_stocks)
print(f"Selected stocks: {[s.symbol for s in selected_stocks]}")

# Mark selected and non-selected stocks
selected_keys = {stock.instrument_key for stock in selected_stocks}

for stock in qualified_stocks:
    if stock.instrument_key in selected_keys:
        # Selected stock
        stock.mark_selected()
        stock.entry_ready = True
        print(f"READY to trade: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")
    else:
        # Not selected - mark for unsubscribe
        stock.mark_not_selected()

# UNSUBSCRIBE NON-SELECTED STOCKS
print("\n=== UNSUBSCRIBING NON-SELECTED STOCKS ===")
unselected_stocks = monitor.get_unselected_stocks()

if unselected_stocks:
    safe_unsubscribe(data_streamer, unselected_stocks, "not_selected")
    monitor.mark_stocks_unsubscribed(unselected_stocks)
    print(f"Unsubscribed {len(unselected_stocks)} non-selected stocks")
else:
    print("All qualified stocks were selected")

# Show final subscribed stocks
subscribed_count = sum(1 for s in monitor.stocks.values() if s.is_subscribed)
subscribed_symbols = [s.symbol for s in monitor.stocks.values() if s.is_subscribed]
print(f"Final subscribed stocks: {subscribed_count} - {subscribed_symbols}")
```

---

### Phase 4: Unsubscribe After Exit (During Trading)

**Location:** In the tick handler, after processing ticks

**Add this code block at the end of the tick handler:**

```python
def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
    """
    Simplified reversal tick handler
    Delegates all logic to individual stocks
    """
    global global_selected_stocks, global_selected_symbols
    
    # ... existing tick processing code ...
    
    # Check for newly exited stocks and unsubscribe
    exited_stocks = monitor.get_exited_stocks()
    if exited_stocks:
        safe_unsubscribe(data_streamer, exited_stocks, "position_closed")
        monitor.mark_stocks_unsubscribed(exited_stocks)
        
        # Log summary
        for key in exited_stocks:
            stock = monitor.stocks.get(key)
            if stock:
                print(f"[CLOSED] {stock.symbol} - Unsubscribed after exit")
```

---

## 4. Add Subscription Status Logging

**Add a helper method to monitor subscription status:**

```python
def log_subscription_status(monitor):
    """Log current subscription status for all stocks"""
    print("\n=== SUBSCRIPTION STATUS ===")
    
    by_state = {}
    for stock in monitor.stocks.values():
        state_name = stock.state.value
        if state_name not in by_state:
            by_state[state_name] = []
        by_state[state_name].append(stock.symbol)
    
    for state_name, symbols in by_state.items():
        print(f"{state_name.upper()}: {len(symbols)} stocks - {symbols}")
    
    subscribed = [s.symbol for s in monitor.stocks.values() if s.is_subscribed]
    print(f"\nACTIVELY SUBSCRIBED: {len(subscribed)} stocks - {subscribed}")
```

**Use this function after each unsubscribe phase:**

```python
# After gap validation unsubscribe
safe_unsubscribe(data_streamer, rejected_after_gap, "gap_rejected")
monitor.mark_stocks_unsubscribed(rejected_after_gap)
log_subscription_status(monitor)

# After selection unsubscribe
safe_unsubscribe(data_streamer, unselected_stocks, "not_selected")
monitor.mark_stocks_unsubscribed(unselected_stocks)
log_subscription_status(monitor)
```

---

## 5. Handle Data Streamer Initialization

**Make sure data_streamer is accessible in the scope where unsubscribe is called.**

**Current code:**
```python
# Initialize data streamer
data_streamer = SimpleStockStreamer(instrument_keys, stock_symbols)
```

**No changes needed** - data_streamer is already in the correct scope.

**Important:** Make sure `SimpleStockStreamer` has the `unsubscribe()` method.

---

## 6. Update SimpleStockStreamer (if needed)

**File:** `src/trading/live_trading/simple_data_streamer.py`

**Check if unsubscribe method exists:**

```python
class SimpleStockStreamer:
    def __init__(self, instrument_keys, stock_symbols):
        # ... existing code ...
    
    def subscribe(self, instrument_keys, mode='full'):
        # ... existing code ...
    
    def unsubscribe(self, instrument_keys):
        """
        Unsubscribe from specific instruments
        
        Args:
            instrument_keys: List of instrument keys to unsubscribe
        """
        if not self.streamer:
            print("Cannot unsubscribe - streamer not connected")
            return
        
        try:
            self.streamer.unsubscribe(instrument_keys)
            print(f"Unsubscribed from {len(instrument_keys)} instruments")
        except Exception as e:
            print(f"Unsubscribe error: {e}")
            raise
```

**If it doesn't exist, add it.**

---

## 7. Complete Unsubscribe Timeline

Here's the complete timeline with unsubscribe points:

```
8:52:11 - Bot starts, loads 15 stocks
9:14:30 - IEP fetch, gap validation
        → 14 stocks REJECTED (gap invalid)
        → UNSUBSCRIBE 14 stocks
        → 1 stock remains (POONAWALLA)

9:15:00 - Market opens, ticks start
        → Only POONAWALLA receives ticks

9:15:00-9:16:00 - Low violation monitoring
        → If POONAWALLA violates low → UNSUBSCRIBE
        → If passes → Keep subscribed

9:16:00 - Selection phase
        → 1 qualified stock (POONAWALLA)
        → Select top 2 (only 1 available)
        → No unsubscribe needed (all qualified were selected)

9:16:00+ - Entry monitoring
        → POONAWALLA receives ticks
        → Entry triggered
        → Keep subscribed (need exit monitoring)

During trading - Exit monitoring
        → 5% profit → Adjust trailing SL
        → SL hit → Exit position
        → UNSUBSCRIBE POONAWALLA

End - 0 stocks subscribed
```

---

## Testing Checklist

After implementing Part 3, verify:

- [ ] Rejected stocks unsubscribe at 9:14:30
- [ ] Low-violated stocks unsubscribe before entry time
- [ ] Non-selected stocks unsubscribe at 9:16:00
- [ ] Exited stocks unsubscribe after position close
- [ ] safe_unsubscribe() handles errors gracefully
- [ ] Subscription status logs show correct states
- [ ] Unsubscribed stocks don't receive ticks
- [ ] SimpleStockStreamer.unsubscribe() works correctly

---

## Edge Cases to Handle

1. **What if all stocks are rejected?**
   - All 15 unsubscribed at 9:14:30
   - Bot continues running but no ticks received
   - Clean shutdown at end of day

2. **What if unsubscribe API fails?**
   - safe_unsubscribe() catches error
   - Falls back to tick filtering (checks is_subscribed)
   - Continues operation, just less efficient

3. **What if stock exits and re-entry is needed?**
   - Currently: Unsubscribe after exit (can't re-enter)
   - Future: Keep subscribed if slots available (not in current design)

4. **What if multiple stocks exit in same tick?**
   - get_exited_stocks() returns all exited stocks
   - Unsubscribe all in one call
   - No issue

---

## Performance Benefits

**Before (without unsubscribe):**
- 15 stocks × 100 ticks/second = 1500 tick events/second
- All processed even if rejected
- Tick handler checks all stocks on every tick

**After (with unsubscribe):**
- Phase 1: 15 → 1 stock (93% reduction)
- Phase 2: 1 → 1 stock (if passes low check)
- Phase 3: 1 → 1 stock (if selected)
- Phase 4: 1 → 0 stocks (after exit)

**Result:** ~93% reduction in tick processing overhead

---

## Next Steps

After completing Part 3, proceed to:
- **Part 4:** Updated run_reversal.py Main Flow (complete integration)

---

## Questions for Coder

1. Is SimpleStockStreamer.unsubscribe() already implemented?
2. Should we add retry logic if unsubscribe fails?
3. Should we log individual stock unsubscribes or just summary?
4. Need help integrating with existing flow?
