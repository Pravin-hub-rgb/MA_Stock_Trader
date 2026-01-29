# MA Stock Trader - Scan Rules and Requirements

## Overview

This document defines the complete set of rules and requirements for the MA Stock Trader scanning system, covering both continuation and reversal scan algorithms.

## Data Requirements

### Minimum Data Requirements
- **All Technical Indicators**: Minimum 20 days of historical data required
- **20-Day Moving Average**: Must have exactly 20 days for proper calculation
- **20-Day High/Low**: Must have 20 days for distance calculations
- **Volume Analysis**: Uses last 20 days (1 month) for volume confirmation
- **ADR Calculation**: Uses 14-day rolling average for volatility assessment

### Data Sources
- **Primary**: Yahoo Finance (yfinance)
- **Fallback**: NSEpy (if available)
- **Cache**: Local pickle files in `data/cache/` directory
- **Update Frequency**: Incremental updates when gaps detected (default: 3+ days)

### Data Quality Checks
- **Column Validation**: Must have Open, High, Low, Close, Volume columns
- **Date Range**: Must cover requested period without gaps
- **Price Validation**: Close price must be > 0
- **Volume Validation**: Volume must be >= 0

## Continuation Scan Rules

### Base Filters (ALL Must Pass)

#### 1. Price Range Filter
- **Minimum Price**: ₹100
- **Maximum Price**: ₹2000
- **Purpose**: Focus on mid-cap stocks with sufficient liquidity

#### 2. ADR (Average Daily Range) Filter
- **Minimum ADR**: > 3%
- **Calculation**: (14-day average daily range / current close price) * 100
- **Purpose**: Ensure sufficient volatility for trading opportunities
- **Data Requirement**: Minimum 14 days of data

#### 3. Volume Confirmation Filter
- **Requirement**: At least 1 day with 1M+ volume in last month (20 days)
- **Threshold**: 1,000,000 shares
- **Purpose**: Confirm institutional interest and liquidity
- **Data Requirement**: Last 20 days of volume data

#### 4. Rising 20-Day Moving Average Filter
- **Requirement**: Current 20-day MA > 20-day MA from 7 days ago
- **Data Requirement**: Minimum 20 days of data
- **Purpose**: Confirm uptrend momentum

### Technical Analysis Filters

#### 1. Moving Average Analysis
- **20-Day MA**: Must be rising (current > 7 days ago)
- **Calculation**: Simple moving average of closing prices
- **Validation**: Requires full 20-day period

#### 2. Distance from High/Low
- **20-Day High**: Maximum high price over last 20 days
- **20-Day Low**: Minimum low price over last 20 days
- **Distance Calculation**: (Current Price - Reference Price) / Reference Price
- **Purpose**: Assess position within recent trading range

#### 3. Price Change Analysis
- **5-Day Change**: Percentage change over last 5 trading days
- **20-Day Change**: Percentage change over last 20 trading days
- **Purpose**: Assess short and medium-term momentum

## Reversal Scan Rules

### Base Filters (ALL Must Pass)

#### 1. Price Range Filter
- **Minimum Price**: ₹100
- **Maximum Price**: ₹2000
- **Purpose**: Same as continuation scan

#### 2. ADR (Average Daily Range) Filter
- **Minimum ADR**: > 3%
- **Purpose**: Ensure sufficient volatility for reversal moves

#### 3. Volume Confirmation Filter
- **Requirement**: At least 1 day with 1M+ volume in last month
- **Purpose**: Confirm institutional interest during decline

#### 4. Extended Decline Filter
- **Duration**: 4-7 consecutive down days
- **Minimum Decline**: 10% total decline over the period
- **Calculation**: (Start Price - End Price) / Start Price
- **Purpose**: Identify stocks in extended downtrends

### Technical Analysis Filters

#### 1. Oversold Condition Filter
- **Distance from 20-Day Low**: Within 5% of 20-day low price
- **Alternative**: Within 10% of 20-day low (partial oversold)
- **Purpose**: Identify potential reversal points near support

#### 2. Volume Analysis
- **Volume Surge**: Recent volume > 1.5x 20-day average
- **Confirmation**: Volume during decline shows institutional activity
- **Purpose**: Validate reversal potential with volume support

#### 3. Score-Based Ranking
- **Extended Decline**: 50 points (if >10% decline) or 25 points (if <10%)
- **Volume Confirmation**: +25 points
- **Oversold Condition**: +25 points (within 5%) or +15 points (within 10%)
- **ADR Requirement**: +25 points (if >3%)
- **Minimum Score**: > 0 points required to pass

