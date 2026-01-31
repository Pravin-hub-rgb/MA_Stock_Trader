# MA Stock Trader - System Architecture Document

## Overview

This document outlines the architecture for a comprehensive stock trading system designed for NSE equities, implementing continuation and reversal trading strategies with systematic scanning, manual review, and automated execution.

## System Components

### Application 1: Market Scanner & Watchlist Manager

**Purpose**: Daily scanning and watchlist management for next-day trading candidates.

**Core Features**:
- Automated daily scans for continuation and reversal setups
- Configurable base filters (volume, price, ADR)
- Manual chart review with navigation
- Watchlist organization and management
- Scan source tracking and notes

**Continuation Scans**:
1. **5% from 1-month high**: Stocks coming back up from recent lows
2. **3-month scan**: Performance-based scan (parameters to be finalized)
3. **Base Filters**:
   - Rising 20MA (last 7 days angle > 0°)
   - Volume: At least 1 day with 1M+ volume in last month
   - ADR: Above configurable threshold (default: >3-4%)
   - Price range: ₹100-2000 (configurable)

**Reversal Scans**:
1. **4-7 days down**: Extended decline patterns (can include some green candles)
2. **Base Filters**:
   - Volume: At least 1 day with 1M+ volume in last month
   - ADR: Above configurable threshold
   - Price range: ₹100-2000 (configurable)

**Manual Review Process**:
1. Daily scan execution after market close
2. Candidate list generation
3. User chart review (top to bottom navigation)
4. Manual cup pattern identification for continuation
5. Add to "Next Day Trade List" with scan source notes
6. Separate tabs: Continuation Candidates, Reversal Candidates, Next Day Trade List

### Application 2: Live Trading & Execution

**Purpose**: Real-time trading with hybrid API setup for order execution.

**Core Features**:
- Real-time monitoring of "Next Day Trade List"
- Strong start detection (open = low in first 3 minutes)
- Gap analysis (gap up for continuation, gap down for reversal)
- Automated position sizing calculations
- Order execution via Dhan API
- Risk monitoring and management

**Trading Rules Integration**:
- Entry: Strong start or gap analysis
- Position sizing: Risk-based calculation (0.5% initially)
- Exit: 50% at 15% profit or 3 days, trailing stops
- Risk management: Maximum 5% drawdown stop

### Application 3: Chart Analysis & Pattern Recognition

**Purpose**: Advanced chart analysis and manual pattern identification.

**Core Features**:
- Multi-timeframe analysis (Daily, 3-min, 15-min)
- Simple chart view with zoom/pan functionality
- Top to bottom navigation through watchlists
- Manual pattern recognition (cup patterns, range formations)
- Integration with Application 1 for seamless workflow

**Chart Types**:
- Daily charts for trend analysis and setup identification
- 3-minute charts for strong start confirmation
- 15-minute charts for intraday analysis

### Application 4: Trade Journal & Performance Analytics

**Purpose**: Comprehensive trade tracking and performance analysis.

**Core Features**:
- Automated trade logging
- Performance metrics (win rate, risk-reward, drawdown)
- Setup quality analysis
- Continuous improvement tracking
- Tax and compliance reporting

**Analytics**:
- Trade-by-trade performance tracking
- Setup type performance comparison
- Risk management effectiveness
- Continuous learning and improvement

## Technical Architecture

### Code Organization and Modularity

**Modular Architecture Principles**:
- **Single Responsibility**: Each module/class has one clear purpose
- **Separation of Concerns**: Business logic, data access, and UI are separate
- **Maximum File Size**: No file should exceed 200 lines of code
- **Clear Dependencies**: Explicit imports and minimal circular dependencies

**Scanner Module Structure**:
```
src/scanner/
├── scanner.py              - Main scanner class and orchestration
├── filters.py              - Common filtering logic and validation
├── continuation_analyzer.py - Continuation setup analysis
└── reversal_analyzer.py    - Reversal setup analysis
```

**Module Responsibilities**:
- **scanner.py**: High-level scan orchestration, parameter management, result aggregation
- **filters.py**: Reusable filter methods (price range, ADR, volume checks)
- **continuation_analyzer.py**: Continuation-specific logic and MA analysis
- **reversal_analyzer.py**: Reversal-specific logic and decline pattern detection

