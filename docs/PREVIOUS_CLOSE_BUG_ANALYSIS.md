# Previous Close Bug Analysis

## Issue Summary

The previous close calculation was returning incorrect values (1576.80 instead of 1516.80 for GODREJPROP) due to a cache bug in the `get_ltp_data()` method.

## Root Cause

**Location:** `src/utils/upstox_fetcher.py` in the `_get_ltp_data_fallback()` method

**The Bug:** The cache fallback method was overriding the correct previous close from the LTP API with an incorrect value from the cache.

### **Bug Flow:**

1. **Historical API correctly fetches Sunday's data** (Budget day) → Returns close: 1516.8 ✅
2. **LTP API also correctly returns Sunday's close** → Returns cp: 1516.8 ✅  
3. **Cache fallback method overrides LTP API's correct value** → Sets cp: 2206.3 ❌
4. **Main method fixes it back** → Sets cp: 1516.8 ✅

### **The Problematic Code:**

```python
def _get_ltp_data_fallback(self, symbol: str) -> Dict:
    # ...
    if ltp_data:
        ltp_data['cp'] = latest_close  # ← BUG: Overrides correct LTP API value
        return ltp_data
```

## Why This Happened

1. **Cache contains old data** (2206.3 from much earlier)
2. **Cache fallback method always overrides `cp`** regardless of whether LTP API provided a correct value
3. **The main method's fix only works when historical API succeeds**
4. **If historical API fails, wrong cache value is returned**

## The Fix

The cache fallback method should only use cache close when the LTP API fails to provide a value.

### **Corrected Logic:**

```python
def _get_ltp_data_fallback(self, symbol: str) -> Dict:
    # ...
    if ltp_data:
        # Only use cache close if LTP API didn't provide one
        if ltp_data.get('cp') is None:
            ltp_data['cp'] = latest_close
        return ltp_data
```

## Testing Results

✅ **Upstox API correctly includes special trading days** (Sunday Budget session)
✅ **Historical API correctly returns Sunday's data** 
✅ **LTP API correctly returns Sunday's close**
❌ **Cache fallback was overriding correct values with stale cache data**

## Impact

- **Wrong previous close** → Wrong gap calculations → Wrong entry triggers
- **Missed trades** when price crosses correct previous close but not wrong cached close
- **Incorrect trading decisions** based on wrong gap percentages

## Solution Status

✅ **Bug identified and root cause confirmed**
✅ **Fix logic designed and tested**
✅ **Ready for implementation in main codebase**