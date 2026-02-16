[10:56:02 am] LAUNCHING CONTINUATION BOT (OHLC-only)...
[10:56:02 am] Starting src/trading/live_trading/run_continuation.py...
[10:56:02 am] [LOCK] Continuation bot singleton lock acquired
[10:56:02 am] STARTING CONTINUATION TRADING BOT (OHLC-ONLY)
[10:56:02 am] ==================================================
[10:56:02 am] CONFIG: Real market trading configuration loaded
[10:56:02 am] CONFIG: Market open: 10:58:00
[10:56:02 am] CONFIG: Entry time: 11:03:00
[10:56:02 am] CONFIG: API poll delay: 5 seconds
[10:56:02 am] CONFIG: Max positions: 2
[10:56:02 am] CONFIG: Entry SL: 4.0%
[10:56:02 am] CONFIG: Low violation: 1.0%
[10:56:02 am] CONFIG: Strong start gap: 0.3%
[10:56:04 am] Time: 2026-02-16 10:56:04 IST
[10:56:04 am] LOADED 13 continuation stocks:
[10:56:04 am] ATHERENERG: SVRO Continuation
[10:56:04 am] CHENNPETRO: SVRO Continuation
[10:56:04 am] DATAPATTNS: SVRO Continuation
[10:56:04 am] ELECON: SVRO Continuation
[10:56:04 am] IDBI: SVRO Continuation
[10:56:04 am] INFOBEAN: SVRO Continuation
[10:56:04 am] LODHA: SVRO Continuation
[10:56:04 am] NAVNETEDUL: SVRO Continuation
[10:56:04 am] NLCINDIA: SVRO Continuation
[10:56:04 am] POONAWALLA: SVRO Continuation
[10:56:04 am] ROSSTECH: SVRO Continuation
[10:56:04 am] SHANTIGOLD: SVRO Continuation
[10:56:04 am] UNIONBANK: SVRO Continuation
[10:56:04 am] OK ATHERENERG: Rs708.25
[10:56:04 am] OK CHENNPETRO: Rs879.00
[10:56:05 am] OK DATAPATTNS: Rs2768.80
[10:56:05 am] OK ELECON: Rs434.20
[10:56:05 am] OK IDBI: Rs110.75
[10:56:05 am] OK INFOBEAN: Rs866.05
[10:56:06 am] OK LODHA: Rs1073.60
[10:56:06 am] OK NAVNETEDUL: Rs156.03
[10:56:06 am] OK NLCINDIA: Rs259.30
[10:56:06 am] OK POONAWALLA: Rs464.15
[10:56:06 am] OK ROSSTECH: Rs714.65
[10:56:07 am] OK SHANTIGOLD: Rs217.84
[10:56:07 am] OK UNIONBANK: Rs178.87
[10:56:07 am] PREPARED 13 continuation instruments
[10:56:07 am] === CONTINUATION BOT INITIALIZED ===
[10:56:07 am] Using pure OHLC processing - no tick-based opening prices
[10:56:07 am] === PREP TIME: Loading metadata and preparing data ===
[10:56:11 am] OK Stock metadata loaded for scoring
[10:56:11 am] LOADING mean volume baselines from cache...
[10:56:11 am] Mean volume baseline for ATHERENERG: 2,155,784.8
[10:56:11 am] Mean volume baseline for CHENNPETRO: 1,053,901.6
[10:56:11 am] Mean volume baseline for DATAPATTNS: 892,039.8
[10:56:11 am] Mean volume baseline for ELECON: 720,705.7
[10:56:11 am] Mean volume baseline for IDBI: 31,246,579.3
[10:56:11 am] Mean volume baseline for INFOBEAN: 672,379.5
[10:56:11 am] Mean volume baseline for LODHA: 1,498,887.2
[10:56:11 am] Mean volume baseline for NAVNETEDUL: 544,269.6
[10:56:11 am] Mean volume baseline for NLCINDIA: 1,556,416.6
[10:56:11 am] Mean volume baseline for POONAWALLA: 2,673,359.1
[10:56:11 am] Mean volume baseline for ROSSTECH: 331,533.3
[10:56:11 am] Mean volume baseline for SHANTIGOLD: 1,013,188.0
[10:56:11 am] Mean volume baseline for UNIONBANK: 11,495,112.4
[10:56:11 am] Calculating VAH from previous day's volume profile...
[10:56:11 am] Continuation symbols: ['ATHERENERG', 'CHENNPETRO', 'DATAPATTNS', 'ELECON', 'IDBI', 'INFOBEAN', 'LODHA', 'NAVNETEDUL', 'NLCINDIA', 'POONAWALLA', 'ROSSTECH', 'SHANTIGOLD', 'UNIONBANK']
[10:56:13 am] VAH calculated for 13 continuation stocks
[10:56:13 am] VAH results saved to vah_results.json
[10:56:13 am] VAH CALCULATION RESULTS:
[10:56:13 am] [OK] ATHERENERG: Upper Range (VAH) = Rs704.72
[10:56:13 am] [OK] CHENNPETRO: Upper Range (VAH) = Rs886.97
[10:56:13 am] [OK] DATAPATTNS: Upper Range (VAH) = Rs2773.23
[10:56:13 am] [OK] ELECON: Upper Range (VAH) = Rs436.23
[10:56:13 am] [OK] IDBI: Upper Range (VAH) = Rs112.69
[10:56:13 am] [OK] INFOBEAN: Upper Range (VAH) = Rs901.02
[10:56:13 am] [OK] LODHA: Upper Range (VAH) = Rs1077.17
[10:56:13 am] [OK] NAVNETEDUL: Upper Range (VAH) = Rs156.80
[10:56:13 am] [OK] NLCINDIA: Upper Range (VAH) = Rs256.28
[10:56:13 am] [OK] POONAWALLA: Upper Range (VAH) = Rs470.43
[10:56:13 am] [OK] ROSSTECH: Upper Range (VAH) = Rs732.67
[10:56:13 am] [OK] SHANTIGOLD: Upper Range (VAH) = Rs221.68
[10:56:13 am] [OK] UNIONBANK: Upper Range (VAH) = Rs179.98
[10:56:13 am] Summary: 13 stocks successfully calculated
[10:56:13 am] === PRE-MARKET IEP FETCH SEQUENCE ===
[10:56:13 am] WAITING 76 seconds until PREP_START (10:57:30)...
[10:57:30 am] FETCHING IEP for 13 continuation stocks...
[10:57:30 am] IEP FETCH COMPLETED SUCCESSFULLY
[10:57:30 am] Set opening price for NAVNETEDUL: Rs155.50
[10:57:30 am] Gap validation failed for NAVNETEDUL
[10:57:30 am] VAH validation failed for NAVNETEDUL (Opening price 155.50 < VAH 156.80)
[10:57:30 am] Set opening price for ELECON: Rs432.45
[10:57:30 am] Gap validation failed for ELECON
[10:57:30 am] VAH validation failed for ELECON (Opening price 432.45 < VAH 436.23)
[10:57:30 am] Set opening price for DATAPATTNS: Rs2855.10
[10:57:30 am] Gap validated for DATAPATTNS
[10:57:30 am] VAH validated for DATAPATTNS
[10:57:30 am] Set opening price for INFOBEAN: Rs877.65
[10:57:30 am] Gap validated for INFOBEAN
[10:57:30 am] VAH validation failed for INFOBEAN (Opening price 877.65 < VAH 901.02)
[10:57:30 am] Set opening price for LODHA: Rs1088.80
[10:57:30 am] Gap validated for LODHA
[10:57:30 am] VAH validated for LODHA
[10:57:30 am] Set opening price for IDBI: Rs109.40
[10:57:30 am] Gap validation failed for IDBI
[10:57:30 am] VAH validation failed for IDBI (Opening price 109.40 < VAH 112.69)
[10:57:30 am] Set opening price for ROSSTECH: Rs709.15
[10:57:30 am] Gap validation failed for ROSSTECH
[10:57:30 am] VAH validation failed for ROSSTECH (Opening price 709.15 < VAH 732.67)
[10:57:30 am] Set opening price for UNIONBANK: Rs176.78
[10:57:30 am] Gap validation failed for UNIONBANK
[10:57:30 am] VAH validation failed for UNIONBANK (Opening price 176.78 < VAH 179.98)
[10:57:30 am] Set opening price for CHENNPETRO: Rs879.50
[10:57:30 am] Gap validation failed for CHENNPETRO
[10:57:30 am] VAH validation failed for CHENNPETRO (Opening price 879.50 < VAH 886.97)
[10:57:30 am] Set opening price for ATHERENERG: Rs719.25
[10:57:30 am] Gap validated for ATHERENERG
[10:57:30 am] VAH validated for ATHERENERG
[10:57:30 am] Set opening price for NLCINDIA: Rs255.85
[10:57:30 am] Gap validation failed for NLCINDIA
[10:57:30 am] VAH validation failed for NLCINDIA (Opening price 255.85 < VAH 256.28)
[10:57:30 am] Set opening price for SHANTIGOLD: Rs216.89
[10:57:30 am] Gap validation failed for SHANTIGOLD
[10:57:30 am] VAH validation failed for SHANTIGOLD (Opening price 216.89 < VAH 221.68)
[10:57:30 am] Set opening price for POONAWALLA: Rs477.15
[10:57:30 am] Gap validated for POONAWALLA
[10:57:30 am] VAH validated for POONAWALLA
[10:57:30 am] === STARTING CONTINUATION TRADING PHASE ===
[10:57:30 am] ATTEMPTING to connect to data stream...
[10:57:30 am] Connecting to Market Data Feed...
[10:57:30 am] CONNECTED Data stream connected
[10:57:30 am] WAITING 30 seconds for market open...
[10:57:30 am] WebSocket OPENED at 10:57:30
[10:57:31 am] Subscribed to 13 active instruments in 'full' mode (LTP + OHLC) at 10:57:31
[10:57:31 am] ENTRY DATAPATTNS entered at Rs2855.10, SL placed at Rs2740.90
[10:57:31 am] ENTRY ATHERENERG entered at Rs719.25, SL placed at Rs690.48
[10:57:31 am] ENTRY LODHA entered at Rs1088.80, SL placed at Rs1045.25
[10:57:31 am] ENTRY POONAWALLA entered at Rs477.15, SL placed at Rs458.06
[10:58:00 am] MARKET OPEN! Monitoring live OHLC data...
[10:58:00 am] NO initial volume capture needed - using current volume directly as cumulative
[10:58:00 am] USING IEP-BASED OPENING PRICES - Set at 9:14:30 from pre-market IEP
[10:58:00 am] Gap validation completed at 9:14:30, ready for trading
[10:58:00 am] === CONTINUATION STOCK STATUS BEFORE PHASE 1 UNSUBSCRIPTION ===
[10:58:00 am] TOTAL STOCKS: 13
[10:58:00 am] UNSUBSCRIBED DUE TO GAP REJECTION (8):
[10:58:00 am] - CHENNPETRO (Gap: +0.06%)
[10:58:00 am] - ELECON (Gap: -0.40%)
[10:58:00 am] - IDBI (Gap: -1.22%)
[10:58:00 am] - NAVNETEDUL (Gap: -0.34%)
[10:58:00 am] - NLCINDIA (Gap: -1.33%)
[10:58:00 am] - ROSSTECH (Gap: -0.77%)
[10:58:00 am] - SHANTIGOLD (Gap: -0.44%)
[10:58:00 am] - UNIONBANK (Gap: -1.17%)
[10:58:00 am] UNSUBSCRIBED DUE TO VAH REJECTION (9):
[10:58:00 am] - CHENNPETRO (Opening: 879.50 < VAH: 886.97)
[10:58:00 am] - ELECON (Opening: 432.45 < VAH: 436.23)
[10:58:00 am] - IDBI (Opening: 109.40 < VAH: 112.69)
[10:58:00 am] - INFOBEAN (Opening: 877.65 < VAH: 901.02)
[10:58:00 am] - NAVNETEDUL (Opening: 155.50 < VAH: 156.80)
[10:58:00 am] - NLCINDIA (Opening: 255.85 < VAH: 256.28)
[10:58:00 am] - ROSSTECH (Opening: 709.15 < VAH: 732.67)
[10:58:00 am] - SHANTIGOLD (Opening: 216.89 < VAH: 221.68)
[10:58:00 am] - UNIONBANK (Opening: 176.78 < VAH: 179.98)
[10:58:00 am] STILL SUBSCRIBED (4):
[10:58:00 am] - ATHERENERG (Gap: +1.55%, VAH: VALIDATED)
[10:58:00 am] - DATAPATTNS (Gap: +3.12%, VAH: VALIDATED)
[10:58:00 am] - LODHA (Gap: +1.42%, VAH: VALIDATED)
[10:58:00 am] - POONAWALLA (Gap: +2.80%, VAH: VALIDATED)
[10:58:00 am] PHASE 1 UNSUBSCRIPTION: Removing 9 rejected stocks from WebSocket
[10:58:00 am] === PHASE 1: UNSUBSCRIBING GAP+VAH REJECTED STOCKS ===
[10:58:00 am] === DEBUG: SUBSCRIPTION STATUS AFTER PHASE 1 UNSUBSCRIPTION ===
[10:58:00 am] Active stocks after unsubscription: 4
[10:58:00 am] Remaining active stocks:
[10:58:00 am] - ATHERENERG
[10:58:00 am] - DATAPATTNS
[10:58:00 am] - LODHA
[10:58:00 am] - POONAWALLA
[10:58:00 am] WAITING 300 seconds until entry decision...


everything is wrong here
it is not following the flow here at all
no market open, no entry time etc etc 

see what was happening earlier 
was according to this:
# Market timing (IST)
MARKET_OPEN = time(10, 58)      
WINDOW_LENGTH = 5            
PREP_START = (datetime.combine(datetime.today(), MARKET_OPEN) - timedelta(seconds=30)).time()  # 30 seconds before market open
ENTRY_TIME = (datetime.combine(datetime.today(), MARKET_OPEN) + timedelta(minutes=WINDOW_LENGTH)).time()  # MARKET_OPEN + WINDOW_LENGTH


see acc. to 10:58 time it is doing all wrong right ... 

it entered early ... 
phase 1 unsub .. etc etc 
all seems wrong .. 