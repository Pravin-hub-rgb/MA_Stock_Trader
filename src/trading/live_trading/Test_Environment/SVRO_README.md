# SVRO Testing Environment

This directory contains a comprehensive testing environment for the SVRO (Strong Volume Reversal Opportunity) continuation bot.

## Overview

The SVRO testing environment provides isolated testing of the continuation bot's SVRO entry system using the exact monolithic architecture with simulated data.

## Architecture

### SVRO vs Reversal Bot Architecture

| Feature | Reversal Bot | SVRO Continuation Bot |
|---------|-------------|----------------------|
| **Architecture** | Modular (StateMachine, TickProcessor) | Monolithic (StockMonitor only) |
| **State Management** | State machine with transitions | Direct flag-based state management |
| **Entry Logic** | OOPS (gap down) and Strong Start (gap up) | SVRO (gap up with volume validation) |
| **Volume Requirements** | Not applicable | 7.5% of mean volume baseline |
| **Testing Approach** | `dummy_tick_streamer.py` | `dummy_svro_tick_streamer.py` |

## Test Environment Structure

```
Test_Environment/
├── run_svro_test.py                    # Main SVRO test runner
├── dummy_svro_tick_streamer.py         # SVRO data simulator
├── run_comprehensive_svro_test.py      # Comprehensive test suite
└── test_scenarios/                     # Individual test scenarios
    ├── svro_gap_validation.py          # Gap validation tests
    ├── svro_volume_validation.py       # Volume validation tests
    └── svro_entry_trigger.py           # Entry trigger tests
```

## Key Features

### ✅ Mock SVRO Architecture
- **Exact continuation bot files**: Uses real `continuation_stock_monitor.py` with simulated data
- **No real API dependencies**: Eliminates Upstox fetcher, IEP fetching, and market data requirements
- **Simulated SVRO data**: Generates synthetic price and volume data for testing
- **Complete state progression**: Tests full SVRO workflow from gap validation to entry triggers

### ✅ SVRO-Specific Testing
- **Gap validation**: Tests 0.3% to 5% gap up requirements for SVRO
- **Volume validation**: Tests 7.5% of mean volume baseline requirement
- **Entry triggers**: Tests price breaking entry high with proper SL placement
- **State progression**: Tests complete SVRO state transitions

## Test Scenarios

### 1. Gap Validation Tests (`svro_gap_validation.py`)
Tests SVRO gap validation requirements:
- ✅ **Minimum gap**: 0.4% gap up should pass
- ✅ **Normal gap**: 2.0% gap up should pass  
- ✅ **Maximum gap**: 5.0% gap up should pass
- ❌ **Too flat**: 0.2% gap should be rejected
- ❌ **Too high**: 5.1% gap should be rejected
- ❌ **Gap down**: Negative gap should be rejected

### 2. Volume Validation Tests (`svro_volume_validation.py`)
Tests SVRO volume threshold requirements:
- ✅ **Minimum volume**: 7.5% of baseline should pass
- ✅ **Normal volume**: 15% of baseline should pass
- ✅ **High volume**: 30% of baseline should pass
- ❌ **Low volume**: 5% of baseline should be rejected
- ❌ **Zero baseline**: Zero volume baseline should be rejected

### 3. Entry Trigger Tests (`svro_entry_trigger.py`)
Tests SVRO entry trigger logic:
- ✅ **Entry high match**: Price equal to entry high should trigger
- ✅ **Entry high break**: Price above entry high should trigger
- ❌ **Below entry high**: Price below entry high should not trigger
- ✅ **Entry execution**: Proper entry price and SL setting

### 4. Full Workflow Tests (`run_svro_test.py`)
End-to-end SVRO testing with simulated data:
- Gap validation → Volume validation → Entry preparation → Entry trigger
- Real continuation bot logic with synthetic data
- Complete state progression simulation

## Usage

### Run Individual Test Scenarios
```bash
# Test gap validation
python src/trading/live_trading/Test_Environment/test_scenarios/svro_gap_validation.py

# Test volume validation
python src/trading/live_trading/Test_Environment/test_scenarios/svro_volume_validation.py

# Test entry triggers
python src/trading/live_trading/Test_Environment/test_scenarios/svro_entry_trigger.py
```

