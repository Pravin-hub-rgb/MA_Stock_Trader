#!/usr/bin/env python3
"""
Test script for stock_scorer.preload_metadata() with timeout handling
"""

import sys
import os
import threading
import time
from typing import List, Dict

# Add src to path
sys.path.insert(0, 'src')

def test_metadata_loading_with_timeout(symbols: List[str], timeout_seconds: int = 60) -> bool:
    """
    Test metadata loading with timeout to prevent hanging

    Args:
        symbols: List of stock symbols to load metadata for
        timeout_seconds: Maximum time to wait for loading

    Returns:
        bool: True if completed successfully, False if timed out
    """
    print(f"Testing metadata loading for {len(symbols)} symbols with {timeout_seconds}s timeout...")

    # Create event to signal completion
    loading_complete = threading.Event()
    exception_caught = None
    loading_success = False

    def load_metadata():
        nonlocal exception_caught, loading_success
        try:
            from src.scanner.stock_scorer import stock_scorer
            stock_scorer.preload_metadata(symbols, prev_closes={})
            loading_success = True
            print("✅ Metadata loading completed successfully")
        except Exception as e:
            exception_caught = e
            print(f"❌ Metadata loading failed: {e}")
        finally:
            loading_complete.set()

    # Start loading in background thread
    load_thread = threading.Thread(target=load_metadata, daemon=True)
    load_thread.start()

    # Wait for completion or timeout
    start_time = time.time()
    completed = loading_complete.wait(timeout=timeout_seconds)
    end_time = time.time()

    if completed:
        if loading_success:
            print(f"✅ Completed in {end_time - start_time:.1f} seconds")
            return True
        else:
            print(f"❌ Failed in {end_time - start_time:.1f} seconds: {exception_caught}")
            return False
    else:
        print(f"⏰ Timed out after {timeout_seconds} seconds")
        return False

    return loading_success

if __name__ == "__main__":
    # Test with reversal symbols
    try:
        # Load symbols from reversal list
        reversal_file = 'src/trading/reversal_list.txt'
        if os.path.exists(reversal_file):
            with open(reversal_file, 'r') as f:
                content = f.read().strip()

            if content:
                symbols = []
                for entry in content.split(','):
                    entry = entry.strip()
                    if entry:
                        # Extract symbol name (remove -u/-d suffix)
                        symbol = entry.split('-')[0]
                        symbols.append(symbol)

                print(f"Loaded {len(symbols)} symbols from reversal list: {symbols[:5]}...")

                # Test metadata loading with 30 second timeout
                success = test_metadata_loading_with_timeout(symbols, timeout_seconds=30)

                if success:
                    print("🎉 Test PASSED - metadata loading works within timeout")
                    sys.exit(0)
                else:
                    print("💥 Test FAILED - metadata loading hangs or fails")
                    sys.exit(1)
            else:
                print("❌ Reversal list is empty")
                sys.exit(1)
        else:
            print(f"❌ Reversal list file not found: {reversal_file}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Test script error: {e}")
        sys.exit(1)
