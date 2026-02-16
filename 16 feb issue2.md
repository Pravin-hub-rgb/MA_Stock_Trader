[11:20:37 am] [OK] UNIONBANK: Upper Range (VAH) = Rs179.98
[11:20:37 am] Summary: 13 stocks successfully calculated
[11:20:37 am] === PRE-MARKET IEP FETCH SEQUENCE ===
[11:20:37 am] WAITING 53 seconds until PREP_START (11:21:30)...
[11:21:30 am] FETCHING IEP for 13 continuation stocks at PREP_START (11:21:30)...
[11:21:30 am] IEP FETCH COMPLETED SUCCESSFULLY
[11:21:30 am] Set opening price for NAVNETEDUL: Rs155.36
[11:21:30 am] Gap validation failed for NAVNETEDUL
[11:21:30 am] VAH validation failed for NAVNETEDUL (Opening price 155.36 < VAH 156.80)
[11:21:30 am] Set opening price for ELECON: Rs432.20
[11:21:30 am] Gap validation failed for ELECON
[11:21:30 am] VAH validation failed for ELECON (Opening price 432.20 < VAH 436.23)
[11:21:30 am] Set opening price for DATAPATTNS: Rs2855.10
[11:21:30 am] Gap validated for DATAPATTNS
[11:21:30 am] VAH validated for DATAPATTNS
[11:21:30 am] Set opening price for INFOBEAN: Rs873.50
[11:21:30 am] Gap validated for INFOBEAN
[11:21:30 am] VAH validation failed for INFOBEAN (Opening price 873.50 < VAH 901.02)
[11:21:30 am] Set opening price for LODHA: Rs1088.60
[11:21:30 am] Gap validated for LODHA
[11:21:30 am] VAH validated for LODHA
[11:21:30 am] Set opening price for IDBI: Rs109.58
[11:21:30 am] Gap validation failed for IDBI
[11:21:30 am] VAH validation failed for IDBI (Opening price 109.58 < VAH 112.69)
[11:21:30 am] Set opening price for ROSSTECH: Rs709.90
[11:21:30 am] Gap validation failed for ROSSTECH
[11:21:30 am] VAH validation failed for ROSSTECH (Opening price 709.90 < VAH 732.67)
[11:21:30 am] Set opening price for UNIONBANK: Rs177.53
[11:21:30 am] Gap validation failed for UNIONBANK
[11:21:30 am] VAH validation failed for UNIONBANK (Opening price 177.53 < VAH 179.98)
[11:21:30 am] Set opening price for CHENNPETRO: Rs880.40
[11:21:30 am] Gap validation failed for CHENNPETRO
[11:21:30 am] VAH validation failed for CHENNPETRO (Opening price 880.40 < VAH 886.97)
[11:21:30 am] Set opening price for ATHERENERG: Rs718.20
[11:21:30 am] Gap validated for ATHERENERG
[11:21:30 am] VAH validated for ATHERENERG
[11:21:30 am] Set opening price for NLCINDIA: Rs257.05
[11:21:30 am] Gap validation failed for NLCINDIA
[11:21:30 am] VAH validation failed for NLCINDIA (Opening price 257.05 < VAH 256.28)
[11:21:30 am] Set opening price for SHANTIGOLD: Rs217.38
[11:21:30 am] Gap validation failed for SHANTIGOLD
[11:21:30 am] VAH validation failed for SHANTIGOLD (Opening price 217.38 < VAH 221.68)
[11:21:30 am] Set opening price for POONAWALLA: Rs477.95
[11:21:30 am] Gap validated for POONAWALLA
[11:21:30 am] VAH validated for POONAWALLA
[11:21:30 am] === STARTING CONTINUATION TRADING PHASE ===
[11:21:30 am] ATTEMPTING to connect to data stream...
[11:21:30 am] Connecting to Market Data Feed...
[11:21:30 am] CONNECTED Data stream connected
[11:21:30 am] WAITING 30 seconds for market open...
[11:21:30 am] WebSocket OPENED at 11:21:30
[11:21:31 am] Subscribed to 13 active instruments in 'full' mode (LTP + OHLC) at 11:21:31
[11:22:00 am] MARKET OPEN! Monitoring live OHLC data...
[11:22:00 am] NO initial volume capture needed - using current volume directly as cumulative
[11:22:00 am] USING IEP-BASED OPENING PRICES - Set at 9:14:30 from pre-market IEP
[11:22:00 am] Gap validation completed at 9:14:30, ready for trading
[11:22:00 am] === PHASE 1: UNSUBSCRIBING GAP+VAH REJECTED STOCKS ===
[11:22:00 am] === DEBUG: SUBSCRIPTION STATUS AFTER PHASE 1 UNSUBSCRIPTION ===
[11:22:00 am] Active stocks after unsubscription: 4
[11:22:00 am] Remaining active stocks:
[11:22:00 am] - ATHERENERG
[11:22:00 am] - DATAPATTNS
[11:22:00 am] - LODHA
[11:22:00 am] - POONAWALLA
[11:22:00 am] WAITING 300 seconds until ENTRY_TIME (11:27:00)...
[11:22:00 am] Current time: 11:22:00.012762
[11:22:00 am] Entry time: 11:27:00

okay so first we have like 10 stocks 
at pre market as we get to know that stocks are validated acc. to the gap and vah so
it feels like there isn't a think for unsubbing phase 1 
what we are doing is subbing to all the stocks but thats not correct instead we should just sub to the validated stocks ...
getting what i'm saying 
so like we have 10 stocks 
at pre market 5 for them fails the gap and vah so i think we should only sub to 5 which passed 
so this phase 1 unsubbing make no sense here ... 