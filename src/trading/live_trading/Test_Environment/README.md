# Continuation Bot Test Environment

A comprehensive monolithic test environment for the continuation bot with SVRO entry system.

## Overview

This test environment exactly mirrors the continuation bot's monolithic architecture while providing comprehensive testing capabilities for the SVRO entry system.

## Test Environment Structure

```
Test_Environment/
├── run_continuation_test.py          # Main monolithic test runner
├── dummy_tick_streamer.py            # Synthetic tick generator with volume control
├── continuation_test.py              # Main test logic (monolithic)
├── run_comprehensive_continuation_test.py  # Comprehensive test runner
└── test_scenarios/
    └── svro_entry_success.py         # SVRO entry success test
```

## Key Features

- **Monolithic Architecture**: Exactly mirrors the continuation bot's single-file structure
- **SVRO Entry System Testing**: Comprehensive testing of all SVRO entry logic
- **Volume Control**: Synthetic volume generation for realistic testing
- **State Progression**: Simulates exact state transitions as in live trading
- **Comprehensive Scenarios**: Success, failure, edge cases, and stress tests

## Test Scenarios

### 1. Basic SVRO Entry
- Gap up 2%, volume 10%, price breaks entry high
- Expected: Entry triggered with all conditions met

### 2. Volume Failure
- Gap up 3%, volume 5% (below threshold)
- Expected: No entry due to insufficient volume

### 3. Price Action Failure
- Gap up 4%, volume 15%, price doesn't break entry high
- Expected: No entry due to lack of price action

### 4. Edge Cases
- Gap exactly 5%, volume exactly 7.5%, timing boundary conditions
- Expected: Proper handling of boundary conditions

## How to Run Tests

### Basic Test
```bash
python src/trading/live_trading/Test_Environment/run_continuation_test.py
```

### SVRO Entry Success Test
```bash
python src/trading/live_trading/Test_Environment/test_scenarios/svro_entry_success.py
```

### Comprehensive Test
```bash
python src/trading/live_trading/Test_Environment/run_comprehensive_continuation_test.py
```

## Test Parameters

### Gap Validation
- **FLAT_GAP_THRESHOLD**: 0.3% flat gap threshold
- **Gap Range**: 0-5% for continuation stocks

### Volume Validation
- **SVRO_MIN_VOLUME_RATIO**: 7.5% minimum relative volume
- **Volume Baseline**: 1M default for testing

### Entry Parameters
- **ENTRY_SL_PCT**: 4% stop loss
- **LOW_VIOLATION_PCT**: 1% low violation threshold

## Test Results

Test results are logged to:
- `continuation_test.log` - Main test logs
- `continuation_tick_streamer.log` - Tick generator logs
- `svro_entry_success.log` - SVRO success test logs
- `comprehensive_continuation_test.log` - Comprehensive test logs

## VAH Calculation

The test environment includes VAH (Volume At High) calculation for continuation stocks:
- Calculated from previous day's volume profile
- Results saved to `vah_results.json`
- Used for VAH validation in entry logic

## State Progression

The test environment simulates exact state progression:
1. Gap validation
2. Low violation monitoring
3. Volume validation
4. Entry preparation
5. Entry execution

## Volume Tracking

Comprehensive volume tracking includes:
- Initial volume capture at market open
- Cumulative volume tracking
- Volume ratio calculations
- Volume baseline comparisons

## Entry Logic

SVRO entry logic includes:
- Gap validation (0-5% range)
- Low violation monitoring
- Volume validation (7.5% minimum)
- Entry signal generation
- Stop loss placement

## Exit Logic

Exit logic includes:
- Stop loss monitoring
- Trailing stop adjustments (5% profit)
- Position exit handling

## Test Environment Benefits

1. **Exact Architecture**: Mirrors live trading code structure
2. **Controlled Environment**: Synthetic data for reliable testing
3. **Comprehensive Coverage**: All scenarios and edge cases
4. **State Simulation**: Exact state progression as in live trading
5. **Volume Control**: Realistic volume generation for testing
6. **Logging**: Detailed logs for debugging and analysis

## Usage Examples

### Testing SVRO Entry Logic
```python
# Create test scenario
streamer = ContinuationDummyTickStreamer(tick_interval=0.5, price_step=0.1, volume_step=1000)
streamer.add_test_stock(
    symbol="TEST_SVRO",
    instrument_key="TEST_SVRO_KEY",
    previous_close=100.0,
    open_price=95.0,  # Gap down
    situation='continuation'  # SVRO
)
streamer.start_streaming()
```

### Running Comprehensive Tests
```python
test = ComprehensiveContinuationTest()
success = test.run_test()
print(f"Test completed with {len(test.test_results)} entries")
```

## Development Notes

- All tests use pure OHLC processing (no tick-based opening prices)
- IEP-based opening prices are used for realistic testing
- State progression is simulated exactly as in live trading
- Volume validation is tested with synthetic volume generation
- VAH calculation is included for comprehensive testing

## Troubleshooting

### Common Issues

1. **No entries triggered**: Check volume validation thresholds
2. **Gap validation failures**: Verify gap percentage calculations
3. **Volume baseline issues**: Ensure volume metadata is loaded correctly
4. **State progression problems**: Check state transition logic

### Debug Tips

- Check log files for detailed error information
- Verify stock configuration and parameters
- Ensure proper market timing and state progression
- Validate volume calculations and baselines

## Performance

The test environment is optimized for:
- Fast execution (300 second max test duration)
- Realistic synthetic data generation
- Comprehensive logging without performance impact
- Memory-efficient state management

## Future Enhancements

Potential improvements include:
- Additional test scenarios
- Performance optimization
- Integration with CI/CD pipelines
- Automated test result analysis
- Visual test result reporting

## Contributing

To contribute to the test environment:
1. Follow the existing monolithic architecture
2. Add comprehensive test scenarios
3. Maintain detailed logging
4. Ensure state progression accuracy
5. Test with synthetic data generation