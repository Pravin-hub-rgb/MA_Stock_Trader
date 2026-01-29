# Reversal Trading Algorithm - Final Framework

## Overview
This document outlines the complete reversal trading system based on instructor methodology, adapted for practical implementation with risk management considerations.

## Stock Selection Criteria (Pre-Qualified by Scanner)
- **Decline Days**: 3-8 consecutive down days
- **Decline Magnitude**: 10-15%+ total decline
- **Volume**: 1M+ shares on 5%+ moves
- **Institutional Activity**: "Purple dots" (multiple 5%+ days with high volume)
- **Source**: reversal_list.txt with format `SYMBOL-DAYS`

## Core Algorithm Structure

### 1. Stock Classification by Decline Duration
```
IF decline_days >= 7:
    confidence_level = HIGH
    entry_mode = AGGRESSIVE  # Immediate gap down entry
ELSE IF decline_days >= 3:
    confidence_level = MEDIUM
    entry_mode = CONFIRMED  # Need strong start or climax
ELSE:
    SKIP_STOCK  # Too early for reversal
```

### 2. Entry Signal Detection (9:15-9:20 Window)

#### Primary Signals (Highest Priority)
```
GAP_DOWN_SIGNAL:
    IF open_price < previous_close * 0.98:  # 2%+ gap down
        IF confidence_level == HIGH:
            TRIGGER: IMMEDIATE_MARKET_ENTRY
        ELSE:  # MEDIUM confidence
            MONITOR_FOR_CONFIRMATION
```

#### Secondary Signals (Confirmation Required)
```
STRONG_START_SIGNAL:
    IF gap_pct > 0.02 AND open_price == low_price (within 1 %):
        TRIGGER: MARKET_ENTRY_WITHIN_5_MIN

CLIMAX_BAR_SIGNAL:
    IF 3min_bar_range > 1.5% AND (gap_down OR time_anywhere):
        TRIGGER: WAIT_FOR_60%_RETRACEMENT
```

### 3. Dynamic Entry Logic Throughout Day

#### For HIGH Confidence Stocks (7+ days)
```
WHILE time < 15:30:
    IF gap_down_detected:
        EXECUTE_IMMEDIATE_ENTRY
        SET_STOP_LOSS = entry_price * 0.96  # 4% below
        BREAK
```

#### For MEDIUM Confidence Stocks (3-6 days)
```
WHILE time < 15:30:
    IF strong_start_detected OR climax_bar_detected:
        EXECUTE_ENTRY
        SET_STOP_LOSS = entry_price * 0.96
        BREAK
```

### 4. Progressive Sizing Algorithm

```
attempt_number = 1
base_position_size = calculate_standard_size()

WHILE attempt_number <= 3:
    IF entry_signal_triggered AND no_active_position:

        IF attempt_number == 1:
            position_size = base_position_size
        ELSE IF attempt_number == 2:
            position_size = base_position_size * 1.5
        ELSE:  # attempt 3
            position_size = base_position_size * 2.0

        EXECUTE_ENTRY with position_size
        attempt_number++

        # Update trigger for next attempt (if climax-based)
        IF climax_entry:
            new_trigger = current_low + (current_high - current_low) * 0.4
```

### 5. Position Limit Management

```
MAX_POSITIONS = 2  # Per day limit

IF new_entry_signal AND active_positions >= MAX_POSITIONS:
    IF signal_strength == EXCEPTIONAL:  # 7+ day gap down climax
        OVERRIDE_LIMIT  # Allow additional position
    ELSE:
        SKIP_ENTRY
```

### 6. Stop Loss and Exit Rules

```
STOP_LOSS = entry_price * 0.96  # 4% below all entries

TRAILING_STOP:
    IF profit > 5%:
        MOVE_SL_TO_BREAKEVEN

EXIT_CONDITIONS:
    - Stop loss hit
    - End of trading day
    - Manual override
```

## Implementation Data Flow

### reversal_list.txt Format
```
SYMBOL1-DAYS1,SYMBOL2-DAYS2,SYMBOL3-DAYS3
Example: HDFC-5,TCS-7,INFY-4
```

### Parsing Logic
```python
def parse_reversal_entry(entry):
    symbol, days_str = entry.split('-')
    decline_days = int(days_str)

    return {
        'symbol': symbol,
        'decline_days': decline_days,
        'aggressive_mode': decline_days >= 7,
        'confirmation_needed': decline_days < 7
    }
```

### Monitoring Phases

#### Phase 1: Opening Window (9:15-9:20)
- Monitor all stocks for gap behavior
- Execute immediate entries for HIGH confidence gap downs
- Identify strong start candidates

#### Phase 2: Full Day Monitoring (9:20-15:30)
- Continue monitoring remaining stocks
- Watch for climax bars throughout day
- Execute confirmed entries as signals appear

## Risk Management Rules

### Position Sizing
- **Base Size**: Standard calculation (0.5-2% of capital)
- **Scaling**: 1x → 1.5x → 2x on subsequent attempts
- **Total Exposure**: Max 2 positions, flexible for exceptional setups

### Time Discipline
- **Entry Window**: Complete within trading day
- **No Overnight**: All positions closed by 15:30
- **Attempt Limit**: Maximum 3 attempts per stock

### Market Conditions
- **Best**: Bear/ranging markets with many reversal candidates
- **Caution**: Strong bull markets (lower probability)
- **Volume Check**: Ensure liquidity for position sizing

## Algorithm Flowchart Summary

```
START
├── Parse reversal_list.txt (SYMBOL-DAYS format)
├── Classify by decline duration
│   ├── 7+ days: AGGRESSIVE mode
│   └── 3-6 days: CONFIRMED mode
├── Monitor 9:15-9:20
│   ├── Gap down + HIGH → Immediate entry
│   ├── Strong start → Entry within 5 min
│   └── Track remaining stocks
├── Continue monitoring 9:20-15:30
│   ├── Climax bar detection
│   ├── Retracement calculation (40%)
│   └── Execute confirmed entries
├── Progressive sizing on re-entries
└── Risk management (4% SL, position limits)
```

## Key Differentiators from Original System

1. **Decline Duration**: Primary factor for confirmation requirements
2. **Unified Logic**: No separate -u/-d classification
3. **Progressive Sizing**: Built-in re-entry scaling
4. **Flexible Limits**: Allow exceptional setups beyond 2-position limit
5. **Time-Agnostic**: Climax monitoring throughout trading day

## Success Metrics

- **Win Rate Target**: 30-40% (lower than continuation due to risk)
- **Risk-Reward**: Target 1:3+ ratio per trade
- **Portfolio Impact**: 20-30% of total trading capital
- **Monthly Goal**: 3-5% account growth in reversal-rich markets

This algorithm balances the instructor's aggressive "show up to setups" philosophy with practical risk management for consistent performance.
