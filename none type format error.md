we did all of this okay then this error 
showed up

things are better than before we are rejecting stocks 
but ther is this error unsupported format string passed to NoneType.format
this is the folder structure : Here's the folder structure of the `src/trading/live_trading` directory: Main Files:
* `__init__.py`
* `bot_args.py`
* `config.py`
* `continuation_stock_monitor.py`
* `data_streamer.py`
* `MarketDataFeedV3_pb2.py`
* `paper_trader.py`
* `previous_close_bug.md`
* `reversal_monitor.py`
* `reversal_stock_monitor.py`
* `rule_engine.py`
* `run_continuation.py`
* `run_live_bot.py`
* `run_reversal.py`
* `selection_engine.py`
* `setup_reversal_data.py`
* `simple_data_streamer.py`
* `stock_classifier.py`
* `stock_scorer.py`
* `test_integration.py`
* `validate_trading_lists.py`
* `volume_profile.py` Subdirectories: better architecture/
* `IMPLEMENTATION_SUMMARY.md`
* `PART_1_State_Machine_Implementation.md`
* `PART_2_Tick_Processing_Guide.md`
* `PART_3_Monitor_Unsubscribe_Logic.md`
* `PART_4_Complete_Integration.md` continuation_modules/
* `__init__.py`
* `continuation_timing_module.py` reversal_modules/
* `__init__.py`
* `integration.py`
* `state_machine.py`
* `subscription_manager.py`
* `tick_processor.py` The structure shows a well-organized trading system with separate modules for continuation and reversal strategies, along with comprehensive documentation and modular architecture components.
Tell me which file you need

