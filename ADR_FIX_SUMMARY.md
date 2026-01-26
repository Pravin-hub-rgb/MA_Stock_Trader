# ADR Cache Fix Summary

## Problem
The reversal bot was using hardcoded 3% ADR values instead of retrieving actual ADR values from cache, causing inaccurate stock scoring and selection.

## Root Cause
Multiple files in the live trading system were importing from the old scanner's `stock_scorer.py` instead of the live trading version:

1. `src/trading/live_trading/selection_engine.py` - Line 71
2. `src/trading/live_trading/continuation_stock_monitor.py` - Line 262  
3. `src/trading/live_trading/setup_reversal_data.py` - Line 71

The old scanner version had hardcoded ADR defaults (0.03 = 3%) while the live trading version properly loads ADR from cache.

## Solution
Updated all imports to use the live trading stock scorer:

```python
# OLD (scanner version with hardcoded defaults)
from scanner.stock_scorer import stock_scorer

# NEW (live trading version with cache-based ADR)
from trading.live_trading.stock_scorer import stock_scorer
```

## Files Modified
1. `src/trading/live_trading/selection_engine.py`
2. `src/trading/live_trading/continuation_stock_monitor.py`
3. `src/trading/live_trading/setup_reversal_data.py`

## Test Results
After fixes, ADR values are properly retrieved from cache:

- ITC: ADR 2.00% (from cache)
- RELIANCE: ADR 2.43% (from cache)
- TATASTEEL: ADR 2.57% (from cache)
- HDFCBANK: ADR 1.75% (from cache)

## Impact
- Stock scoring now uses actual ADR values instead of hardcoded 3%
- Better stock selection based on real volatility data
- More accurate trading decisions
- Reversal bot now has proper data access equivalent to continuation bot

## Verification
Created test script `test_adr_cache.py` to verify ADR cache functionality and ensure the fixes work correctly.