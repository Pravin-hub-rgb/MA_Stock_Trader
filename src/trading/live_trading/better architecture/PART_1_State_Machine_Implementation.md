# PART 1: State Machine Implementation Guide

## Overview
This document guides the implementation of an explicit state machine for `ReversalStockState` class to replace boolean flags and enable proper lifecycle management.

---

## 1. Create State Enum

**File:** `src/trading/live_trading/reversal_stock_monitor.py`

**Location:** Add at the top of the file, after imports

```python
from enum import Enum

class StockState(Enum):
    """Explicit states for stock lifecycle management"""
    INITIALIZED = "initialized"
    WAITING_FOR_OPEN = "waiting_for_open"
    GAP_VALIDATED = "gap_validated"
    QUALIFIED = "qualified"
    SELECTED = "selected"
    MONITORING_ENTRY = "monitoring_entry"
    ENTERED = "entered"
    MONITORING_EXIT = "monitoring_exit"
    NOT_SELECTED = "not_selected"
    REJECTED = "rejected"
    UNSUBSCRIBED = "unsubscribed"
    EXITED = "exited"
```

---

## 2. Update ReversalStockState.__init__()

**Current code:**
```python
def __init__(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'reversal_s2'):
    self.symbol = symbol
    self.instrument_key = instrument_key
    self.previous_close = previous_close
    self.situation = situation
    
    # ... existing fields ...
    
    # Status flags
    self.is_active = True
    self.gap_validated = False
    # ... other boolean flags ...
```

**New code - Add these fields:**
```python
def __init__(self, symbol: str, instrument_key: str, previous_close: float, situation: str = 'reversal_s2'):
    self.symbol = symbol
    self.instrument_key = instrument_key
    self.previous_close = previous_close
    self.situation = situation
    
    # ... keep all existing fields ...
    
    # NEW: State management
    self.state = StockState.INITIALIZED
    self.is_subscribed = True  # Track subscription status
    
    # Keep existing boolean flags for backward compatibility during transition
    self.is_active = True
    self.gap_validated = False
    # ... other existing flags ...
```

**Why keep old flags?** For gradual migration. We'll remove them later once everything works.

---

## 3. Update validate_gap() Method

**Current code:**
```python
def validate_gap(self) -> bool:
    """Validate gap based on reversal situation"""
    if self.open_price is None:
        return False
    
    # ... validation logic ...
    
    self.gap_validated = True
    logger.info(f"[{self.symbol}] Gap {gap_type} validated: {gap_pct:.1%} ({self.situation})")
    return True
```

**Updated code - Add state transitions:**
```python
def validate_gap(self) -> bool:
    """Validate gap based on reversal situation"""
    if self.open_price is None:
        return False
    
    gap_pct = (self.open_price - self.previous_close) / self.previous_close
    
    # Check if gap is within flat range (reject)
    if abs(gap_pct) <= FLAT_GAP_THRESHOLD:
        self.reject(f"Gap too flat: {gap_pct:.1%} (within ±{FLAT_GAP_THRESHOLD:.1%} range)")
        return False
    
    # Situation-specific gap requirements
    if self.situation == 'reversal_s1':
        # Need gap up > flat threshold, but not too high
        if gap_pct <= FLAT_GAP_THRESHOLD:
            self.reject(f"Gap down or flat: {gap_pct:.1%} (need gap up > {FLAT_GAP_THRESHOLD:.1%} for {self.situation})")
            return False
        if gap_pct > 0.05:
            self.reject(f"Gap up too high: {gap_pct:.1%} > 5%")
            return False
    elif self.situation == 'reversal_s2':
        # Need gap down < -flat threshold (no lower limit)
        if gap_pct >= -FLAT_GAP_THRESHOLD:
            self.reject(f"Gap up or flat: {gap_pct:.1%} (need gap down < -{FLAT_GAP_THRESHOLD:.1%} for reversal_s2)")
            return False
    else:
        self.reject(f"Unknown situation: {self.situation}")
        return False
    
    # Gap validated - transition state
    self.gap_validated = True
    self.state = StockState.GAP_VALIDATED  # NEW: State transition
    
    gap_type = "up" if gap_pct >= 0 else "down"
    logger.info(f"[{self.symbol}] Gap {gap_type} validated: {gap_pct:.1%} ({self.situation}) - State: {self.state.value}")
    return True
```

---

## 4. Update check_low_violation() Method

**Current code:**
```python
def check_low_violation(self) -> bool:
    """Check if low dropped below 1% of open price"""
    if self.open_price is None:
        return False
    
    threshold = self.open_price * (1 - LOW_VIOLATION_PCT)
    
    if self.daily_low < threshold:
        self.reject(f"Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
        return False
    
    self.low_violation_checked = True
    return True
```

**Updated code - Add state transition:**
```python
def check_low_violation(self) -> bool:
    """Check if low dropped below 1% of open price"""
    if self.open_price is None:
        return False
    
    threshold = self.open_price * (1 - LOW_VIOLATION_PCT)
    
    if self.daily_low < threshold:
        self.reject(f"Low violation: {self.daily_low:.2f} < {threshold:.2f} (1% below open {self.open_price:.2f})")
        return False
    
    self.low_violation_checked = True
    self.state = StockState.QUALIFIED  # NEW: State transition
    
    logger.info(f"[{self.symbol}] Low violation check passed - State: {self.state.value}")
    return True
```

