#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live Trading Bot Dispatcher
Launches the appropriate dedicated bot based on mode
"""

import sys
import subprocess
import os

def main():
    """Main dispatcher function"""
    if len(sys.argv) < 2:
        print("Usage: python run_live_bot.py <mode>")
        print("  mode: 'c' for continuation, 'r' for reversal")
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == 'c':
        print("LAUNCHING CONTINUATION BOT (OHLC-only)...")
        bot_script = 'src/trading/live_trading/run_continuation.py'
    elif mode == 'r':
        print("LAUNCHING REVERSAL BOT (Tick-based)...")
        bot_script = 'src/trading/live_trading/run_reversal.py'
    else:
        print(f"ERROR: Invalid mode '{mode}'. Use 'c' for continuation or 'r' for reversal.")
        sys.exit(1)

    # Check if bot script exists
    if not os.path.exists(bot_script):
        print(f"ERROR: {bot_script} not found!")
        print(f"Looking for: {os.path.abspath(bot_script)}")
        sys.exit(1)

    try:
        # Launch the appropriate bot
        print(f"Starting {bot_script}...")
        result = subprocess.run([sys.executable, bot_script] + sys.argv[2:],
                              capture_output=False, text=True)

        # Exit with the same code as the bot
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        print("\nDispatcher interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR launching bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
