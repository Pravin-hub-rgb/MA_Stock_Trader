# MA Stock Trader - User Guide

## Overview

Welcome to MA Stock Trader! This comprehensive trading system implements proven continuation and reversal trading strategies with systematic scanning, manual review, and automated execution.

## Quick Start

### 1. Installation

1. **Install Python 3.10+** (if not already installed)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

### 2. First Time Setup

1. **Database Initialization**: The system will automatically create the SQLite database
2. **Data Source**: By default, uses Yahoo Finance for NSE data
3. **Configuration**: Edit `config/config.json` to customize settings

### 3. Daily Workflow

#### Morning (30 minutes)
1. **Run Scans**: Use the scanner to find continuation and reversal candidates
2. **Review Charts**: Manually review candidates in the chart analysis module
3. **Create Watchlists**: Add qualified candidates to "Next Day Trade List"

#### Market Hours
1. **Monitor Watchlist**: Watch for strong start opportunities
2. **Execute Trades**: Enter trades based on strong start or gap analysis
3. **Manage Positions**: Follow exit rules and risk management

#### End of Day
1. **Log Trades**: Record all trades in the trade journal
2. **Review Performance**: Analyze setup quality and performance
3. **Update Watchlists**: Prepare for next day

## Scanner Usage

### Running Scans

1. **Open Scanner**: Launch the scanner GUI
2. **Select Scan Type**: Choose "Continuation" or "Reversal"
3. **Set Date**: Choose scan date (default: today)
4. **Run Scan**: Click "Run Scan" button
5. **Review Results**: Analyze candidates in the results table

### Scan Parameters

#### Continuation Scans
- **5% from 1-month high**: Stocks coming back up from recent lows
- **Rising 20MA**: Moving average angle > 0°
- **Volume Confirmation**: At least 1 day with 1M+ volume in last month
- **ADR**: Average Daily Range > 3%
- **Price Range**: ₹100-2000 (configurable)

#### Reversal Scans
- **4-7 days decline**: Extended decline patterns
- **Volume Confirmation**: At least 1 day with 1M+ volume
- **ADR**: Average Daily Range > 3%
- **Price Range**: ₹100-2000 (configurable)

### Manual Review Process

1. **Chart Analysis**: Review daily charts for pattern confirmation
2. **Cup Pattern**: For continuation, look for price above MA → down → back up → settle
3. **Volume Analysis**: Confirm volume patterns support the setup
4. **Add to Watchlist**: Move qualified candidates to appropriate watchlists

## Trading Rules

### Entry Rules

#### Strong Start (Primary)
- **Definition**: Open = Low (within 1% tolerance) in first 3 minutes
- **Timing**: Enter within first 3 minutes of market open
- **Confirmation**: Price stays strong throughout the period

#### Gap Analysis
- **Gap Up**: Open > Previous Close with Low > Previous Close
- **Gap Down**: For reversal setups, gap down with climax bars
- **Volume**: 25-30% of daily volume in first 3-5 minutes

### Exit Rules

#### Profit Taking
- **50% Position**: Exit at 15% profit OR after 3 days (whichever comes first)
- **Cost Protection**: Move stop to break-even after 3-5% gain
- **Trailing Stop**: Follow 20-day MA for remaining position

#### Risk Management
- **Stop Loss**: 2-4% maximum (tighter for beginners)
- **Emergency Stop**: Exit immediately if price breaks below key support
- **Time Exit**: Exit if no progress after 3 days

### Position Sizing

#### Risk-Based Calculation
```python
Risk Amount = Account Size × Risk Percentage
Risk Per Share = |Entry Price - Stop Loss|
Position Size = Risk Amount ÷ Risk Per Share
```

#### Risk Guidelines
- **Beginners**: 0.5% risk per trade
- **Intermediate**: 1-2% risk per trade
- **Advanced**: 2-4% risk per trade

### Drawdown Management

#### Stop Trading Rules
- **5% Drawdown**: Stop trading for 10 days
- **Review Period**: Analyze what went wrong
- **Return Strategy**: Come back with reduced position sizes

## Watchlist Management

### Watchlist Types

1. **Continuation Candidates**: Stocks meeting continuation criteria
2. **Reversal Candidates**: Stocks meeting reversal criteria
3. **Next Day Trades**: Qualified candidates for next day trading

### Manual Review Workflow

1. **Scan Results**: Review automated scan results
2. **Chart Analysis**: Manually verify patterns
3. **Add Notes**: Document reasoning for each addition
4. **Prioritize**: Rank candidates by confidence level

### Chart Navigation

