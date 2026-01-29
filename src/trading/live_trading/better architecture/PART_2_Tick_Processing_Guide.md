# PART 2: Self-Contained Tick Processing Guide

## Overview
This document guides the implementation of per-stock tick processing to eliminate cross-contamination and nested loops. Each stock will process only its own ticks using its own price data.

---

## 1. Add process_tick() Method to ReversalStockState

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**Location:** Add this method to the `ReversalStockState` class

```python
def process_tick(self, price: float, timestamp: datetime):
    """
    Process a tick for THIS stock only
    Routes to appropriate handler based on current state
    
    Args:
        price: Current price for THIS stock
        timestamp: Tick timestamp
    """
    # Always update price tracking regardless of state
    self.update_price(price, timestamp)
    
    # Route to state-specific handlers
    if self.state == StockState.MONITORING_ENTRY:
        self._handle_entry_monitoring(price, timestamp)
    
    elif self.state == StockState.MONITORING_EXIT:
        self._handle_exit_monitoring(price, timestamp)
    
    # Other states don't need tick processing:
    # - INITIALIZED, WAITING_FOR_OPEN: No data yet
    # - GAP_VALIDATED, QUALIFIED, SELECTED: Waiting for entry time
    # - REJECTED, NOT_SELECTED, UNSUBSCRIBED, EXITED: Terminal states
```

**Key Points:**
- Uses `price` parameter which is THIS stock's price only
- State-based routing prevents wrong logic execution
- Always updates price for high/low tracking

---

## 2. Add _handle_entry_monitoring() Method

**Add this private method to ReversalStockState class:**

```python
def _handle_entry_monitoring(self, price: float, timestamp: datetime):
    """
    Handle entry monitoring based on stock situation
    
    Args:
        price: Current price for THIS stock
        timestamp: Current timestamp
    """
    # Import reversal monitor for trigger checks
    # Note: This is a circular import workaround - reversal_monitor should be passed in
    # For now, we'll handle this in the tick handler
    
    if self.situation == 'reversal_s2':
        # OOPS entry logic
        self._check_oops_entry(price, timestamp)
    
    elif self.situation == 'reversal_s1':
        # Strong Start entry logic
        self._check_strong_start_entry(price, timestamp)
```

**Note:** We'll handle the reversal_monitor dependency in the actual implementation. For now, the trigger checks will remain in the tick handler but use the stock's own price.

---

## 3. Add _check_oops_entry() Method

**Add this private method to ReversalStockState class:**

```python
def _check_oops_entry(self, price: float, timestamp: datetime):
    """
    Check OOPS entry conditions using THIS stock's price
    
    Args:
        price: Current price for THIS stock
        timestamp: Current timestamp
    """
    # Already triggered - don't re-enter
    if self.oops_triggered or self.entered:
        return
    
    # Need opening price data
    if self.open_price is None or self.previous_close is None:
        return
    
    # Import reversal monitor (will be refactored to dependency injection)
    from reversal_monitor import ReversalMonitor
    reversal_monitor = ReversalMonitor()
    
    # Check OOPS trigger using THIS stock's data
    if reversal_monitor.check_oops_trigger(
        self.symbol, 
        self.open_price,      # THIS stock's open
        self.previous_close,  # THIS stock's prev close
        price                 # THIS stock's current price
    ):
        self.oops_triggered = True
        
        # CRITICAL: Use THIS stock's price, not some other stock's price
        self.entry_high = price
        self.entry_sl = price * 0.96  # 4% SL
        
        # Enter position
        self.enter_position(price, timestamp)
        
        logger.info(f"[{self.symbol}] OOPS TRIGGERED at {price:.2f} - Entered position")
```

**Critical Point:** All data (open_price, previous_close, price) belongs to THIS stock only.

---

## 4. Add _check_strong_start_entry() Method

**Add this private method to ReversalStockState class:**

```python
def _check_strong_start_entry(self, price: float, timestamp: datetime):
    """
    Check Strong Start entry conditions using THIS stock's price
    
    Args:
        price: Current price for THIS stock
        timestamp: Current timestamp
    """
    # Already triggered - don't re-enter
    if self.strong_start_triggered or self.entered:
        return
    
    # Need opening price data
    if self.open_price is None or self.previous_close is None:
        return
    
    # Import reversal monitor (will be refactored to dependency injection)
    from reversal_monitor import ReversalMonitor
    reversal_monitor = ReversalMonitor()
    
    # Check Strong Start trigger using THIS stock's data
    if reversal_monitor.check_strong_start_trigger(
        self.symbol,
        self.open_price,      # THIS stock's open
        self.previous_close,  # THIS stock's prev close
        self.daily_low        # THIS stock's daily low
    ):
        self.strong_start_triggered = True
        
        # CRITICAL: Use THIS stock's price, not some other stock's price
        self.entry_high = price
        self.entry_sl = price * 0.96  # 4% SL
        
        # Enter position
        self.enter_position(price, timestamp)
        
        logger.info(f"[{self.symbol}] STRONG START TRIGGERED at {price:.2f} - Entered position")
```

