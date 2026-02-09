# Continuation Bot Automated Launcher

## Overview

The `launch_continuation_bot.py` script automates the process of launching the continuation trading bot with proper time configuration.

## What It Does

1. **Kills all Python processes** - Ensures clean startup
2. **Updates market open time** - Sets MARKET_OPEN in config.json to current time + 2 minutes
3. **Launches continuation bot** - Starts the trading bot with proper configuration

## Usage

```bash
python launch_continuation_bot.py
```

## Why This Is Needed

- **Prevents connection errors** by setting market open time to 2 minutes in the future
- **Ensures clean startup** by killing any existing Python processes
- **Automates the setup process** for consistent bot launches

## Configuration

The script automatically:
- Reads current IST time
- Adds 2 minutes to set as MARKET_OPEN time
- Updates `config/config.json`
- Launches the continuation bot

## Example Output

```
============================================================
CONTINUATION BOT AUTOMATED LAUNCHER
============================================================
KILLING all Python processes...
✓ All Python processes killed
UPDATING market open time in config.json...
Current time: 16:47:15
Market open time set to: 16:49:15
✓ Market open time updated in config.json
LAUNCHING continuation bot...
✓ Continuation bot launched successfully

🎉 CONTINUATION BOT LAUNCHED SUCCESSFULLY!
============================================================
```

## Notes

- The script uses IST (Asia/Kolkata) timezone
- Market open time is set to current time + 2 minutes
- All Python processes are killed before launching
- The continuation bot will start with the updated configuration