Here's the folder structure of the `src/trading/live_trading` directory:
**Main Files:**
- `__init__.py`
- `bot_args.py`
- `config.py`
- `continuation_stock_monitor.py`
- `data_streamer.py`
- `MarketDataFeedV3_pb2.py`
- `paper_trader.py`
- `previous_close_bug.md`
- `reversal_monitor.py`
- `reversal_stock_monitor.py`
- `rule_engine.py`
- `run_continuation.py`
- `run_live_bot.py`
- `run_reversal.py`
- `selection_engine.py`
- `setup_reversal_data.py`
- `simple_data_streamer.py`
- `stock_classifier.py`
- `stock_scorer.py`
- `test_integration.py`
- `validate_trading_lists.py`
- `volume_profile.py`
**Subdirectories:**
**better architecture/**
- `IMPLEMENTATION_SUMMARY.md`
- `PART_1_State_Machine_Implementation.md`
- `PART_2_Tick_Processing_Guide.md`
- `PART_3_Monitor_Unsubscribe_Logic.md`
- `PART_4_Complete_Integration.md`
**continuation_modules/**
- `__init__.py`
- `continuation_timing_module.py`
**reversal_modules/**
- `__init__.py`
- `integration.py`
- `state_machine.py`
- `subscription_manager.py`
- `tick_processor.py`
The structure shows a well-organized trading system with separate modules for continuation and reversal strategies, along with comprehensive documentation and modular architecture components.

just discuss no code yet untill we have common ground and you understand stuff fully 
so tell me which file you need to understand stuff\


Looking at the error "unsupported format string passed to NoneType.format", this is a Python formatting error that happens when you try to use `.format()` on a `None` value, or when you're trying to format `None` into a string.

Given that you mentioned:
1. The implementation is working better - stocks are being rejected
2. But this error is appearing
3. This likely involves logging or string formatting

I need to see these files to diagnose:

1. **`run_reversal.py`** - This is where the main tick handler and unsubscribe logic lives. The error is probably in the logging statements we added (like `safe_unsubscribe()`, `log_subscription_status()`, or in the tick processing logs)

2. **`reversal_stock_monitor.py`** - This has the state machine and process_tick() method. The error might be in the state transition logging or when formatting stock attributes that could be None

3. **`reversal_modules/tick_processor.py`** - If you implemented tick processing as a separate module, the error might be here

**My hypothesis**: The error is likely in a logging statement where we're trying to format something like:
```python
print(f"Stock {symbol} at {price:.2f}")  # price could be None
# or
f"{some_value}" where some_value is None
```

Can you start by showing me **`run_reversal.py`**? That's the most likely culprit since it has the most new logging code for unsubscribe operations and tick handling.

Also, if you can share the **full error traceback**, that would immediately tell us which file and line number is causing the issue!

Looking at your code, I can already spot the likely issue without needing the full traceback. Let me explain what I see:

## The Problem

In `tick_processor.py`, line 149 at the end of `_handle_exit_monitoring()`:

```python
logger.info(f"[{self.stock.symbol}] EXIT at Rs{price:.2f}, PNL: {pnl:+.2f}%")
```

The issue is that `pnl` could be `None` in certain edge cases, and you're trying to format it with `{pnl:+.2f}%`.

## Why This Happens

Look at the logic just above:
1. You calculate `profit_pct` from price and entry_price
2. You use `profit_pct` to check conditions and adjust stop loss
3. But then when the exit triggers, you call `self.stock.exit_position(price, timestamp, "Stop Loss Hit")`
4. The `exit_position` method calculates `self.pnl` internally
5. THEN you try to log `pnl` which you set as `profit_pct * 100`

**But here's the problem**: If `self.stock.entry_price` is somehow `None` (due to some edge case or race condition), then `profit_pct` calculation would fail OR the `pnl` variable might not get set properly.

## Questions Before We Fix:

1. **Is this the exact error location?** Can you confirm the traceback points to line 149 in tick_processor.py, or is it somewhere else?

2. **When does it happen?** Does this error occur:
   - During rejection (when logging rejected stocks)?
   - During exit (when a position closes)?
   - During some logging statement in `run_reversal.py`?

3. **Which stocks trigger it?** Does it happen for:
   - Specific stocks that get rejected early?
   - Stocks that enter positions?
   - All stocks?

4. **Do you have the full error traceback?** That would tell us exactly which line and which variable is `None`.

My best guess is it's either:
- Line 149 in tick_processor.py (the exit logging)
- Or some logging statement in `run_reversal.py` where you're formatting stock attributes that could be `None`

**Can you share the full error traceback or tell me which of these scenarios matches what you're seeing?**

[1:47:00 pm] ==================================================
[1:47:00 pm] Qualified stocks: 4
[1:47:00 pm] Selected stocks: ['SIGNATURE', 'ANANTRAJ']
[1:47:00 pm] =======================================================
[1:47:00 pm] PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED
[1:47:00 pm] =======================================================
[1:47:00 pm] Reversal bot error: unsupported format string passed to NoneType.__format__
[1:47:00 pm] [UNLOCK] Reversal bot singleton lock released
[1:47:00 pm] Reversal bot shutdown complete

this log is all we have man

i don't know any of your question
if you need other file i can give it to you

Okay, based on that log, the error happens at **PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED**. This is in `run_reversal.py`.

Let me see the `run_reversal.py` file to find the exact line causing the issue.

Can you show me the file? I need to see what happens after this log line:
```
[1:47:00 pm] PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED
```

The error is happening in some formatting statement right after you log that phase starts, probably when you're trying to log information about stocks being unsubscribed or their status.

**Please upload `run_reversal.py` - I can see it was in your first batch of uploads but I need to read it to find the Phase 3 code.**

Perfect! Now I found it. The error is at **line 370** where it calls:

```python
integration.phase_3_unsubscribe_after_selection(selected_stocks)
```

The error is happening **inside the integration module's Phase 3 method**. I need to see that file.

**Can you show me `/mnt/user-data/uploads/integration.py` from the `reversal_modules` folder?**

That's where the `phase_3_unsubscribe_after_selection()` method is defined, and that's where the formatting error is occurring - likely when it's trying to log information about stocks being unsubscribed and some attribute (like `open_price`, `entry_high`, `entry_sl`, etc.) is `None`.

Good! Now I need to see the **`subscription_manager.py`** file because the error is happening inside:

```python
self.subscription_manager.unsubscribe_non_selected(selected_stocks)
```

That's the Phase 3 method that's causing the format error. 

**Can you show me `subscription_manager.py` from the `reversal_modules` folder?**

That's where the actual unsubscribe logic and the problematic logging statement lives.

## FOUND IT! 🎯

**Line 161 in `subscription_manager.py`:**

```python
print(f" SELECTED: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")
```

**The Problem:**

At Phase 3 (selection phase), some stocks that are qualified might have `entry_high` or `entry_sl` set to `None`. This happens when:

1. Stock passes gap validation 
2. Stock passes low violation check   
3. Stock becomes "qualified" 
4. BUT `prepare_entry()` hasn't been called yet OR didn't set these values properly ❌

So when you try to format `None` with `.2f`, Python throws:
```
unsupported format string passed to NoneType.__format__
```

## The Fix

We need to **handle the case where `entry_high` or `entry_sl` might be `None`** in the Phase 3 logging.

Here are the fixes needed:

### Fix 1: In `subscription_manager.py` line 161
Change:
```python
print(f" SELECTED: {stock.symbol} (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})")
```

To:
```python
entry_info = ""
if stock.entry_high is not None and stock.entry_sl is not None:
    entry_info = f" (Entry: Rs{stock.entry_high:.2f}, SL: Rs{stock.entry_sl:.2f})"
print(f" SELECTED: {stock.symbol}{entry_info}")
```

### Fix 2: Also check line 165 (NOT SELECTED logging)
Change:
```python
print(f"✗ NOT SELECTED: {stock.symbol} (limited to {len(selected_stocks)} positions)")
```

This one is probably fine, but let's be safe.

---

## Root Cause Analysis

Looking at `run_reversal.py`:
- Line 362: `qualified_stocks = monitor.get_qualified_stocks()`
- Line 365: `selected_stocks = selection_engine.select_stocks(qualified_stocks)`
- **Line 356: `monitor.prepare_entries()` is called BEFORE getting qualified stocks**

But the issue is that `prepare_entries()` in `reversal_stock_monitor.py` only prepares entries for stocks that are **already qualified**, and it sets `entry_high` and `entry_sl`.

**The bug**: Some stocks might be in a weird state where they're "qualified" but their `entry_high` and `entry_sl` are still `None` because `prepare_entry()` wasn't called or didn't work properly.

---

## Should I write the fix now, or do you want to discuss more?

The safest fix is to add None-checks in the logging statements. But we might also want to investigate WHY `entry_high` and `entry_sl` are `None` for qualified stocks.

**Exactly!** You're absolutely right. For qualified stocks, `entry_high` and `entry_sl` should NOT be `None`. 

So the real question is: **WHY are they `None` for qualified stocks?**

Let me trace through the logic:

## The Flow (as designed)

1. **Gap validation** (9:14:30) → sets `gap_validated = True`
2. **Low violation check** (before 9:16:00) → sets `low_violation_checked = True`
3. **Get qualified stocks** → returns stocks where `gap_validated AND low_violation_checked`
4. **Prepare entries** (line 356) → calls `monitor.prepare_entries()`
5. **Selection** (line 365) → selects from qualified stocks
6. **Phase 3 logging** (line 161) → tries to print `entry_high` and `entry_sl` ❌

## Let's Check `monitor.prepare_entries()`

Looking at `reversal_stock_monitor.py` line 356 area, the `prepare_entries()` method should be calling `stock.prepare_entry()` for each qualified stock.

But I notice something in `reversal_stock_monitor.py`:

```python
def prepare_entries(self):
    """Called when stocks are qualified to prepare entry levels"""
    for stock in self.get_qualified_stocks():
        stock.prepare_entry()
```

And in `ReversalStockState.prepare_entry()`:

```python
def prepare_entry(self):
    """Called when stock is qualified to set entry levels"""
    if not self.is_active:
        return
    
    # Set entry high as the high reached so far
    self.entry_high = self.daily_high
    
    # Set stop loss 4% below entry high
    self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)
```

## The Problem

**`self.daily_high` might be `float('-inf')`** (the initialization value) if:
- No ticks have been processed yet
- The stock hasn't updated its price

This would make `entry_high = float('-inf')` and `entry_sl` would be a calculated value from that.

But wait... that's not `None`, so that's not causing the format error.

## Let me check something else

Looking back at `ReversalStockState.__init__`:

```python
self.entry_high: Optional[float] = None  # High reached after entry time
self.entry_sl: Optional[float] = None    # 4% below entry_high
```

So they're initialized as `None`.

**The issue**: Some qualified stocks never had their `prepare_entry()` called, OR the method returned early because `self.is_active = False`.

## Hypothesis

**I think some stocks are being marked as NOT active (`is_active = False`) but still appearing in qualified stocks.**

Can you check:
1. Does `get_qualified_stocks()` check `stock.is_active`?
2. When does `is_active` get set to `False`?

Let me look at the code again...

In `reversal_stock_monitor.py` line 273:

```python
def get_qualified_stocks(self) -> List[ReversalStockState]:
    """Get stocks that passed gap and low violation checks"""
    qualified = []
    rejected = []

    for stock in self.stocks.values():
        # For reversals: only gap and low violation required
        if stock.is_active and stock.gap_validated and stock.low_violation_checked:
            qualified.append(stock)
```

So it DOES check `is_active`. 

**Then the only way `entry_high` and `entry_sl` are `None` is if `prepare_entry()` never executed the assignment lines.**

Wait... could `daily_high` be causing this? Let me check if `daily_high` being `float('-inf')` causes the format to fail...

Actually, **I think I found it!** Look at the selection process. Are ALL qualified stocks being passed to `selection_engine.select_stocks()`, and then SOME are filtered out? If so, the NON-selected stocks might not have had `prepare_entry()` called on them properly.

**Can you tell me: Which stocks were qualified vs which were selected in your log?**

[1:44:24 pm] LAUNCHING REVERSAL BOT (Tick-based)...
[1:44:24 pm] Starting src/trading/live_trading/run_reversal.py...
[1:44:25 pm] [LOCK] Reversal bot singleton lock acquired
[1:44:25 pm] STARTING REVERSAL TRADING BOT (API-BASED OPENING PRICES)
[1:44:25 pm] =======================================================
[1:44:25 pm] CONFIG: Real market trading configuration loaded
[1:44:25 pm] CONFIG: Market open: 13:46:00
[1:44:25 pm] CONFIG: Entry time: 13:47:00
[1:44:25 pm] CONFIG: API poll delay: 5 seconds
[1:44:25 pm] CONFIG: Max positions: 2
[1:44:25 pm] CONFIG: Entry SL: 4.0%
[1:44:25 pm] CONFIG: Low violation: 1.0%
[1:44:25 pm] CONFIG: Strong start gap: 2.0%
[1:44:26 pm] Time: 2026-01-28 13:44:26 IST
[1:44:26 pm] Loaded 15 reversal stocks:
[1:44:26 pm] ANANTRAJ: OOPS (d14) - 14 days any trend
[1:44:26 pm] TEJASNET: OOPS (d15) - 15 days any trend
[1:44:26 pm] SIGNATURE: OOPS (d15) - 15 days any trend
[1:44:26 pm] POONAWALLA: Strong Start (u6) - 3-6 days uptrend
[1:44:26 pm] PANACEABIO: OOPS (d11) - 11 days any trend
[1:44:26 pm] ORIENTTECH: OOPS (d15) - 15 days any trend
[1:44:26 pm] KALYANKJIL: OOPS (d12) - 12 days any trend
[1:44:26 pm] IIFL: OOPS (d13) - 13 days any trend
[1:44:26 pm] GODREJPROP: OOPS (d14) - 14 days any trend
[1:44:26 pm] ETERNAL: OOPS (d3) - 3 days downtrend
[1:44:26 pm] ENGINERSIN: OOPS (d15) - 15 days any trend
[1:44:26 pm] DEVYANI: OOPS (d15) - 15 days any trend
[1:44:26 pm] BALUFORGE: OOPS (d14) - 14 days any trend
[1:44:26 pm] ASHAPURMIN: OOPS (u9) - 9 days any trend
[1:44:26 pm] ARISINFRA: OOPS (d15) - 15 days any trend
[1:44:26 pm] LOADED 15 reversal stocks:
[1:44:26 pm] ANANTRAJ: Reversal Downtrend
[1:44:26 pm] TEJASNET: Reversal Downtrend
[1:44:26 pm] SIGNATURE: Reversal Downtrend
[1:44:26 pm] POONAWALLA: Reversal Uptrend
[1:44:26 pm] PANACEABIO: Reversal Downtrend
[1:44:26 pm] ORIENTTECH: Reversal Downtrend
[1:44:26 pm] KALYANKJIL: Reversal Downtrend
[1:44:26 pm] IIFL: Reversal Downtrend
[1:44:26 pm] GODREJPROP: Reversal Downtrend
[1:44:26 pm] ETERNAL: Reversal Downtrend
[1:44:26 pm] ENGINERSIN: Reversal Downtrend
[1:44:26 pm] DEVYANI: Reversal Downtrend
[1:44:26 pm] BALUFORGE: Reversal Downtrend
[1:44:26 pm] ASHAPURMIN: Reversal Downtrend
[1:44:26 pm] ARISINFRA: Reversal Downtrend
[1:44:27 pm] OK ANANTRAJ: Prev Close Rs490.15
[1:44:27 pm] OK TEJASNET: Prev Close Rs296.15
[1:44:27 pm] OK SIGNATURE: Prev Close Rs823.00
[1:44:27 pm] OK POONAWALLA: Prev Close Rs404.40
[1:44:28 pm] OK PANACEABIO: Prev Close Rs347.75
[1:44:28 pm] OK ORIENTTECH: Prev Close Rs325.20
[1:44:28 pm] OK KALYANKJIL: Prev Close Rs368.90
[1:44:28 pm] OK IIFL: Prev Close Rs521.85
[1:44:28 pm] OK GODREJPROP: Prev Close Rs1517.90
[1:44:29 pm] OK ETERNAL: Prev Close Rs253.85
[1:44:29 pm] OK ENGINERSIN: Prev Close Rs164.56
[1:44:29 pm] OK DEVYANI: Prev Close Rs111.71
[1:44:29 pm] OK BALUFORGE: Prev Close Rs363.40
[1:44:29 pm] OK ASHAPURMIN: Prev Close Rs638.70
[1:44:30 pm] OK ARISINFRA: Prev Close Rs100.75
[1:44:30 pm] PREPARED 15 reversal instruments
[1:44:30 pm] === PRE-MARKET IEP FETCH SEQUENCE ===
[1:44:30 pm] WAITING 60 seconds until PREP_START (13:45:30)...
[1:45:30 pm] FETCHING IEP for 15 reversal stocks...
[1:45:30 pm] Clean symbols for IEP: ['ANANTRAJ', 'TEJASNET', 'SIGNATURE', 'POONAWALLA', 'PANACEABIO', 'ORIENTTECH', 'KALYANKJIL', 'IIFL', 'GODREJPROP', 'ETERNAL', 'ENGINERSIN', 'DEVYANI', 'BALUFORGE', 'ASHAPURMIN', 'ARISINFRA']
[1:45:30 pm] IEP FETCH COMPLETED SUCCESSFULLY
[1:45:30 pm] Set opening price for ANANTRAJ: Rs481.50
[1:45:30 pm] Gap validated for ANANTRAJ
[1:45:30 pm] Set opening price for TEJASNET: Rs335.40
[1:45:30 pm] Gap validation failed for TEJASNET
[1:45:30 pm] Set opening price for SIGNATURE: Rs811.80
[1:45:30 pm] Gap validated for SIGNATURE
[1:45:30 pm] Set opening price for POONAWALLA: Rs403.05
[1:45:30 pm] Gap validation failed for POONAWALLA
[1:45:30 pm] Set opening price for PANACEABIO: Rs355.35
[1:45:30 pm] Gap validation failed for PANACEABIO
[1:45:30 pm] Set opening price for ORIENTTECH: Rs329.30
[1:45:30 pm] Gap validation failed for ORIENTTECH
[1:45:30 pm] Set opening price for KALYANKJIL: Rs363.75
[1:45:30 pm] Gap validated for KALYANKJIL
[1:45:30 pm] Set opening price for IIFL: Rs541.75
[1:45:30 pm] Gap validation failed for IIFL
[1:45:30 pm] Set opening price for GODREJPROP: Rs1529.20
[1:45:30 pm] Gap validation failed for GODREJPROP
[1:45:30 pm] Set opening price for ETERNAL: Rs261.85
[1:45:30 pm] Gap validation failed for ETERNAL
[1:45:30 pm] Set opening price for ENGINERSIN: Rs170.26
[1:45:30 pm] Gap validation failed for ENGINERSIN
[1:45:30 pm] Set opening price for DEVYANI: Rs114.01
[1:45:30 pm] Gap validation failed for DEVYANI
[1:45:30 pm] Set opening price for BALUFORGE: Rs353.40
[1:45:30 pm] Gap validated for BALUFORGE
[1:45:30 pm] Set opening price for ASHAPURMIN: Rs646.00
[1:45:30 pm] Gap validation failed for ASHAPURMIN
[1:45:30 pm] Set opening price for ARISINFRA: Rs104.84
[1:45:30 pm] Gap validation failed for ARISINFRA
[1:45:30 pm] =======================================================
[1:45:30 pm] PHASE 1: UNSUBSCRIBING GAP-REJECTED STOCKS
[1:45:30 pm] =======================================================
[1:45:30 pm] No stocks rejected at gap validation
[1:45:30 pm] === SUBSCRIPTION STATUS ===
[1:45:30 pm] INITIALIZED: 4 stocks - ['ANANTRAJ', 'SIGNATURE', 'KALYANKJIL', 'BALUFORGE']
[1:45:30 pm] REJECTED: 11 stocks - ['TEJASNET', 'POONAWALLA', 'PANACEABIO', 'ORIENTTECH', 'IIFL', 'GODREJPROP', 'ETERNAL', 'ENGINERSIN', 'DEVYANI', 'ASHAPURMIN', 'ARISINFRA']
[1:45:30 pm] ACTIVELY SUBSCRIBED: 4 stocks - ['ANANTRAJ', 'SIGNATURE', 'KALYANKJIL', 'BALUFORGE']
[1:45:30 pm] ==================================================
[1:45:30 pm] === REVERSAL BOT INITIALIZED ===
[1:45:30 pm] Using modular architecture with state management and self-contained tick processing
[1:45:30 pm] Cross-contamination bugs eliminated - each stock processes only its own price
[1:45:30 pm] === PREP TIME: Loading metadata and preparing data ===
[1:45:34 pm] OK Stock metadata loaded for scoring
[1:45:34 pm] VIP Stock: ANANTRAJ-d14 (7+ days, any trend)
[1:45:34 pm] VIP Stock: TEJASNET-d15 (7+ days, any trend)
[1:45:34 pm] VIP Stock: SIGNATURE-d15 (7+ days, any trend)
[1:45:34 pm] Tertiary Stock: POONAWALLA-u6 (3-6 days, uptrend)
[1:45:34 pm] VIP Stock: PANACEABIO-d11 (7+ days, any trend)
[1:45:34 pm] VIP Stock: ORIENTTECH-d15 (7+ days, any trend)
[1:45:34 pm] VIP Stock: KALYANKJIL-d12 (7+ days, any trend)
[1:45:34 pm] VIP Stock: IIFL-d13 (7+ days, any trend)
[1:45:34 pm] VIP Stock: GODREJPROP-d14 (7+ days, any trend)
[1:45:34 pm] Secondary Stock: ETERNAL-d3 (3-6 days, downtrend)
[1:45:34 pm] VIP Stock: ENGINERSIN-d15 (7+ days, any trend)
[1:45:34 pm] VIP Stock: DEVYANI-d15 (7+ days, any trend)
[1:45:34 pm] VIP Stock: BALUFORGE-d14 (7+ days, any trend)
[1:45:34 pm] VIP Stock: ASHAPURMIN-u9 (7+ days, any trend)
[1:45:34 pm] VIP Stock: ARISINFRA-d15 (7+ days, any trend)
[1:45:34 pm] Loaded 15 reversal stocks: 13 VIP, 1 secondary, 1 tertiary
[1:45:34 pm] OK Reversal watchlist loaded
[1:45:37 pm] VIP #1: GODREJPROP (Score: 22, ADR: 5.2%)
[1:45:37 pm] VIP #2: SIGNATURE (Score: 19, ADR: 5.9%)
[1:45:37 pm] VIP #3: IIFL (Score: 19, ADR: 6.0%)
[1:45:37 pm] VIP #4: ASHAPURMIN (Score: 19, ADR: 7.5%)
[1:45:37 pm] VIP #5: ANANTRAJ (Score: 17, ADR: 5.1%)
[1:45:37 pm] VIP #6: TEJASNET (Score: 17, ADR: 6.3%)
[1:45:37 pm] VIP #7: PANACEABIO (Score: 17, ADR: 6.2%)
[1:45:37 pm] VIP #8: ORIENTTECH (Score: 17, ADR: 7.8%)
[1:45:37 pm] VIP #9: KALYANKJIL (Score: 17, ADR: 6.3%)
[1:45:37 pm] VIP #10: BALUFORGE (Score: 17, ADR: 9.1%)
[1:45:37 pm] VIP #11: ARISINFRA (Score: 15, ADR: 8.9%)
[1:45:37 pm] VIP #12: ENGINERSIN (Score: 13, ADR: 4.1%)
[1:45:37 pm] VIP #13: DEVYANI (Score: 13, ADR: 4.5%)
[1:45:37 pm] Secondary #1: ETERNAL (Score: 17, ADR: 5.0%)
[1:45:37 pm] Tertiary #1: POONAWALLA (Score: 15, ADR: 4.8%)
[1:45:37 pm] Stock ranking completed - higher ranked stocks will be monitored first
[1:45:37 pm] WAITING 22 seconds until market open...
[1:46:00 pm] === STARTING REVERSAL TRADING PHASE ===
[1:46:00 pm] ATTEMPTING to connect to data stream...
[1:46:00 pm] Connecting to Market Data Feed...
[1:46:00 pm] CONNECTED Data stream connected
[1:46:00 pm] MARKET OPEN! Monitoring live tick data...
[1:46:00 pm] WAITING 60 seconds until entry time...
[1:46:00 pm] WebSocket OPENED at 13:46:00
[1:46:01 pm] Subscribed to 15 instruments in 'full' mode (LTP + OHLC) at 13:46:01
[1:47:00 pm] === PREPARING ENTRIES ===
[1:47:00 pm] POST-REVERSAL QUALIFICATION STATUS:
[1:47:00 pm] ANANTRAJ (Rev-D): Open: Rs481.50 | Gap validated | Low not checked
[1:47:00 pm] TEJASNET (Rev-D): Open: Rs335.40 | Gap: +13.3% | Low not checked | REJECTED: Gap up or flat: 13.3% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] SIGNATURE (Rev-D): Open: Rs811.80 | Gap validated | Low not checked
[1:47:00 pm] POONAWALLA (Rev-U): Open: Rs403.05 | Gap: -0.3% | Low not checked | REJECTED: Gap down or flat: -0.3% (need gap up > 0.3% for reversal_s1)
[1:47:00 pm] PANACEABIO (Rev-D): Open: Rs355.35 | Gap: +2.2% | Low not checked | REJECTED: Gap up or flat: 2.2% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] ORIENTTECH (Rev-D): Open: Rs329.30 | Gap: +1.3% | Low not checked | REJECTED: Gap up or flat: 1.3% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] KALYANKJIL (Rev-D): Open: Rs363.75 | Gap validated | Low not checked
[1:47:00 pm] IIFL (Rev-D): Open: Rs541.75 | Gap: +3.8% | Low not checked | REJECTED: Gap up or flat: 3.8% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] GODREJPROP (Rev-D): Open: Rs1529.20 | Gap: +0.7% | Low not checked | REJECTED: Gap up or flat: 0.7% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] ETERNAL (Rev-D): Open: Rs261.85 | Gap: +3.2% | Low not checked | REJECTED: Gap up or flat: 3.2% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] ENGINERSIN (Rev-D): Open: Rs170.26 | Gap: +3.5% | Low not checked | REJECTED: Gap up or flat: 3.5% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] DEVYANI (Rev-D): Open: Rs114.01 | Gap: +2.1% | Low not checked | REJECTED: Gap up or flat: 2.1% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] BALUFORGE (Rev-D): Open: Rs353.40 | Gap validated | Low not checked
[1:47:00 pm] ASHAPURMIN (Rev-D): Open: Rs646.00 | Gap: +1.1% | Low not checked | REJECTED: Gap up or flat: 1.1% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] ARISINFRA (Rev-D): Open: Rs104.84 | Gap: +4.1% | Low not checked | REJECTED: Gap up or flat: 4.1% (need gap down < -0.3% for reversal_s2)
[1:47:00 pm] =======================================================
[1:47:00 pm] PHASE 2: CHECKING LOW VIOLATIONS
[1:47:00 pm] =======================================================
[1:47:00 pm] No low violations detected
[1:47:00 pm] === SUBSCRIPTION STATUS ===
[1:47:00 pm] INITIALIZED: 4 stocks - ['ANANTRAJ', 'SIGNATURE', 'KALYANKJIL', 'BALUFORGE']
[1:47:00 pm] REJECTED: 11 stocks - ['TEJASNET', 'POONAWALLA', 'PANACEABIO', 'ORIENTTECH', 'IIFL', 'GODREJPROP', 'ETERNAL', 'ENGINERSIN', 'DEVYANI', 'ASHAPURMIN', 'ARISINFRA']
[1:47:00 pm] ACTIVELY SUBSCRIBED: 4 stocks - ['ANANTRAJ', 'SIGNATURE', 'KALYANKJIL', 'BALUFORGE']
[1:47:00 pm] ==================================================
[1:47:00 pm] Qualified stocks: 4
[1:47:00 pm] Selected stocks: ['SIGNATURE', 'ANANTRAJ']
[1:47:00 pm] =======================================================
[1:47:00 pm] PHASE 3: SELECTION AND UNSUBSCRIBING NON-SELECTED
[1:47:00 pm] =======================================================
[1:47:00 pm] Reversal bot error: unsupported format string passed to NoneType.__format__
[1:47:00 pm] [UNLOCK] Reversal bot singleton lock released
[1:47:00 pm] Reversal bot shutdown complete

## GOT IT! 🎯

Looking at the logs:

**Qualified stocks:** 4 stocks (ANANTRAJ, SIGNATURE, KALYANKJIL, BALUFORGE)
**Selected stocks:** 2 stocks (SIGNATURE, ANANTRAJ)

**The Key Line:**
```
ANANTRAJ (Rev-D): Open: Rs481.50 | Gap validated | Low not checked
```

Notice: **"Low not checked"** ❌

## The Problem

All 4 qualified stocks have `low_violation_checked = False`!

Looking at the logic in `reversal_stock_monitor.py`:

```python
def get_qualified_stocks(self) -> List[ReversalStockState]:
    """Get stocks that passed gap and low violation checks"""
    for stock in self.stocks.values():
        # For reversals: only gap and low violation required
        if stock.is_active and stock.gap_validated and stock.low_violation_checked:
            qualified.append(stock)
```

**But the logs show stocks are being returned as "qualified" even though `low_violation_checked = False`!**

This means:
1. The stocks shouldn't be qualified yet
2. `prepare_entry()` doesn't get called on them
3. Their `entry_high` and `entry_sl` remain `None`
4. Phase 3 tries to format `None` → **CRASH**

## Root Cause

Look at the sequence in `run_reversal.py`:

```python
# Line 356: Prepare entries BEFORE checking violations
monitor.prepare_entries()

# Line 360: PHASE 2 - Check violations 
integration.phase_2_unsubscribe_after_low_violation()

# Line 362: Get qualified stocks
qualified_stocks = monitor.get_qualified_stocks()
```

**The issue:** `monitor.prepare_entries()` is called on line 356, which calls `get_qualified_stocks()` internally. But at this point, `low_violation_checked` is still `False` for all stocks!

So when `prepare_entries()` calls `get_qualified_stocks()`, it should return 0 stocks, but somehow it's returning 4 stocks.

## Let Me Check Something

In `reversal_stock_monitor.py`, the `check_low_violation()` method sets `low_violation_checked = True`:

```python
def check_low_violation(self) -> bool:
    """Check if low dropped below 1% of open price"""
    # ... checking logic ...
    self.low_violation_checked = True
    return True
```

And `check_violations()` calls this:

```python
def check_violations(self):
    """Check for low violations for opened stocks that haven't been checked yet"""
    for stock in self.get_active_stocks():
        if stock.gap_validated and not stock.low_violation_checked and stock.open_price:
            stock.check_low_violation()
```

**But Phase 2 happens AFTER prepare_entries()!**

## The Fix

The order in `run_reversal.py` is wrong. It should be:

```python
# FIRST: Check low violations
integration.phase_2_unsubscribe_after_low_violation()

# THEN: Prepare entries (now stocks have low_violation_checked = True)
monitor.prepare_entries()

# THEN: Get qualified and select
qualified_stocks = monitor.get_qualified_stocks()
selected_stocks = selection_engine.select_stocks(qualified_stocks)
```

**But wait...** that still doesn't explain why `get_qualified_stocks()` is returning stocks with `low_violation_checked = False`.

Let me look at the implementation again... I think there might be a different version of `get_qualified_stocks()` being used, or the logic was changed.

**Can you confirm: Does the version of `get_qualified_stocks()` in your actual code match what I see in the uploaded file?**

well if they are oops candidate right in this case low doesn't matter only for SS the low matters

**AH! You're absolutely right!** 🎯

For **OOPS candidates (reversal_s2)**, the low violation check doesn't matter at all! They just need:
1. Gap down validated 
2. That's it!

For **Strong Start candidates (reversal_s1)**, they need:
1. Gap up validated 
2. Low violation check passed 

So the logic in `get_qualified_stocks()` is **wrong**. It's checking `low_violation_checked` for ALL stocks, but it should only check it for Strong Start (reversal_s1) stocks!

## The Bug in `get_qualified_stocks()`

In `reversal_stock_monitor.py`:

```python
def get_qualified_stocks(self) -> List[ReversalStockState]:
    """Get stocks that passed gap and low violation checks"""
    for stock in self.stocks.values():
        # For reversals: only gap and low violation required
        if stock.is_active and stock.gap_validated and stock.low_violation_checked:
            qualified.append(stock)
```

This is checking `low_violation_checked` for ALL stocks, but it should be:

```python
def get_qualified_stocks(self) -> List[ReversalStockState]:
    """Get stocks that passed gap validation (and low check for Strong Start)"""
    for stock in self.stocks.values():
        # OOPS (reversal_s2): Only needs gap validated
        if stock.situation == 'reversal_s2':
            if stock.is_active and stock.gap_validated:
                qualified.append(stock)
        
        # Strong Start (reversal_s1): Needs gap validated AND low violation checked
        elif stock.situation == 'reversal_s1':
            if stock.is_active and stock.gap_validated and stock.low_violation_checked:
                qualified.append(stock)
```

## But Then Why Are They Qualified in the Logs?

Looking at your log:
```
Qualified stocks: 4
```

All 4 stocks (ANANTRAJ, SIGNATURE, KALYANKJIL, BALUFORGE) are reversal_s2 (OOPS), so they ARE qualified even without the low check.

**So the actual bug is:** `prepare_entry()` is being called on them, but their `entry_high` and `entry_sl` are still `None` when Phase 3 tries to log them.

## Why Are `entry_high` and `entry_sl` Still `None`?

Looking at `prepare_entry()` in `reversal_stock_monitor.py`:

```python
def prepare_entry(self):
    """Called when stock is qualified to set entry levels"""
    if not self.is_active:
        return
    
    # Set entry high as the high reached so far
    self.entry_high = self.daily_high
    
    # Set stop loss 4% below entry high
    self.entry_sl = self.entry_high * (1 - ENTRY_SL_PCT)
```

**The problem:** `self.daily_high` is initialized as `float('-inf')` and only gets updated when ticks are processed!

**But:** Between 1:45:30 (when stocks were subscribed) and 1:47:00 (when prepare_entries is called), there's been **1 minute and 30 seconds** of market data. So `daily_high` should have been updated with tick data.

**UNLESS...** the stocks haven't received any ticks yet, or the ticks aren't being processed because the stocks are in the wrong state!

## Let Me Check the State Machine

Looking at the logs again:
```
INITIALIZED: 4 stocks - ['ANANTRAJ', 'SIGNATURE', 'KALYANKJIL', 'BALUFORGE']
```

The stocks are in `INITIALIZED` state at 1:47:00 (entry time).

Now look at `tick_processor.py`:

```python
def process_tick(self, price: float, timestamp: datetime, reversal_monitor=None):
    # Route to state-specific handlers
    if self.stock.is_in_state(self.stock.state, 'monitoring_entry'):
        self._handle_entry_monitoring(price, timestamp, reversal_monitor)
```

**The stocks need to be in `MONITORING_ENTRY` state to process entry ticks!**

But they're in `INITIALIZED` state, so ticks are being **ignored**!

That's why:
- `daily_high` is still `float('-inf')`
- `entry_high` becomes `float('-inf')` 
- `entry_sl` becomes some negative number
- When formatting tries to print them... **BOOM!**

Actually wait, `float('-inf')` should format fine with `.2f`. Let me think...

**Actually, I bet `entry_high` and `entry_sl` are still literally `None` because `prepare_entry()` is never being called successfully, OR the stocks aren't transitioning to the right state.**

**Can you add some debug logging right before the Phase 3 error to see what the actual values are?**

Or we can just add the None-check fix since that's the safest solution regardless of the root cause.