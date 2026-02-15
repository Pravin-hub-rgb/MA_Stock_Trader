[8:53:50 am] LAUNCHING CONTINUATION BOT (OHLC-only)...
[8:53:50 am] Starting src/trading/live_trading/run_continuation.py...
[8:53:50 am] [LOCK] Continuation bot singleton lock acquired
[8:53:50 am] STARTING CONTINUATION TRADING BOT (OHLC-ONLY)
[8:53:50 am] ==================================================
[8:53:50 am] CONFIG: Real market trading configuration loaded
[8:53:50 am] CONFIG: Market open: 09:15:00
[8:53:50 am] CONFIG: Entry time: 09:20:00
[8:53:50 am] CONFIG: API poll delay: 5 seconds
[8:53:50 am] CONFIG: Max positions: 2
[8:53:50 am] CONFIG: Entry SL: 4.0%
[8:53:50 am] CONFIG: Low violation: 1.0%
[8:53:50 am] CONFIG: Strong start gap: 0.3%
[8:53:51 am] Time: 2026-02-11 08:53:51 IST
[8:53:51 am] LOADED 12 continuation stocks:
[8:53:51 am] ADANIPOWER: SVRO Continuation
[8:53:51 am] AWHCL: SVRO Continuation
[8:53:51 am] CUBEXTUB: SVRO Continuation
[8:53:51 am] CUPID: SVRO Continuation
[8:53:51 am] DCBBANK: SVRO Continuation
[8:53:51 am] GROWW: SVRO Continuation
[8:53:51 am] HINDCOPPER: SVRO Continuation
[8:53:51 am] MOSCHIP: SVRO Continuation
[8:53:51 am] PATELRMART: SVRO Continuation
[8:53:51 am] REDTAPE: SVRO Continuation
[8:53:51 am] UNIONBANK: SVRO Continuation
[8:53:51 am] WALCHANNAG: SVRO Continuation
[8:53:52 am] OK ADANIPOWER: Rs149.05
[8:53:52 am] OK AWHCL: Rs527.50
[8:53:53 am] OK CUBEXTUB: Rs113.28
[8:53:53 am] OK CUPID: Rs434.95
[8:53:53 am] OK DCBBANK: Rs198.58
[8:53:53 am] OK GROWW: Rs168.62
[8:53:54 am] OK HINDCOPPER: Rs598.00
[8:53:54 am] OK MOSCHIP: Rs199.91
[8:53:54 am] OK PATELRMART: Rs209.35
[8:53:54 am] OK REDTAPE: Rs128.73
[8:53:55 am] OK UNIONBANK: Rs179.98
[8:53:55 am] OK WALCHANNAG: Rs180.40
[8:53:55 am] PREPARED 12 continuation instruments
[8:53:55 am] === CONTINUATION BOT INITIALIZED ===
[8:53:55 am] Using pure OHLC processing - no tick-based opening prices
[8:53:55 am] === PREP TIME: Loading metadata and preparing data ===
[8:53:59 am] OK Stock metadata loaded for scoring
[8:53:59 am] LOADING mean volume baselines from cache...
[8:53:59 am] Mean volume baseline for ADANIPOWER: 27,118,555.9
[8:53:59 am] Mean volume baseline for AWHCL: 395,435.7
[8:53:59 am] Mean volume baseline for CUBEXTUB: 970,234.8
[8:53:59 am] Mean volume baseline for CUPID: 10,202,684.6
[8:53:59 am] Mean volume baseline for DCBBANK: 2,473,323.7
[8:53:59 am] Mean volume baseline for GROWW: 41,783,393.3
[8:53:59 am] Mean volume baseline for HINDCOPPER: 58,690,422.3
[8:53:59 am] Mean volume baseline for MOSCHIP: 3,806,181.6
[8:53:59 am] Mean volume baseline for PATELRMART: 198,826.3
[8:53:59 am] Mean volume baseline for REDTAPE: 575,464.8
[8:53:59 am] Mean volume baseline for UNIONBANK: 15,241,153.9
[8:53:59 am] Mean volume baseline for WALCHANNAG: 4,319,594.8
[8:53:59 am] Calculating VAH from previous day's volume profile...
[8:53:59 am] Continuation symbols: ['ADANIPOWER', 'AWHCL', 'CUBEXTUB', 'CUPID', 'DCBBANK', 'GROWW', 'HINDCOPPER', 'MOSCHIP', 'PATELRMART', 'REDTAPE', 'UNIONBANK', 'WALCHANNAG']
[8:54:08 am] VAH calculated for 12 continuation stocks
[8:54:08 am] VAH results saved to vah_results.json
[8:54:08 am] VAH CALCULATION RESULTS:
[8:54:08 am] [OK] ADANIPOWER: Upper Range (VAH) = Rs149.54
[8:54:08 am] [OK] AWHCL: Upper Range (VAH) = Rs532.27
[8:54:08 am] [OK] CUBEXTUB: Upper Range (VAH) = Rs116.37
[8:54:08 am] [OK] CUPID: Upper Range (VAH) = Rs439.43
[8:54:08 am] [OK] DCBBANK: Upper Range (VAH) = Rs200.01
[8:54:08 am] [OK] GROWW: Upper Range (VAH) = Rs168.19
[8:54:08 am] [OK] HINDCOPPER: Upper Range (VAH) = Rs602.87
[8:54:08 am] [OK] MOSCHIP: Upper Range (VAH) = Rs204.48
[8:54:08 am] [OK] PATELRMART: Upper Range (VAH) = Rs212.86
[8:54:08 am] [OK] REDTAPE: Upper Range (VAH) = Rs130.77
[8:54:08 am] [OK] UNIONBANK: Upper Range (VAH) = Rs179.53
[8:54:08 am] [OK] WALCHANNAG: Upper Range (VAH) = Rs186.33
[8:54:08 am] Summary: 12 stocks successfully calculated
[8:54:08 am] === PRE-MARKET IEP FETCH SEQUENCE ===
[8:54:08 am] WAITING 1221 seconds until PREP_START (09:14:30)...
[9:14:30 am] FETCHING IEP for 12 continuation stocks...
[9:14:30 am] IEP FETCH COMPLETED SUCCESSFULLY
[9:14:30 am] Set opening price for DCBBANK: Rs200.05
[9:14:30 am] Gap validated for DCBBANK
[9:14:30 am] Set opening price for ADANIPOWER: Rs149.59
[9:14:30 am] Gap validated for ADANIPOWER
[9:14:30 am] Set opening price for WALCHANNAG: Rs181.00
[9:14:30 am] Gap validated for WALCHANNAG
[9:14:30 am] Set opening price for HINDCOPPER: Rs601.00
[9:14:30 am] Gap validated for HINDCOPPER
[9:14:30 am] Set opening price for CUBEXTUB: Rs113.85
[9:14:30 am] Gap validated for CUBEXTUB
[9:14:30 am] Set opening price for AWHCL: Rs526.00
[9:14:30 am] Gap validation failed for AWHCL
[9:14:30 am] Set opening price for CUPID: Rs437.45
[9:14:30 am] Gap validated for CUPID
[9:14:30 am] Set opening price for MOSCHIP: Rs202.63
[9:14:30 am] Gap validated for MOSCHIP
[9:14:30 am] Set opening price for REDTAPE: Rs128.50
[9:14:30 am] Gap validation failed for REDTAPE
[9:14:30 am] Set opening price for PATELRMART: Rs209.80
[9:14:30 am] Gap validation failed for PATELRMART
[9:14:30 am] Set opening price for GROWW: Rs170.00
[9:14:30 am] Gap validated for GROWW
[9:14:30 am] Set opening price for UNIONBANK: Rs179.98
[9:14:30 am] Gap validation failed for UNIONBANK
[9:14:30 am] === STARTING CONTINUATION TRADING PHASE ===
[9:14:30 am] ATTEMPTING to connect to data stream...
[9:14:30 am] Connecting to Market Data Feed...
[9:14:30 am] CONNECTED Data stream connected
[9:14:30 am] WAITING 30 seconds for market open...
[9:14:30 am] WebSocket OPENED at 09:14:30
[9:14:31 am] Subscribed to 12 instruments in 'full' mode (LTP + OHLC) at 09:14:31
[9:15:00 am] MARKET OPEN! Monitoring live OHLC data...
[9:15:00 am] NO initial volume capture needed - using current volume directly as cumulative
[9:15:00 am] USING IEP-BASED OPENING PRICES - Set at 9:14:30 from pre-market IEP
[9:15:00 am] Gap validation completed at 9:14:30, ready for trading
[9:15:00 am] WAITING 300 seconds until entry decision...
[9:20:00 am] === PREPARING ENTRIES ===
[9:20:00 am] POST-OHLC QUALIFICATION STATUS:
[9:20:00 am] ADANIPOWER (Cont): Open: Rs149.59 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] AWHCL (Cont): Open: Rs526.00 | Gap: -0.28% | Low not checked | Volume not checked | REJECTED: Gap too flat: -0.3% (within ±0.3% range)
[9:20:00 am] CUBEXTUB (Cont): Open: Rs113.85 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] CUPID (Cont): Open: Rs437.45 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] DCBBANK (Cont): Open: Rs200.05 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] GROWW (Cont): Open: Rs170.00 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] HINDCOPPER (Cont): Open: Rs601.00 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] MOSCHIP (Cont): Open: Rs202.63 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] PATELRMART (Cont): Open: Rs209.80 | Gap: +0.21% | Low not checked | Volume not checked | REJECTED: Gap too flat: 0.2% (within ±0.3% range)
[9:20:00 am] REDTAPE (Cont): Open: Rs128.50 | Gap: -0.18% | Low not checked | Volume not checked | REJECTED: Gap too flat: -0.2% (within ±0.3% range)
[9:20:00 am] UNIONBANK (Cont): Open: Rs179.98 | Gap: +0.00% | Low not checked | Volume not checked | REJECTED: Gap too flat: 0.0% (within ±0.3% range)
[9:20:00 am] WALCHANNAG (Cont): Open: Rs181.00 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] === APPLYING VAH VALIDATION ===
[9:20:00 am] === CHECKING LOW VIOLATIONS AND VOLUME VALIDATIONS ===
[9:20:00 am] Qualified stocks: 2
[9:20:00 am] READY to trade: DCBBANK (Entry: Rs200.05, SL: Rs192.05)
[9:20:00 am] READY to trade: GROWW (Entry: Rs170.00, SL: Rs163.20)
[9:20:00 am] MODULAR SUBSCRIPTION: All 2 qualified stocks subscribed
[9:20:00 am] MONITORING for entry/exit signals...
[9:20:00 am] Connection active - monitoring for signals...
[9:20:00 am] ENTRY GROWW entered at Rs170.66, SL placed at Rs163.83
[9:20:01 am] ENTRY GROWW entered at Rs170.66, SL placed at Rs163.91


