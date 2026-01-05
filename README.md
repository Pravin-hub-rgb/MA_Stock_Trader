# MA Stock Trader

A comprehensive stock trading system for NSE equities implementing continuation and reversal trading strategies with systematic scanning, manual review, and automated execution.

## Overview

This system combines proven trading strategies with modern technology to create a systematic approach to swing trading. The system is designed for traders who want to apply disciplined, rules-based strategies while maintaining manual oversight of trade selection.

## Trading Strategies

### Continuation Moves (80% of trades)
- **Concept**: Stocks in uptrends that correct below 20-day MA, then resume the trend
- **Pattern**: Range expansion → Range contraction → Breakout
- **Timeframe**: 3-5 day moves targeting 15-20% gains
- **Entry**: Strong start (open = low) or gap up with volume confirmation

### Reversal Moves (20% of trades)
- **Concept**: Counter-trend trades in oversold stocks
- **Pattern**: Extended declines → Gap down/climax → Reversal
- **Timeframe**: 3-5 day moves targeting 15% gains
- **Entry**: Gap down with climax bars or strong start after extended decline

## System Components

### Application 1: Market Scanner & Watchlist Manager
- Automated daily scans for continuation and reversal setups
- Configurable base filters (volume, price, ADR)
- Manual chart review with navigation
- Watchlist organization and management

### Application 2: Live Trading & Execution
- Real-time monitoring of "Next Day Trade List"
- Strong start detection (open = low in first 3 minutes)
- Gap analysis (gap up for continuation, gap down for reversal)
- Automated position sizing and order execution

### Application 3: Chart Analysis & Pattern Recognition
- Multi-timeframe analysis (Daily, 3-min, 15-min)
- Simple chart view with zoom/pan functionality
- Manual pattern recognition (cup patterns, range formations)
- Integration with scanner for seamless workflow

### Application 4: Trade Journal & Performance Analytics
- Automated trade logging
- Performance metrics (win rate, risk-reward, drawdown)
- Setup quality analysis
- Continuous improvement tracking

## Technical Requirements

### Prerequisites
- Python 3.10+
- Windows 10/11 (primary development platform)
- NSE trading account (for live trading)

### Core Dependencies
```bash
pip install pandas numpy matplotlib plotly
pip install yfinance nsepy
pip install PyQt6 requests websocket-client
```

### Optional Dependencies
```bash
pip install TA-Lib  # For advanced technical indicators
pip install backtrader  # For backtesting
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/MA_Stock_Trader.git
cd MA_Stock_Trader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API keys:
   - Create `config.json` with your Upstox and Dhan API credentials
   - Set up NSE data sources

4. Run the application:
```bash
python main.py
```

## Usage

### Daily Workflow

1. **Morning Prep (30 minutes)**
   - Run daily scans for continuation and reversal candidates
   - Review candidates in chart analysis module
   - Add qualified candidates to "Next Day Trade List"

2. **Market Hours**
   - Monitor "Next Day Trade List" for strong start opportunities
   - Execute trades based on strong start or gap analysis
   - Manage positions according to exit rules

3. **End of Day**
   - Log all trades in trade journal
   - Review performance metrics
   - Update watchlists for next day

### Key Features

#### Scanner Configuration
- **Base Filters**: Volume, price range, ADR thresholds
- **Continuation Scans**: 5% from 1-month high, rising 20MA, cup patterns
- **Reversal Scans**: 4-7 days decline, volume confirmation, climax bars

#### Risk Management
- **Position Sizing**: Risk-based calculation (0.5% initially)
- **Stop Loss**: 2-4% maximum (tighter for beginners)
- **Drawdown Control**: Stop trading after 5% account loss

#### Trade Execution
- **Entry Rules**: Strong start, gap analysis, volume confirmation
- **Exit Rules**: 50% at 15% profit or 3 days, trailing stops
- **Position Management**: Scale in/out, emergency stops

## Configuration

### Base Filters
```json
{
  "min_volume": 1000000,
  "price_min": 100,
  "price_max": 2000,
  "min_adr": 0.03
}
```

### Scan Parameters
```json
{
  "continuation": {
    "max_distance_from_high": 0.05,
    "min_ma_angle": 0.0,
    "consolidation_days": [3, 7]
  },
  "reversal": {
    "decline_days": [4, 7],
    "min_decline_percent": 0.10
  }
}
```

### Trading Rules
```json
{
  "risk_per_trade": 0.005,
  "max_drawdown": 0.05,
  "profit_target": 0.15,
  "time_exit_days": 3
}
```

## Development

### Project Structure
```
MA_Stock_Trader/
├── docs/                    # Documentation
│   ├── system_architecture.md
│   ├── technical_specifications.md
│   └── user_guide.md
├── src/                     # Source code
│   ├── scanner/            # Market scanning logic
│   ├── trading/            # Trade execution logic
│   ├── charts/             # Chart analysis logic
│   ├── journal/            # Trade journal logic
│   └── utils/              # Utility functions
├── data/                   # Data storage
│   ├── stocks.db           # SQLite database
│   ├── cache/              # Cached data
│   └── logs/               # Application logs
├── config/                 # Configuration files
│   ├── config.json         # Application settings
│   └── api_keys.json       # API credentials
├── tests/                  # Test files
└── main.py                 # Application entry point
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run specific test modules:
```bash
python -m pytest tests/test_scanner.py
python -m pytest tests/test_trading.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and informational purposes only. Trading involves substantial risk and is not suitable for everyone. Users should not invest money they cannot afford to lose. The developers are not financial advisors and are not responsible for any losses incurred through the use of this software.

## Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Email: support@mastrader.com

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Roadmap

### Phase 1: Core System (Current)
- [x] Market scanner with continuation/reversal detection
- [x] Manual chart review workflow
- [x] Basic trade execution
- [x] Trade journal and analytics

### Phase 2: Advanced Features
- [ ] Advanced pattern recognition algorithms
- [ ] Machine learning for setup quality scoring
- [ ] Mobile application for monitoring
- [ ] Advanced risk management tools

### Phase 3: Enterprise Features
- [ ] Multi-market support (US, European markets)
- [ ] Options trading integration
- [ ] Advanced portfolio management
- [ ] AI-powered trade suggestions

## Acknowledgments

This system is based on proven trading strategies and incorporates best practices from professional trading. We acknowledge the contributions of the trading community and the developers of the underlying libraries and APIs.