**Critical Point:** Uses `self.daily_low` (THIS stock's low) and `price` (THIS stock's current price).

---

## 5. Add _handle_exit_monitoring() Method

**Add this private method to ReversalStockState class:**

```python
def _handle_exit_monitoring(self, price: float, timestamp: datetime):
    """
    Handle exit monitoring (trailing SL + exit signals)
    
    Args:
        price: Current price for THIS stock
        timestamp: Current timestamp
    """
    if not self.entered or self.entry_price is None:
        return
    
    # Calculate current profit percentage
    profit_pct = (price - self.entry_price) / self.entry_price
    
    # Trailing SL: Move SL to entry when 5% profit
    if profit_pct >= 0.05 and self.entry_sl < self.entry_price:
        old_sl = self.entry_sl
        self.entry_sl = self.entry_price  # Move to breakeven
        logger.info(f"[{self.symbol}] Trailing SL adjusted: Rs{old_sl:.2f} → Rs{self.entry_sl:.2f} (5% profit reached)")
    
    # Check exit signal: SL hit
    if price <= self.entry_sl:
        pnl = profit_pct * 100
        self.exit_position(price, timestamp, "Stop Loss Hit")
        logger.info(f"[{self.symbol}] EXIT at Rs{price:.2f}, PNL: {pnl:+.2f}%")
```

**Key Points:**
- Handles trailing stop loss (5% profit → move SL to entry)
- Handles exit signal (price hits SL)
- Uses THIS stock's price only

---

## 6. Refactor Existing update_price() Method

**Current code:**
```python
def update_price(self, price: float, timestamp: datetime):
    """Update price and track high/low"""
    self.current_price = price
    self.daily_high = max(self.daily_high, price)
    self.daily_low = min(self.daily_low, price)
    self.last_update = timestamp
```

**This is already correct - no changes needed!**

The update_price method already uses the price parameter correctly.

---

## 7. Update ReversalStockMonitor.process_tick()

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**Current code:**
```python
def process_tick(self, instrument_key: str, symbol: str, price: float, timestamp: datetime, ohlc_list: list = None):
    """Process a price tick for a stock"""
    if instrument_key not in self.stocks:
        return
    
    stock = self.stocks[instrument_key]
    
    # Update price tracking (for high/low and current price)
    stock.update_price(price, timestamp)
    
    # Set session start if this is the first tick
    if self.session_start_time is None:
        self.session_start_time = timestamp
```

**Updated code:**
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

**Change:** Replaced `stock.update_price()` with `stock.process_tick()` which internally calls update_price and handles state-based logic.

---

## 8. Simplify Tick Handler in run_reversal.py

**File:** `src/trading/live_trading/run_reversal.py`

**Current code (lines 232-304):**
```python
def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
    """Reversal tick handler - ticks for monitoring/triggers only"""
    global global_selected_stocks, global_selected_symbols
    
    monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)
    
    # Get stock for processing
    stock = monitor.stocks.get(instrument_key)
    if not stock:
        return
    
    # Process OOPS reversal logic (only if opening price is available from API)
    if stock and stock.situation == 'reversal_s2':
        # Check OOPS reversal conditions
        if reversal_monitor.check_oops_trigger(symbol, stock.open_price, stock.previous_close, price):
            if not stock.oops_triggered:
                stock.oops_triggered = True
                print(f"TARGET {symbol}: OOPS reversal triggered - gap down + prev close cross")
                # Enter position immediately for OOPS
                stock.entry_high = price
                stock.entry_sl = price * 0.96  # 4% SL
                stock.enter_position(price, timestamp)
                paper_trader.log_entry(stock, price, timestamp)
    
    # ... more complex logic with loops ...
```