- **Keyboard Navigation**: Use ↑↓ keys to cycle through watchlist stocks
- **Multi-Timeframe**: View daily, 3-minute, and 15-minute charts
- **Pattern Recognition**: Manually identify cup patterns and range formations

## Risk Management

### Core Principles

1. **Risk First**: Always consider risk before potential reward
2. **Position Sizing**: Use systematic position sizing based on risk
3. **Stop Losses**: Always use predetermined stop levels
4. **Diversification**: Don't put all capital in one trade

### Risk Control Measures

#### Maximum Risk Per Trade
- **Beginners**: 0.5% of account
- **Intermediate**: 1-2% of account
- **Advanced**: 2-4% of account

#### Maximum Drawdown
- **Stop Trading**: After 5% account loss
- **Recovery Period**: 10-day break minimum
- **Position Reduction**: Reduce size after losses

#### Position Limits
- **Concentration**: Don't over-concentrate in one sector
- **Correlation**: Avoid highly correlated positions
- **Liquidity**: Ensure adequate liquidity for position sizes

## Performance Tracking

### Trade Journal Features

1. **Automated Logging**: All trades automatically recorded
2. **Performance Metrics**: Win rate, risk-reward, drawdown tracking
3. **Setup Analysis**: Quality assessment of different setup types
4. **Continuous Improvement**: Identify patterns in winners and losers

### Key Metrics

#### Profitability Metrics
- **Win Rate**: Percentage of winning trades
- **Average Win**: Size of average winning trade
- **Average Loss**: Size of average losing trade
- **Profit Factor**: Total profits ÷ Total losses

#### Risk Metrics
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Risk-Adjusted Returns**: Returns relative to risk taken
- **Consistency**: Month-over-month performance stability

#### Setup Quality
- **Continuation Performance**: How well continuation setups work
- **Reversal Performance**: How well reversal setups work
- **Pattern Recognition**: Accuracy of manual pattern identification

## Troubleshooting

### Common Issues

#### Scanner Not Finding Candidates
- **Check Date**: Ensure correct scan date
- **Filters**: Review base filter settings
- **Data**: Verify data source connectivity
- **Market**: Consider overall market conditions

#### GUI Not Loading
- **Dependencies**: Ensure PyQt6 is installed
- **Python Path**: Check Python path includes src directory
- **Permissions**: Verify file access permissions

#### Database Errors
- **File Access**: Check data directory permissions
- **Corruption**: Delete and recreate database if corrupted
- **Connections**: Ensure no other processes using database

### Getting Help

1. **Documentation**: Check this user guide and technical specifications
2. **Logs**: Review application logs in `data/logs/`
3. **Issues**: Create GitHub issue for bugs or feature requests
4. **Community**: Join Discord community for support

## Advanced Features

### Custom Scans

1. **Parameter Tuning**: Adjust scan parameters in config
2. **Custom Filters**: Add custom filters for specific strategies
3. **Multi-Market**: Extend to other markets (US, European)

### Automation

1. **Scheduled Scans**: Set up automated daily scans
2. **Alerts**: Configure email or SMS notifications
3. **Integration**: Connect with broker APIs for automated execution

### Backtesting

1. **Historical Analysis**: Test strategies on historical data
2. **Parameter Optimization**: Optimize scan parameters
3. **Strategy Validation**: Validate strategy effectiveness

## Best Practices

### Trading Discipline

1. **Follow Rules**: Stick to established trading rules
2. **Emotional Control**: Avoid emotional decision-making
3. **Continuous Learning**: Learn from every trade
4. **Patience**: Wait for high-quality setups

### Risk Management

1. **Never Revenge Trade**: Don't try to immediately recover losses
2. **Position Sizing**: Always use proper position sizing
3. **Stop Losses**: Never move stop losses further away
4. **Diversification**: Don't put all eggs in one basket

### Continuous Improvement

1. **Trade Review**: Review every trade for lessons
2. **Setup Analysis**: Analyze what makes setups successful
3. **Market Adaptation**: Adapt to changing market conditions
4. **Skill Development**: Continuously improve trading skills

## Disclaimer

This software is for educational and informational purposes only. Trading involves substantial risk and is not suitable for everyone. Users should not invest money they cannot afford to lose. The developers are not financial advisors and are not responsible for any losses incurred through the use of this software.

## Support

For additional support:
- **Documentation**: Complete documentation in `/docs`
- **Issues**: GitHub issues for bugs and feature requests
- **Community**: Discord community for user discussions
- **Email**: support@mastrader.com

Remember: Successful trading requires discipline, patience, and continuous learning. Use this system as a tool to help you apply proven strategies systematically, but always trade responsibly and within your risk tolerance.
