#!/usr/bin/env python3
"""
Clean Breadth Cache Script
Removes test entries and invalid data from market breadth cache
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.scanner.market_breadth_analyzer import breadth_cache

def clean_breadth_cache():
    """Clean the breadth cache by removing invalid entries"""
    print("Loading breadth cache...")

    # Load current cache
    cache_data = breadth_cache._load_cache()
    original_count = len(cache_data)

    print(f"Found {original_count} entries in cache")

    # Remove invalid entries
    keys_to_remove = []

    for date_key, data in cache_data.items():
        # Remove test entries
        if date_key == 'test':
            keys_to_remove.append(date_key)
            print(f"Found test entry: {date_key}")
            continue

        # Validate data structure
        if not isinstance(data, dict):
            keys_to_remove.append(date_key)
            print(f"Invalid data type for {date_key}: {type(data)}")
            continue

        # Check required fields
        required_fields = ['up_4_5', 'down_4_5', 'up_20_5d', 'down_20_5d', 'above_20ma', 'below_20ma', 'above_50ma', 'below_50ma']
        if not all(field in data for field in required_fields):
            keys_to_remove.append(date_key)
            print(f"Missing required fields for {date_key}")
            continue

    # Remove invalid entries
    for key in keys_to_remove:
        del cache_data[key]

    # Save cleaned cache
    breadth_cache.breadth_cache = cache_data
    breadth_cache._save_cache()

    final_count = len(cache_data)
    removed_count = original_count - final_count

    print(f"Cleaned cache: removed {removed_count} invalid entries")
    print(f"Cache now has {final_count} valid entries")

    return final_count

def reset_breadth_cache():
    """Completely reset the breadth cache"""
    print("Resetting breadth cache...")

    # Clear cache
    breadth_cache.breadth_cache = {}
    breadth_cache._save_cache()

    print("Breadth cache reset - all data cleared")
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        count = reset_breadth_cache()
    else:
        count = clean_breadth_cache()

    print(f"Final cache size: {count} entries")