## Caching System Rules

### Cache Management
- **Cache Directory**: `data/cache/`
- **File Format**: Pickle (.pkl) files per symbol
- **Cache Key**: Stock symbol (e.g., "RELIANCE.NS.pkl")

### Update Triggers
- **Gap Detection**: Update if last cached date is 3+ days old
- **Date Range**: Always fetch 1 year of data for new symbols
- **Incremental Updates**: Add new data to existing cache
- **Deduplication**: Remove duplicate dates, sort by date

### Cache Operations
- **Load**: Read cached data for date range queries
- **Save**: Store combined existing + new data
- **Validation**: Check for corrupted cache files
- **Fallback**: Fetch fresh data if cache unavailable

## Error Handling Rules

### Data Fetching Errors
- **Network Issues**: Retry with exponential backoff
- **Symbol Not Found**: Log warning, skip symbol
- **Invalid Data**: Return empty DataFrame, log error
- **Column Mismatch**: Return empty DataFrame, log warning

### Calculation Errors
- **Division by Zero**: Return 0 or NaN with warning
- **Insufficient Data**: Return empty results with warning
- **Invalid Values**: Skip calculation, log warning
- **Type Errors**: Convert types, log warning

### System Errors
- **File I/O Errors**: Skip cache operations, continue scanning
- **Database Errors**: Log error, continue without database save
- **Memory Issues**: Process in batches, log warnings
- **Import Errors**: Use fallback methods, log warnings

## Performance Rules

### Scanning Performance
- **Batch Size**: Process 100 stocks per batch
- **Parallel Processing**: Single-threaded for simplicity
- **Memory Management**: Clear data after each symbol
- **Timeout Handling**: 30-second timeout per symbol

### Caching Performance
- **Cache Hit Rate**: Target >90% for repeated scans
- **Cache Size**: Monitor disk usage, implement cleanup if needed
- **Load Time**: Cache loading should be <1 second per symbol
- **Update Time**: Cache updates should be <5 seconds per symbol

### Optimization Rules
- **Data Reuse**: Use cached data when available
- **Calculation Caching**: Avoid recalculation of same indicators
- **Memory Cleanup**: Clear large DataFrames after processing
- **Logging Levels**: Use appropriate log levels to minimize overhead

## Validation Rules

### Input Validation
- **Date Format**: YYYY-MM-DD format required
- **Symbol Format**: Valid NSE symbol format
- **Parameter Range**: Validate all scan parameters
- **File Paths**: Validate cache and data directory paths

### Output Validation
- **Result Format**: Consistent dictionary structure
- **Data Types**: Proper types for all fields (float, int, str)
- **Range Validation**: Check values are within expected ranges
- **Completeness**: Ensure all required fields are present

### Business Rule Validation
- **Filter Logic**: All base filters must pass for qualification
- **Score Calculation**: Proper scoring for reversal candidates
- **Ranking Logic**: Correct sorting and ranking of results
- **Cache Consistency**: Cache data matches source data

## Compliance Rules

### Data Compliance
- **Source Attribution**: Document data sources and licenses
- **Update Frequency**: Regular updates to maintain data freshness
- **Backup Strategy**: Implement cache backup procedures
- **Security**: Protect cached data from unauthorized access

### Operational Compliance
- **Logging Standards**: Consistent logging format and levels
- **Error Reporting**: Comprehensive error messages and codes
- **Performance Monitoring**: Track scan performance metrics
- **Documentation**: Keep rules documentation up to date

## Implementation Notes

### Code Organization
- **Separation of Concerns**: Data fetching, calculation, and scanning logic separated
- **Modular Design**: Each filter and calculation in separate methods
- **Configuration**: All parameters configurable via class attributes
- **Testing**: Unit tests for all filter and calculation methods

### Future Enhancements
- **Additional Filters**: Easy to add new filter methods
- **Parameter Tuning**: Configuration-based parameter adjustment
- **Multiple Timeframes**: Support for different timeframes
- **Advanced Indicators**: Easy integration of new technical indicators

### Maintenance
- **Regular Updates**: Keep dependencies and data sources updated
- **Performance Review**: Monitor and optimize performance regularly
- **Rule Review**: Periodic review and update of trading rules
- **Documentation**: Keep documentation current with code changes