### Run Main SVRO Test
```bash
# Run SVRO test with exact continuation bot architecture
python src/trading/live_trading/Test_Environment/run_svro_test.py
```

### Run Comprehensive SVRO Test Suite
```bash
# Run all SVRO tests (gap, volume, entry, full workflow)
python src/trading/live_trading/Test_Environment/run_comprehensive_svro_test.py
```

## SVRO Test Parameters

### Gap Validation
- **FLAT_GAP_THRESHOLD**: 0.3% flat gap threshold
- **Gap Range**: 0.3% to 5% for SVRO continuation stocks
- **Gap Direction**: Must be gap up (positive)

### Volume Validation
- **SVRO_MIN_VOLUME_RATIO**: 7.5% minimum relative volume
- **Volume Baseline**: Mean volume from cache
- **Volume Calculation**: Cumulative volume / baseline

### Entry Parameters
- **ENTRY_SL_PCT**: 4% stop loss below entry high
- **ENTRY_TIME**: 9:20 AM for entry preparation
- **Entry High**: Highest price reached by 9:20 AM

## SVRO State Progression

The SVRO test environment simulates exact state progression:

1. **Gap Validation**: Validate 0.3% to 5% gap up
2. **Low Violation Check**: Ensure no violation of 1% threshold
3. **Volume Validation**: Check 7.5% volume threshold
4. **Entry Preparation**: Set entry high and SL at 9:20
5. **Entry Trigger**: Price breaks entry high
6. **Position Management**: SL monitoring and trailing stops

## SVRO Data Simulation

The `DummySVROTickStreamer` generates realistic SVRO test data:

- **Price Steps**: Gradually increasing prices for SVRO success
- **Volume Steps**: Volume buildup to meet 7.5% threshold
- **Timing**: Proper market open and entry timing simulation
- **State Progression**: Automatic state transitions

## Test Results

### Success Indicators
- ✅ Gap validation passes (0.3% to 5% gap up)
- ✅ Volume validation passes (≥7.5% of baseline)
- ✅ Entry trigger activates (price breaks entry high)
- ✅ Entry execution completes (position opened)

### Failure Indicators
- ❌ Gap too flat (<0.3%) or too high (>5%)
- ❌ Volume below threshold (<7.5%)
- ❌ Price doesn't break entry high
- ❌ Entry execution fails

## Benefits

### ✅ Isolated Testing
- No dependencies on real market data
- No Upstox API requirements
- No IEP fetching or volume calculations
- Pure logic testing with synthetic data

### ✅ Exact Architecture
- Uses real continuation bot files
- Same state progression as live trading
- Identical entry logic and validation
- Realistic SVRO workflow simulation

### ✅ Comprehensive Coverage
- All SVRO requirements tested
- Edge cases and boundary conditions
- Complete workflow validation
- Detailed logging and debugging

## Troubleshooting

### Common Issues

1. **No entries triggered**
   - Check gap validation (must be 0.3% to 5% gap up)
   - Verify volume threshold (must be ≥7.5%)
   - Ensure price breaks entry high

2. **Gap validation failures**
   - Verify gap calculation logic
   - Check gap direction (must be up)
   - Validate gap percentage range

3. **Volume validation failures**
   - Ensure volume baseline is set
   - Check volume ratio calculation
   - Verify 7.5% threshold logic

### Debug Tips

- Check `svro_test.log` for detailed logs
- Verify stock configuration parameters
- Monitor state progression in logs
- Validate synthetic data generation

## Integration with Live Trading

The SVRO testing environment provides:

- **Pre-deployment validation**: Test SVRO logic before live deployment
- **Regression testing**: Ensure SVRO changes don't break existing logic
- **Performance testing**: Validate SVRO performance with synthetic data
- **Edge case testing**: Test boundary conditions safely

## Future Enhancements

Potential improvements:
- Additional SVRO test scenarios
- Performance optimization
- Automated test result analysis
- Visual test result reporting
- Integration with CI/CD pipelines