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

### Continuation Trading (Gap Up Setup):
```
python run_live_bot.py c
```
Trades stocks from `continuation_list.txt` with gap up validation and standard continuation entry logic.

### Reversal Trading (Gap Down Setup):
```
python run_live_bot.py r
```
Trades stocks from `reversal_list.txt` with gap down validation and reversal-specific entry logic. Supports uptrend reversals (-u) and downtrend reversals (-d) with different sub-case strategies.

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




taskkill /f /im python.exe

create a script instead of running terminal commands


make it modular okay we don't wanna make monolithic code okay create a separate script and import it to where it need
if the code is long make sure to create folder like [relative name]_modules and at right directory too suppose you creating modules for upstox_fetcher so the modules folder should be in same directory as upstox_fetcher so its easy to import from those modules