**Coding Standards**:
- **Remove Dead Code**: Delete unused parameters, methods, and imports immediately
- **Parameter Cleanup**: Only keep parameters that are actively used in logic
- **Method Consolidation**: Combine similar methods, eliminate redundant checks
- **Clear Documentation**: Each module/class/method has clear docstrings

### Technology Stack

**Core Technologies**:
- **Language**: Python 3.10+ (free, versatile, excellent for data analysis)
- **GUI Framework**: PyQt6/PySide6 (professional desktop app feel)
- **Data Libraries**: yfinance, pandas, numpy
- **Charting**: Plotly (TradingView-like interactive charts)
- **APIs**: Upstox (data), Dhan (execution), NSEpy (NSE data)

**Database**:
- **Primary**: SQLite for local data storage
- **Caching**: Pickle files for chart data
- **Metadata**: JSON configuration files

**Data Management**:
- **Primary Source**: yfinance (free, reliable EOD data)
- **Fallback**: NSEpy for robust NSE data
- **Caching**: Local storage with incremental updates
- **Update Strategy**: Daily EOD updates (1-5 minutes)

### System Integration

**Application Communication**:
- Shared database for watchlists and trade data
- Inter-application messaging for real-time updates
- Common configuration system
- Unified user authentication and preferences

**Data Flow**:
1. **Daily Scan**: Application 1 runs scans → generates candidates
2. **Manual Review**: User reviews charts in Application 3
3. **Watchlist Management**: Candidates moved to Next Day Trade List
4. **Live Trading**: Application 2 monitors and executes trades
5. **Journaling**: All trades logged in Application 4

### Performance Requirements

**Scan Performance**:
- **Target**: <30 seconds for 2000 stocks
- **Optimization**: Parallel processing, efficient algorithms
- **Caching**: Smart caching of frequently accessed data

**Chart Performance**:
- **Target**: <200ms chart switching
- **Optimization**: Pre-loading, efficient rendering
- **Memory**: ~50MB for 50 cached charts

**Data Updates**:
- **Daily Updates**: <5 minutes for full market data
- **Real-time**: WebSocket integration for live data
- **Incremental**: Smart updates to minimize bandwidth

## Configuration and Customization

### Base Filters Configuration

**Volume Settings**:
- Minimum volume threshold (default: 1M shares)
- Lookback period (default: 1 month)
- Volume spike detection

**Price Settings**:
- Minimum price (default: ₹100)
- Maximum price (default: ₹2000)
- Price range filtering

**ADR Settings**:
- Minimum ADR threshold (default: 3-4%)
- ADR calculation period (default: 20 days)
- ADR-based stock classification

### Scan Parameters

**Continuation Scan Settings**:
- Proximity to highs (default: 5%)
- 20MA angle threshold (default: >0°)
- Consolidation period (default: 3-7 days)

**Reversal Scan Settings**:
- Decline period (default: 4-7 days)
- Minimum decline percentage
- Volume confirmation requirements

### Trading Rules Configuration

**Risk Management**:
- Maximum risk per trade (default: 0.5%)
- Maximum drawdown (default: 5%)
- Position sizing algorithm

**Exit Rules**:
- Profit target (default: 15%)
- Time-based exit (default: 3 days)
- Trailing stop parameters

## Security and Compliance

### Data Security
- Local data storage with encryption
- Secure API key management
- User authentication and authorization

### Regulatory Compliance
- SEBI compliance for algorithmic trading
- Data privacy and protection
- Audit trails for all trading activities

### Risk Controls
- Built-in risk management rules
- Position size limits
- Drawdown protection mechanisms

## Deployment and Maintenance

### Development Environment
- Version control with Git
- Continuous integration/continuous deployment
- Automated testing framework
- Documentation generation

### Production Deployment
- Standalone executable packaging
- Installation and setup automation
- User support and documentation
- Regular updates and maintenance

### Monitoring and Support
- System health monitoring
- Performance metrics tracking
- User support system
- Regular system updates

## Future Enhancements

### Phase 2 Features
- Advanced pattern recognition algorithms
- Machine learning for setup quality scoring
- Mobile application for monitoring
- Advanced risk management tools

### Phase 3 Features
- Multi-market support (US, European markets)
- Options trading integration
- Advanced portfolio management
- AI-powered trade suggestions

This architecture provides a solid foundation for implementing a comprehensive trading system that combines systematic scanning with manual review and automated execution, following the proven trading strategies outlined in the course materials.
