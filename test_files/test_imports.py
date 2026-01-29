#!/usr/bin/env python3
"""
Test script to verify all live trading imports work correctly
"""

import sys
import os

# Add src to path
sys.path.append('src')
sys.path.insert(0, os.path.join('src', 'trading', 'live_trading'))

def test_imports():
    """Test all imports for live trading bot"""
    print("🧪 Testing Live Trading Bot Imports")
    print("=" * 50)

    tests = [
        ("stock_monitor", "StockMonitor"),
        ("reversal_monitor", "ReversalMonitor"),
        ("rule_engine", "RuleEngine"),
        ("selection_engine", "SelectionEngine"),
        ("paper_trader", "PaperTrader"),
        ("simple_data_streamer", "SimpleStockStreamer"),
        ("bot_args", "parse_bot_arguments"),
        ("stock_classifier", "StockClassifier"),
    ]

    failed = []

    for module_name, class_name in tests:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {e}")
            failed.append((module_name, class_name))

    # Test upstox_fetcher separately
    try:
        from utils.upstox_fetcher import UpstoxFetcher
        print("✅ utils.upstox_fetcher.UpstoxFetcher")
    except Exception as e:
        print(f"❌ utils.upstox_fetcher.UpstoxFetcher: {e}")
        failed.append(("utils.upstox_fetcher", "UpstoxFetcher"))

    # Test stock_scorer
    try:
        from scanner.stock_scorer import stock_scorer
        print("✅ scanner.stock_scorer.stock_scorer")
    except Exception as e:
        print(f"❌ scanner.stock_scorer.stock_scorer: {e}")
        failed.append(("scanner.stock_scorer", "stock_scorer"))

    print("\n" + "=" * 50)
    if failed:
        print(f"❌ {len(failed)} imports failed")
        for module, cls in failed:
            print(f"   - {module}.{cls}")
        return False
    else:
        print("✅ All imports successful!")
        return True

def test_stock_classifier():
    """Test stock classifier functionality"""
    print("\n🧪 Testing Stock Classifier")
    print("-" * 30)

    try:
        from stock_classifier import StockClassifier
        classifier = StockClassifier()

        # Test reversal classification
        result = classifier.load_reversal_stocks()
        symbols, situations = result

        print(f"✅ Loaded {len(symbols)} reversal stocks:")
        for symbol, situation in situations.items():
            desc = {
                'reversal_s1': 'Uptrend (Continuation method)',
                'reversal_s2': 'Downtrend (Gap down required)'
            }.get(situation, situation)
            print(f"   {symbol}: {desc}")

        # Test continuation
        cont_symbols = classifier.load_continuation_stocks()
        print(f"✅ Loaded {len(cont_symbols)} continuation stocks")

        # Test full config
        config = classifier.get_stock_configuration('r')
        print(f"✅ Generated config for {len(config['symbols'])} stocks")

        return True

    except Exception as e:
        print(f"❌ Stock classifier test failed: {e}")
        return False

def test_argument_parsing():
    """Test argument parsing"""
    print("\n🧪 Testing Argument Parsing")
    print("-" * 30)

    try:
        from bot_args import parse_bot_arguments
        # This will show help, but we can catch it
        import argparse
        try:
            config = parse_bot_arguments()
            print("❌ Should have shown help")
            return False
        except SystemExit:
            print("✅ Help displayed correctly (SystemExit expected)")
            return True

    except Exception as e:
        print(f"❌ Argument parsing test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 LIVE TRADING BOT - IMPORT VERIFICATION")
    print("=" * 60)

    success = True

    # Test imports
    if not test_imports():
        success = False

    # Test classifier
    if not test_stock_classifier():
        success = False

    # Test args (will show help)
    if not test_argument_parsing():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - Ready for live trading!")
        print("\nUsage:")
        print("  python run_live_bot.py c    # Continuation trading")
        print("  python run_live_bot.py r    # Reversal trading")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")

    sys.exit(0 if success else 1)