---

## 5. Update reject() Method

**Current code:**
```python
def reject(self, reason: str):
    """Mark stock as rejected"""
    self.is_active = False
    self.rejection_reason = reason
    logger.info(f"[{self.symbol}] REJECTED: {reason}")
```

**Updated code - Add state transition and subscription flag:**
```python
def reject(self, reason: str):
    """Mark stock as rejected and stop monitoring"""
    self.is_active = False
    self.is_subscribed = False  # NEW: Mark for unsubscribe
    self.state = StockState.REJECTED  # NEW: State transition
    self.rejection_reason = reason
    
    logger.info(f"[{self.symbol}] REJECTED: {reason} - State: {self.state.value}")
```

---

## 6. Update prepare_entry() Method

**Current code:**
```python
def prepare_entry(self):
    """Called when stock is qualified to set entry levels"""
    if not self.is_active:
        return
    
    # Set entry high as the high reached so far
    self.entry_high = self.daily_high
    
    # Set stop loss 4% below entry high
    self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)
    
    self.entry_ready = True
    logger.info(f"[{self.symbol}] Entry prepared - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f}")
```

**Updated code - Add state transition:**
```python
def prepare_entry(self):
    """Called when stock is selected to set entry levels"""
    if not self.is_active:
        return
    
    # Set entry high as the high reached so far
    self.entry_high = self.daily_high
    
    # Set stop loss 4% below entry high
    self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)
    
    self.entry_ready = True
    self.state = StockState.MONITORING_ENTRY  # NEW: State transition
    
    logger.info(f"[{self.symbol}] Entry prepared - High: {self.entry_high:.2f}, SL: {self.entry_sl:.2f} - State: {self.state.value}")
```

---

## 7. Update enter_position() Method

**Current code:**
```python
def enter_position(self, price: float, timestamp: datetime):
    """Enter position at market"""
    self.entry_price = price
    self.entry_time = timestamp
    self.entered = True
    
    logger.info(f"[{self.symbol}] ENTRY at {price:.2f} (target was {self.entry_high:.2f})")
```

**Updated code - Add state transition:**
```python
def enter_position(self, price: float, timestamp: datetime):
    """Enter position at market"""
    self.entry_price = price
    self.entry_time = timestamp
    self.entered = True
    self.state = StockState.MONITORING_EXIT  # NEW: State transition (from MONITORING_ENTRY to MONITORING_EXIT)
    
    logger.info(f"[{self.symbol}] ENTRY at {price:.2f} (target was {self.entry_high:.2f}) - State: {self.state.value}")
```

---

## 8. Update exit_position() Method

**Current code:**
```python
def exit_position(self, price: float, timestamp: datetime, reason: str):
    """Exit position"""
    self.exit_price = price
    self.exit_time = timestamp
    
    # Calculate P&L
    if self.entry_price:
        self.pnl = (price - self.entry_price) / self.entry_price * 100
    
    logger.info(f"[{self.symbol}] EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason}")
```

**Updated code - Add state transition and unsubscribe flag:**
```python
def exit_position(self, price: float, timestamp: datetime, reason: str):
    """Exit position"""
    self.exit_price = price
    self.exit_time = timestamp
    self.is_subscribed = False  # NEW: Mark for unsubscribe after exit
    self.state = StockState.EXITED  # NEW: State transition
    
    # Calculate P&L
    if self.entry_price:
        self.pnl = (price - self.entry_price) / self.entry_price * 100
    
    logger.info(f"[{self.symbol}] EXIT at {price:.2f} | P&L: {self.pnl:.2f}% | Reason: {reason} - State: {self.state.value}")
```

---

## 9. Add New Method: mark_not_selected()

**Add this new method to ReversalStockState class:**

```python
def mark_not_selected(self):
    """Mark stock as not selected during selection phase"""
    self.is_active = False
    self.is_subscribed = False  # Mark for unsubscribe
    self.state = StockState.NOT_SELECTED
    
    logger.info(f"[{self.symbol}] Not selected (limited slots) - State: {self.state.value}")
```

---

## 10. Add New Method: mark_selected()

**Add this new method to ReversalStockState class:**

```python
def mark_selected(self):
    """Mark stock as selected during selection phase"""
    self.state = StockState.SELECTED
    
    logger.info(f"[{self.symbol}] Selected for trading - State: {self.state.value}")
```

---

## Testing Checklist

After implementing Part 1, verify:

- [ ] All state transitions log correctly with state names
- [ ] `is_subscribed` flag is set to `False` for rejected stocks
- [ ] `is_subscribed` flag is set to `False` for exited stocks
- [ ] State progression: INITIALIZED → GAP_VALIDATED → QUALIFIED → SELECTED → MONITORING_ENTRY → MONITORING_EXIT → EXITED
- [ ] Rejected stocks transition to REJECTED state
- [ ] Not selected stocks transition to NOT_SELECTED state

---

## Next Steps

After completing Part 1, proceed to:
- **Part 2:** Simplified Tick Handler (process_tick method)
- **Part 3:** Monitor Unsubscribe Logic
- **Part 4:** Updated run_reversal.py Main Flow

---

## Questions for Coder

1. Any unclear state transitions?
2. Should we add state validation (prevent invalid transitions)?
3. Need help with testing this part?
