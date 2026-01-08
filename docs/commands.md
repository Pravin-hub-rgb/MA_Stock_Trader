# MA Stock Trader - Commands

## To run Market Breadth Analyzer:
```
python -m src.scanner.market_breadth_analyzer
```

## To run Stock Scanner:
```
python -m src.scanner.gui
```

## To run Live Trading Bot:
```
python run_live_bot.py
```

## Trading Lists Validation:
```
python validate_trading_lists.py
```
Validates continuation_list.txt and reversal_list.txt for live trading readiness. Checks Upstox instrument keys and LTP data retrieval. Run before live trading to ensure no subscription failures.

## Data Update Command (Bhavcopy Integration):

### Update Latest Bhavcopy Data:
```
python update_bhavcopy.py
```
Downloads latest bhavcopy from NSE and integrates missing data into cache. Run after market close (6 PM IST+) to get same-day EOD data for all cached stocks.

## Notes:
- Run all commands from project root directory
- GUI apps open in separate windows
- Market breadth uses caching for fast subsequent runs
- Trading list validation ensures no subscription failures during live trading
- Price filtering (₹100-2000 range)
