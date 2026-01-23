"""
Command-line argument parsing for live trading bot
"""

import argparse
import sys

def parse_bot_arguments():
    """
    Parse command-line arguments for the live trading bot

    Returns:
        dict: Configuration with mode and other settings
    """
    parser = argparse.ArgumentParser(
        description='Live Trading Bot - Continuation or Reversal Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_live_bot.py c    # Continuation trading
  python run_live_bot.py r    # Reversal trading
        """
    )

    parser.add_argument(
        'mode',
        choices=['c', 'r'],
        help='Trading mode: c=continuation, r=reversal'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode (simulated data)'
    )

    args = parser.parse_args()

    config = {
        'mode': args.mode,
        'trading_mode': 'continuation' if args.mode == 'c' else 'reversal',
        'test_mode': args.test
    }

    print(f"Bot Mode: {config['trading_mode'].upper()}")
    if config['test_mode']:
        print("TEST MODE ENABLED")

    return config
