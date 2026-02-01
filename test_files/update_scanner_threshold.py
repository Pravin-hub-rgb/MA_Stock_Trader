#!/usr/bin/env python3
"""
Script to update the scanner threshold to 6% as expected.
"""

import sys
import os

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner

def update_scanner_threshold():
    """Update the scanner threshold to 6%"""
    print("🔧 UPDATING SCANNER THRESHOLD")
    print("=" * 60)
    
    print(f"\n1. CURRENT CONFIGURATION:")
    print(f"   Near MA Threshold: {scanner.continuation_params.get('near_ma_threshold', 0)*100:.1f}%")
    
    print(f"\n2. UPDATING THRESHOLD TO 6%:")
    scanner.update_near_ma_threshold(6)  # Set to 6%
    
    print(f"\n3. NEW CONFIGURATION:")
    print(f"   Near MA Threshold: {scanner.continuation_params.get('near_ma_threshold', 0)*100:.1f}%")
    
    print(f"\n✅ Scanner threshold updated to 6%")
    
    return scanner.continuation_params.get('near_ma_threshold', 0)

def main():
    """Main function"""
    threshold = update_scanner_threshold()
    
    print(f"\n{'='*60}")
    print("THRESHOLD UPDATE COMPLETE")
    print(f"{'='*60}")
    print(f"New Near MA Threshold: {threshold*100:.1f}%")
    
    print(f"\n📝 Note: This change will apply to future scanner runs.")
    print(f"   The scanner should now use 6% threshold as expected.")

if __name__ == "__main__":
    main()