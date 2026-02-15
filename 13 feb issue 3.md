[2:51:09 pm] LAUNCHING CONTINUATION BOT (OHLC-only)...
[2:51:09 pm] Starting src/trading/live_trading/run_continuation.py...
[2:51:09 pm] [LOCK] Continuation bot singleton lock acquired
[2:51:09 pm] STARTING CONTINUATION TRADING BOT (OHLC-ONLY)
[2:51:09 pm] ==================================================
[2:51:09 pm] CONFIG: Real market trading configuration loaded
[2:51:09 pm] CONFIG: Market open: 14:53:00
[2:51:09 pm] CONFIG: Entry time: 14:54:00
[2:51:09 pm] CONFIG: API poll delay: 5 seconds
[2:51:09 pm] CONFIG: Max positions: 2
[2:51:09 pm] CONFIG: Entry SL: 4.0%
[2:51:09 pm] CONFIG: Low violation: 1.0%
[2:51:09 pm] CONFIG: Strong start gap: 0.3%
[2:51:10 pm] Time: 2026-02-13 14:51:10 IST
[2:51:10 pm] LOADED 15 continuation stocks:
[2:51:10 pm] ADANIPOWER: SVRO Continuation
[2:51:10 pm] ANGELONE: SVRO Continuation
[2:51:10 pm] ELECON: SVRO Continuation
[2:51:10 pm] GRSE: SVRO Continuation
[2:51:10 pm] HINDCOPPER: SVRO Continuation
[2:51:10 pm] MIDHANI: SVRO Continuation
[2:51:10 pm] MOSCHIP: SVRO Continuation
[2:51:10 pm] NAVNETEDUL: SVRO Continuation
[2:51:10 pm] PATELRMART: SVRO Continuation
[2:51:10 pm] PICCADIL: SVRO Continuation
[2:51:10 pm] ROSSTECH: SVRO Continuation
[2:51:10 pm] SHANTIGOLD: SVRO Continuation
[2:51:10 pm] SHRINGARMS: SVRO Continuation
[2:51:10 pm] UNIONBANK: SVRO Continuation
[2:51:10 pm] WALCHANNAG: SVRO Continuation
[2:51:11 pm] OK ADANIPOWER: Rs149.79
[2:51:11 pm] OK ANGELONE: Rs2752.00
[2:51:11 pm] OK ELECON: Rs444.70
[2:51:12 pm] OK GRSE: Rs2496.20
[2:51:12 pm] OK HINDCOPPER: Rs624.70
[2:51:13 pm] OK MIDHANI: Rs369.05
[2:51:13 pm] OK MOSCHIP: Rs195.52
[2:51:14 pm] OK NAVNETEDUL: Rs156.29
[2:51:14 pm] OK PATELRMART: Rs200.18
[2:51:14 pm] OK PICCADIL: Rs612.35
[2:51:14 pm] OK ROSSTECH: Rs712.55
[2:51:14 pm] OK SHANTIGOLD: Rs217.93
[2:51:15 pm] OK SHRINGARMS: Rs240.04
[2:51:15 pm] OK UNIONBANK: Rs181.00
[2:51:15 pm] OK WALCHANNAG: Rs174.80
[2:51:15 pm] PREPARED 15 continuation instruments
[2:51:15 pm] === CONTINUATION BOT INITIALIZED ===
[2:51:15 pm] Using pure OHLC processing - no tick-based opening prices
[2:51:15 pm] === PREP TIME: Loading metadata and preparing data ===
[2:51:20 pm] OK Stock metadata loaded for scoring
[2:51:20 pm] LOADING mean volume baselines from cache...
[2:51:20 pm] Mean volume baseline for ADANIPOWER: 24,841,115.2
[2:51:20 pm] Mean volume baseline for ANGELONE: 1,382,061.8
[2:51:20 pm] Mean volume baseline for ELECON: 738,324.0
[2:51:20 pm] Mean volume baseline for GRSE: 1,324,695.2
[2:51:20 pm] Mean volume baseline for HINDCOPPER: 37,308,234.2
[2:51:20 pm] Mean volume baseline for MIDHANI: 742,010.8
[2:51:20 pm] Mean volume baseline for MOSCHIP: 2,661,381.8
[2:51:20 pm] Mean volume baseline for NAVNETEDUL: 546,033.1
[2:51:20 pm] Mean volume baseline for PATELRMART: 185,406.3
[2:51:20 pm] Mean volume baseline for PICCADIL: 112,048.4
[2:51:20 pm] Mean volume baseline for ROSSTECH: 337,130.5
[2:51:20 pm] Mean volume baseline for SHANTIGOLD: 929,578.3
[2:51:20 pm] Mean volume baseline for SHRINGARMS: 1,403,967.8
[2:51:20 pm] Mean volume baseline for UNIONBANK: 11,980,475.3
[2:51:20 pm] Mean volume baseline for WALCHANNAG: 1,461,388.2
[2:51:20 pm] Calculating VAH from previous day's volume profile...
[2:51:20 pm] Continuation symbols: ['ADANIPOWER', 'ANGELONE', 'ELECON', 'GRSE', 'HINDCOPPER', 'MIDHANI', 'MOSCHIP', 'NAVNETEDUL', 'PATELRMART', 'PICCADIL', 'ROSSTECH', 'SHANTIGOLD', 'SHRINGARMS', 'UNIONBANK', 'WALCHANNAG']
[2:51:22 pm] VAH calculated for 15 continuation stocks
[2:51:22 pm] VAH results saved to vah_results.json
[2:51:22 pm] VAH CALCULATION RESULTS:
[2:51:22 pm] [OK] ADANIPOWER: Upper Range (VAH) = Rs149.93
[2:51:22 pm] [OK] ANGELONE: Upper Range (VAH) = Rs2745.08
[2:51:22 pm] [OK] ELECON: Upper Range (VAH) = Rs452.63
[2:51:22 pm] [OK] GRSE: Upper Range (VAH) = Rs2499.93
[2:51:22 pm] [OK] HINDCOPPER: Upper Range (VAH) = Rs628.37
[2:51:22 pm] [OK] MIDHANI: Upper Range (VAH) = Rs369.93
[2:51:22 pm] [OK] MOSCHIP: Upper Range (VAH) = Rs197.13
[2:51:22 pm] [OK] NAVNETEDUL: Upper Range (VAH) = Rs157.33
[2:51:22 pm] [OK] PATELRMART: Upper Range (VAH) = Rs205.93
[2:51:22 pm] [OK] PICCADIL: Upper Range (VAH) = Rs620.87
[2:51:22 pm] [OK] ROSSTECH: Upper Range (VAH) = Rs707.77
[2:51:22 pm] [OK] SHANTIGOLD: Upper Range (VAH) = Rs219.44
[2:51:22 pm] [OK] SHRINGARMS: Upper Range (VAH) = Rs243.33
[2:51:22 pm] [OK] UNIONBANK: Upper Range (VAH) = Rs182.14
[2:51:22 pm] [OK] WALCHANNAG: Upper Range (VAH) = Rs176.38
[2:51:22 pm] Summary: 15 stocks successfully calculated
[2:51:22 pm] === PRE-MARKET IEP FETCH SEQUENCE ===
[2:51:22 pm] WAITING 67 seconds until PREP_START (14:52:30)...
[2:52:30 pm] FETCHING IEP for 15 continuation stocks...
[2:52:30 pm] IEP FETCH COMPLETED SUCCESSFULLY
[2:52:30 pm] Set opening price for NAVNETEDUL: Rs155.86
[2:52:30 pm] Gap validation failed for NAVNETEDUL
[2:52:30 pm] VAH validation failed for NAVNETEDUL (Opening price 155.86 < VAH 157.33)
[2:52:30 pm] Set opening price for ELECON: Rs434.45
[2:52:30 pm] Gap validation failed for ELECON
[2:52:30 pm] VAH validation failed for ELECON (Opening price 434.45 < VAH 452.63)
[2:52:30 pm] Set opening price for ADANIPOWER: Rs140.31
[2:52:30 pm] Gap validation failed for ADANIPOWER
[2:52:30 pm] VAH validation failed for ADANIPOWER (Opening price 140.31 < VAH 149.93)
[2:52:30 pm] Set opening price for PICCADIL: Rs587.65
[2:52:30 pm] Gap validation failed for PICCADIL
[2:52:30 pm] VAH validation failed for PICCADIL (Opening price 587.65 < VAH 620.87)
[2:52:30 pm] Set opening price for SHRINGARMS: Rs237.66
[2:52:30 pm] Gap validation failed for SHRINGARMS
[2:52:30 pm] VAH validation failed for SHRINGARMS (Opening price 237.66 < VAH 243.33)
[2:52:30 pm] Set opening price for HINDCOPPER: Rs597.10
[2:52:30 pm] Gap validation failed for HINDCOPPER
[2:52:30 pm] VAH validation failed for HINDCOPPER (Opening price 597.10 < VAH 628.37)
[2:52:30 pm] Set opening price for ROSSTECH: Rs719.10
[2:52:30 pm] Gap validated for ROSSTECH
[2:52:30 pm] VAH validated for ROSSTECH
[2:52:30 pm] Set opening price for MOSCHIP: Rs190.61
[2:52:30 pm] Gap validation failed for MOSCHIP
[2:52:30 pm] VAH validation failed for MOSCHIP (Opening price 190.61 < VAH 197.13)
[2:52:30 pm] Set opening price for UNIONBANK: Rs178.80
[2:52:30 pm] Gap validation failed for UNIONBANK
[2:52:30 pm] VAH validation failed for UNIONBANK (Opening price 178.80 < VAH 182.14)
[2:52:30 pm] Set opening price for SHANTIGOLD: Rs219.00
[2:52:30 pm] Gap validated for SHANTIGOLD
[2:52:30 pm] VAH validation failed for SHANTIGOLD (Opening price 219.00 < VAH 219.44)
[2:52:30 pm] Set opening price for GRSE: Rs2439.20
[2:52:30 pm] Gap validation failed for GRSE
[2:52:30 pm] VAH validation failed for GRSE (Opening price 2439.20 < VAH 2499.93)
[2:52:30 pm] Set opening price for WALCHANNAG: Rs170.33
[2:52:30 pm] Gap validation failed for WALCHANNAG
[2:52:30 pm] VAH validation failed for WALCHANNAG (Opening price 170.33 < VAH 176.38)
[2:52:30 pm] Set opening price for ANGELONE: Rs2710.60
[2:52:30 pm] Gap validation failed for ANGELONE
[2:52:30 pm] VAH validation failed for ANGELONE (Opening price 2710.60 < VAH 2745.08)
[2:52:30 pm] Set opening price for MIDHANI: Rs360.05
[2:52:30 pm] Gap validation failed for MIDHANI
[2:52:30 pm] VAH validation failed for MIDHANI (Opening price 360.05 < VAH 369.93)
[2:52:30 pm] Set opening price for PATELRMART: Rs193.39
[2:52:30 pm] Gap validation failed for PATELRMART
[2:52:30 pm] VAH validation failed for PATELRMART (Opening price 193.39 < VAH 205.93)
[2:52:30 pm] === STARTING CONTINUATION TRADING PHASE ===
[2:52:30 pm] ATTEMPTING to connect to data stream...
[2:52:30 pm] Connecting to Market Data Feed...
[2:52:30 pm] CONNECTED Data stream connected
[2:52:30 pm] WAITING 30 seconds for market open...
[2:52:30 pm] WebSocket OPENED at 14:52:30
[2:52:31 pm] Subscribed to 15 instruments in 'full' mode (LTP + OHLC) at 14:52:31
[2:52:31 pm] [TICK DEBUG] 14:52:31 - NAVNETEDUL: Rs155.86
[2:52:31 pm] [TICK DEBUG] 14:52:31 - MOSCHIP: Rs190.61
[2:52:31 pm] [TICK DEBUG] 14:52:31 - SHANTIGOLD: Rs219.00
[2:52:31 pm] [TICK DEBUG] 14:52:31 - PATELRMART: Rs193.39
[2:52:31 pm] [TICK DEBUG] 14:52:31 - ELECON: Rs434.45
[2:52:31 pm] [TICK DEBUG] 14:52:31 - UNIONBANK: Rs178.80
[2:52:31 pm] [TICK DEBUG] 14:52:31 - ROSSTECH: Rs719.10
[2:52:31 pm] [TICK PROCESSOR] 14:52:31 - ROSSTECH: Processing tick Rs719.10
[2:52:31 pm] [TRACKING] 14:52:31 - ROSSTECH: Price Rs719.10, Daily High: Rs719.10, Open: Rs719.10
[2:52:31 pm] [TRACKING] 14:52:31 - ROSSTECH: Updated Entry High: Rs719.10, SL: Rs690.34
[2:52:31 pm] ENTRY ROSSTECH entered at Rs719.10, SL placed at Rs690.34
[2:52:31 pm] [TICK DEBUG] 14:52:31 - MIDHANI: Rs359.95
[2:52:31 pm] [TICK DEBUG] 14:52:31 - GRSE: Rs2439.20
[2:52:31 pm] [TICK DEBUG] 14:52:31 - WALCHANNAG: Rs170.33
[2:52:31 pm] [TICK DEBUG] 14:52:31 - PICCADIL: Rs587.65
[2:52:31 pm] [TICK DEBUG] 14:52:31 - HINDCOPPER: Rs597.10
[2:52:31 pm] [TICK DEBUG] 14:52:31 - ANGELONE: Rs2710.60
[2:52:31 pm] [TICK DEBUG] 14:52:31 - ADANIPOWER: Rs140.29
[2:52:31 pm] [TICK DEBUG] 14:52:31 - SHRINGARMS: Rs237.66
[2:52:31 pm] [TICK DEBUG] 14:52:31 - HINDCOPPER: Rs597.10
[2:52:31 pm] [TICK DEBUG] 14:52:31 - ANGELONE: Rs2710.60
[2:52:32 pm] [TICK DEBUG] 14:52:32 - UNIONBANK: Rs178.80
[2:52:32 pm] [TICK DEBUG] 14:52:32 - GRSE: Rs2440.20
[2:52:32 pm] [TICK DEBUG] 14:52:32 - ADANIPOWER: Rs140.29
[2:52:32 pm] [TICK DEBUG] 14:52:32 - ANGELONE: Rs2711.50
[2:52:32 pm] [TICK DEBUG] 14:52:32 - HINDCOPPER: Rs597.10
[2:52:32 pm] [TICK DEBUG] 14:52:32 - GRSE: Rs2440.00
[2:52:33 pm] [TICK DEBUG] 14:52:33 - ELECON: Rs434.45
[2:52:33 pm] [TICK DEBUG] 14:52:33 - UNIONBANK: Rs178.80
[2:52:33 pm] [TICK DEBUG] 14:52:33 - SHANTIGOLD: Rs218.89
[2:52:33 pm] [TICK DEBUG] 14:52:33 - HINDCOPPER: Rs596.90
[2:52:33 pm] [TICK DEBUG] 14:52:33 - ELECON: Rs434.45
[2:52:33 pm] [TICK DEBUG] 14:52:33 - UNIONBANK: Rs178.80
[2:52:33 pm] [TICK DEBUG] 14:52:33 - SHANTIGOLD: Rs218.89



after unsubbing we still receiving ticks

we did the test called test_unsubcription_logic.py it says it was not receiving ticks after it and we have implemented the same stuff here


test_real_unsubscription.py

