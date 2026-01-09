# Reversal Scanner Implementation Plan

## Phase 1: Documentation and Planning
- [x] Create implementation plan document
- [x] Review existing scanner code
- [x] Document current issues
- [x] Define new requirements

## Phase 2: Core Pattern Logic Implementation
- [x] Implement `_check_pattern_logic()` method
- [x] Add period-specific red/green counting rules
- [x] Implement 13% minimum decline calculation
- [x] Add liquidity check (1M+ volume)

## Phase 3: Trend Classification
- [x] Implement `_classify_trend_context()` method
- [x] Add MA_20 comparison logic (day "a" vs day "a-5")
- [x] Return trend classification in results

## Phase 4: Integration and Testing
- [x] Update `analyze_reversal_setup()` method
- [ ] Test with sample data
- [ ] Validate results against theory
- [ ] Fix any issues found

## Phase 5: Finalization
- [ ] Update documentation
- [ ] Clean up code
- [ ] Prepare for deployment
- [ ] Mark task complete

## Detailed Implementation Notes

### Pattern Logic Rules
- 3 days: 3 red, 0 green
- 4-5 days: red > green
- 6-8 days: red + 1 > green

### Trend Classification
- Compare MA_20 at oldest decline day vs 5 days earlier
- MA_today > MA_5days_ago → "uptrend"
- MA_today ≤ MA_5days_ago → "downtrend"

### Expected Return Structure
```python
{
    'symbol': 'HDFCLife',
    'period': 4,
    'red_days': 3,
    'green_days': 1,
    'decline_percent': 15.2,
    'trend_context': 'uptrend',  # or 'downtrend'
    'liquidity_verified': True
}
```

### GUI Display Format
```
Symbol         | Period | Red Days | Decline % | Trend
---------------------------------------------------
HDFCLife (u)   | 4      | 3        | 15.2%     | Uptrend
TATAMOTORS (d) | 5      | 4        | 18.1%     | Downtrend