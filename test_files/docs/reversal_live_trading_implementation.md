# Reversal Live Trading Implementation Guide

## Overview

This document outlines the implementation plan for adding reversal trading capabilities to the existing live trading bot. The bot will support both continuation and reversal trading modes, chosen via command-line arguments.

## Trading Modes

### Continuation Trading (Existing)
- Trades stocks from `continuation_list.txt`
- Gap up validation (0-5%)
- Entry on break above daily high
- Standard continuation logic

### Reversal Trading (New)
- Trades stocks from `reversal_list.txt`
- Two situations based on stock's trend context
- Gap direction depends on situation
- Specialized entry logic for each scenario

## Command-Line Usage

```bash
# For continuation trading
python run_live_bot.py c

# For reversal trading
python run_live_bot.py r
```

## Stock List Formats

### continuation_list.txt
```
HDFC,TCS,INFY
```

### reversal_list.txt
```
HDFC-u,TCS-d,INFY-d
```
- `-u`: Uptrend reversal stock (uses continuation method)
- `-d`: Downtrend reversal stock (situation 2: gap down required)

## Reversal Trading Situations

### Situation 1: Uptrend Reversal Stocks (-u flag)
**Treatment**: Identical to continuation trading
- Gap up = GOOD (0-5% gap)
- Strong start validation
- Entry on break above daily high
- 4% stop loss

### Situation 2: Downtrend Reversal Stocks (-d flag)
**Core Requirements**:
- Gap down = MANDATORY (-5% to 0% gap)
- Rubber band stretching effect
- Two sub-cases based on market open behavior

#### Sub-case 2A: Gap Down + Strong Start
**Entry Condition**: Gap down followed by immediate strength
- Open price equals low price (open = low)
- **Entry**: Within first 5 minutes at market
- **Logic**: Gap down stretches rubber band, immediate strength shows reversal

#### Sub-case 2B: Gap Down + Climax Bar + Half-Retracement
**Entry Condition**: Gap down followed by 3-minute climax bar
- **Climax Detection**: Largest 3-minute bar in the decline sequence
- **Dynamic Retracement**: 40% retracement from daily range
- **Formula**: Entry Trigger = Daily Low + (Daily High - Daily Low) × 0.4
- **Dynamic Updates**: Recalculate trigger on every new daily low
- **Multiple Attempts**: Up to 3 entries per stock, same-day execution

## Implementation Architecture

### Modified Components

#### run_live_bot.py
- Add argument parsing (`c` or `r`)
- Load appropriate stock list based on mode
- Parse `-u`/`-d` flags for reversal stocks
- Pass situation flags to StockMonitor

#### StockMonitor Extensions
- **Gap Validation**: Different logic for continuation vs reversal
  - Continuation: Gap up (0-5%)
  - Reversal Situation 1: Gap up (0-5%)
  - Reversal Situation 2: Gap down (-5% to 0%)

- **Entry Preparation**: Situation-aware entry levels
  - Continuation/Situation 1: Entry = Daily High, SL = 4% below
  - Situation 2: Depends on sub-case

- **2A Logic**: Immediate entry if open = low in first 5 min
- **2B Logic**: Monitor 3-min bars for climax, then dynamic retracement

### New Methods in StockState

```python
def detect_climax_bar(self, three_min_bars):
    """Detect if current 3-min bar is climax (largest in sequence)"""
    # Implementation for 3-min OHLC analysis

def calculate_retracement_trigger(self):
    """Calculate 40% retracement from current daily range"""
    return self.daily_low + (self.daily_high - self.daily_low) * 0.4

def update_retracement_on_new_low(self, new_price):
    """Update daily high and recalculate trigger on new low"""
    self.daily_high = max(self.daily_high, new_price)
    self.retracement_trigger = self.calculate_retracement_trigger()
```

## Trading Flow

### Pre-Market (Before 9:15)
1. Parse command-line argument
2. Load stock list and parse flags
3. Initialize StockMonitor with situation classifications

### Market Open (9:15-9:20)
1. Receive 1-min OHLC candles to set opening prices
2. Validate gaps based on situation:
   - Continuation/Situation 1: Check gap up 0-5%
   - Situation 2: Check gap down -5% to 0%
3. Monitor for low violations (<1% below open)

### Entry Preparation (9:20)
1. **Continuation/Situation 1**: Set entry = daily high, SL = 4% below
2. **Situation 2A**: Monitor for open = low in first 5 min
3. **Situation 2B**: Monitor 3-min bars for climax detection

### Live Trading (9:20-3:30)
1. **Continuation/Situation 1**: Enter on break above entry high
2. **Situation 2A**: Enter immediately if conditions met in first 5 min
3. **Situation 2B**:
   - Detect climax bar
   - Calculate initial 40% retracement trigger
   - Update trigger on new daily lows
   - Enter on trigger hit (up to 3 attempts)

### Risk Management
- **Stop Loss**: 4% below entry for all setups
- **Trailing Stop**: Move SL to breakeven after 5% profit
- **Position Limit**: 2 reversal setups per day
- **Exit**: SL hit or end of day

## WebSocket Data Processing

### Tick Handling
- **OHLC Data**: Use 1-min candles for opening price, 3-min for climax detection
- **LTP Updates**: Real-time price feeds for entry/exit signals
- **Event-Driven**: All processing in tick_handler callback

### Data Requirements
- **Continuation**: LTP + 1-min OHLC for open
- **Reversal 2A**: LTP + 1-min OHLC for open/low check
- **Reversal 2B**: LTP + 3-min OHLC for climax + daily range tracking

## Testing and Validation

### Test Mode
- Simulate opening prices and ticks
- Test gap validation logic
- Verify entry signal detection
- Paper trading for position management

### Edge Cases
- Multiple climax bars in sequence
- Gap validation boundaries
- Retracement trigger updates
- Stop loss and trailing stop logic

## Integration Notes

### Shared Components
- WebSocket streamer (SimpleStockStreamer)
- Paper trader for logging
- Upstox API integration
- Singleton locking for single instance

### Code Reuse
- 80% of continuation code reused
- Extensions via inheritance/polymorphism
- Configuration-driven logic selection

## Usage Examples

### Start Reversal Bot
```bash
python run_live_bot.py r
```

### Expected Output
```
🚀 STARTING LIVE TRADING BOT (REVERSAL MODE)
📋 Loaded 3 stocks: HDFC-u, TCS-d, INFY-d
✅ HDFC: Situation 1 (uptrend)
✅ TCS: Situation 2 (downtrend)
✅ INFY: Situation 2 (downtrend)
📈 MARKET OPEN! Monitoring live data...
```

### Log Entries
```
✅ TCS qualified - Gap: -2.1% | Sub-case: 2A | Entry: Immediate
📈 TCS entry triggered at ₹2450.00, SL placed at ₹2352.00
🔒 TCS trailing stop adjusted: ₹2352.00 → ₹2450.00 (5% profit)
```

## Future Enhancements

### Market Breadth Integration
- Automatic mode selection based on breadth analysis
- Remove manual argument requirement

### Advanced Features
- Position sizing adjustments per situation
- Volume confirmation for entries
- Multi-timeframe climax detection

### Monitoring
- Real-time dashboard for reversal setups
- Performance tracking by situation type
- Risk metrics per trading mode

## Conclusion

This implementation extends the existing continuation bot with reversal capabilities while maintaining code reusability and consistent risk management. The situation-based approach ensures appropriate handling of different market contexts for optimal reversal trading performance.