first is twice entry
second is the window was of 5 min ass market start = 9:15 and entry time - 9:20 so during this preiod the high was 172.20 in grow but it say 170.66 
and why these stocks:

[9:20:00 am] GROWW (Cont): Open: Rs170.00 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] HINDCOPPER (Cont): Open: Rs601.00 | Gap validated | Low not checked | Volume not checked
[9:20:00 am] MOSCHIP (Cont): Open: Rs202.63 | Gap validated | Low not checked | Volume not checked

low and volume is not checked??????????
and grow was selcted but there it said low not checked + volume not checked ?? so why it passed as selected stocks??
it should pass all the test right..... 

I've analyzed the issues from your log file. Here are the root causes:

## Issue 1: Double Entry
**Root Cause**: In `integration.py`, `_handle_paper_trading_logs()` prints the entry message whenever `stock.entered=True` and entry_time is within 1 second of current timestamp. But it doesn't track if the log was already printed, so multiple ticks within that 1-second window cause duplicate log messages.

## Issue 2: High Not Captured (170.66 vs 172.20)
**Root Cause**: The `daily_high` isn't being properly updated from tick data between 9:15-9:20. Looking at `tick_processor.py`, `_track_entry_levels()` should update entry_high when daily_high increases, but `daily_high` relies on `update_price()` being called. The issue is that `process_tick()` calls `update_price()` first, but `_track_entry_levels()` uses `stock.daily_high` which may not include the current tick's price yet.

## Issue 3: "Low not checked | Volume not checked" Confusion
**Root Cause**: In `run_continuation.py`, the POST-OHLC QUALIFICATION STATUS is printed **BEFORE** `check_violations()` and `check_volume_validations()` are called. The actual checks happen after the status print, so the display is misleading.

---

## Proposed Fixes:

1. **Fix Double Entry**: Add an `entry_logged` flag to prevent duplicate entry logs
2. **Fix High Tracking**: Update `_track_entry_levels()` to consider the current tick price when comparing highs
3. **Fix Logging**: Either reorder the status print to after checks, or add clarifying messages

Would you like me to toggle to **Act Mode** to implement these fixes?