**New simplified code:**
```python
def tick_handler_reversal(instrument_key, symbol, price, timestamp, ohlc_list=None):
    """
    Simplified reversal tick handler
    Delegates all logic to individual stocks
    """
    global global_selected_stocks, global_selected_symbols
    
    # Get stock
    stock = monitor.stocks.get(instrument_key)
    if not stock:
        return
    
    # Early exit for unsubscribed stocks
    if not stock.is_subscribed:
        return
    
    # Delegate to stock's own tick processor
    # Stock will handle its own entry/exit logic based on its state
    monitor.process_tick(instrument_key, symbol, price, timestamp, ohlc_list)
    
    # Log paper trades if stock just entered
    if stock.entered and stock.entry_time == timestamp:
        paper_trader.log_entry(stock, price, timestamp)
    
    # Log paper exits if stock just exited
    if stock.state == StockState.EXITED and stock.exit_time == timestamp:
        paper_trader.log_exit(stock, price, timestamp, "Stop Loss Hit")
```

**Key Changes:**
1. ✅ Removed all nested loops
2. ✅ Removed duplicate entry logic (OOPS and Strong Start)
3. ✅ Early exit for unsubscribed stocks
4. ✅ Delegates to `monitor.process_tick()` which calls `stock.process_tick()`
5. ✅ Only logs paper trades after entry/exit

**Complexity:** O(n) → O(1) (no loops, just dictionary lookup)

---

## 9. Handle Paper Trader Integration

**Current approach in tick handler:**
- Manually calls `paper_trader.log_entry()` after detecting entry
- Manually calls `paper_trader.log_exit()` after detecting exit

**New approach:**
- Stock's `enter_position()` method is called by stock itself
- Stock's `exit_position()` method is called by stock itself
- Tick handler just checks if entry/exit just happened and logs

**Alternative (cleaner):** Add paper trader to stock's methods:

```python
# In ReversalStockState class
def enter_position(self, price: float, timestamp: datetime, paper_trader=None):
    """Enter position at market"""
    self.entry_price = price
    self.entry_time = timestamp
    self.entered = True
    self.state = StockState.MONITORING_EXIT
    
    logger.info(f"[{self.symbol}] ENTRY at {price:.2f} (target was {self.entry_high:.2f}) - State: {self.state.value}")
    
    # Log to paper trader if provided
    if paper_trader:
        paper_trader.log_entry(self, price, timestamp)

def exit_position(self, price: float, timestamp: datetime, reason: str, paper_trader=None):
    """Exit position"""
    self.exit_price = price
    self.exit_time = timestamp
    self.is_subscribed = False
    self.state = StockState.EXITED
    
    # Calculate P&L
    if self.entry_price:
        self.pnl = (price - self.entry_price) / self.entry_price * 100
    
    logger.info(f"[{self.symbol}] EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason} - State: {self.state.value}")
    
    # Log to paper trader if provided
    if paper_trader:
        paper_trader.log_exit(self, price, timestamp, reason)
```

**Then update the entry check methods to pass paper_trader:**

```python
def _check_oops_entry(self, price: float, timestamp: datetime, paper_trader=None):
    # ... existing code ...
    
    # Enter position with paper trader
    self.enter_position(price, timestamp, paper_trader)

def _check_strong_start_entry(self, price: float, timestamp: datetime, paper_trader=None):
    # ... existing code ...
    
    # Enter position with paper trader
    self.enter_position(price, timestamp, paper_trader)
```

**But this requires passing paper_trader through process_tick chain.** 

For now, keep the tick handler approach (check if just entered/exited and log).

---

## Testing Checklist

After implementing Part 2, verify:

- [ ] Each stock only processes its own price
- [ ] No cross-contamination (GODREJPROP's price doesn't affect POONAWALLA)
- [ ] OOPS stocks trigger correctly with their own price
- [ ] Strong Start stocks trigger correctly with their own price
- [ ] Trailing SL adjusts at 5% profit
- [ ] Exit triggers at SL hit
- [ ] Paper trader logs entries and exits
- [ ] No nested loops in tick handler
- [ ] Early exit for unsubscribed stocks works

---

## Edge Cases to Handle

1. **What if stock enters and exits in same tick?**
   - Current design: enter_position() sets state to MONITORING_EXIT, then _handle_exit_monitoring() can trigger in same tick
   - Solution: This is fine, but make sure paper_trader.log_entry() happens before log_exit()

2. **What if reversal_monitor is None?**
   - Add null checks in _check_oops_entry() and _check_strong_start_entry()

3. **What if multiple stocks enter simultaneously?**
   - Each processes independently, no issue

---

## Next Steps

After completing Part 2, proceed to:
- **Part 3:** Monitor Unsubscribe Logic (coordinate unsubscribes at key phases)
- **Part 4:** Updated run_reversal.py Main Flow (integrate everything)

---

## Questions for Coder

1. Should we pass paper_trader as dependency or keep current approach?
2. Should we add validation to prevent re-entry after already entered?
3. Need help with reversal_monitor dependency injection?
