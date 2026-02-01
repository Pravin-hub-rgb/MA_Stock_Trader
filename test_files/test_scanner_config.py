#!/usr/bin/env python3
"""
Test to check the actual scanner configuration and see what threshold is being used.
"""

import sys
import os
from datetime import date

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner

def check_scanner_config():
    """Check the actual scanner configuration"""
    print("🔍 SCANNER CONFIGURATION CHECK")
    print("=" * 60)
    
    print(f"\n1. CONTINUATION SCANNER PARAMETERS:")
    print(f"   {scanner.continuation_params}")
    
    print(f"\n2. CURRENT THRESHOLD SETTINGS:")
    near_ma_threshold = scanner.continuation_params.get('near_ma_threshold', 'NOT SET')
    print(f"   Near MA Threshold: {near_ma_threshold} ({near_ma_threshold*100:.1f}% if numeric)")
    
    max_body_threshold = scanner.continuation_params.get('max_body_percentage', 'NOT SET')
    print(f"   Max Body Threshold: {max_body_threshold} ({max_body_threshold*100:.1f}% if numeric)")
    
    print(f"\n3. COMMON PARAMETERS:")
    print(f"   Price Min: {scanner.common_params.get('price_min', 'NOT SET')}")
    print(f"   Price Max: {scanner.common_params.get('price_max', 'NOT SET')}")
    print(f"   Min ADR: {scanner.common_params.get('min_adr', 'NOT SET')}")
    print(f"   Volume Threshold: {scanner.common_params.get('volume_threshold', 'NOT SET')}")
    
    print(f"\n4. REVERSAL SCANNER PARAMETERS:")
    print(f"   {scanner.reversal_params}")
    
    return {
        'continuation_params': scanner.continuation_params,
        'common_params': scanner.common_params,
        'reversal_params': scanner.reversal_params
    }

def main():
    """Main test function"""
    config = check_scanner_config()
    
    print(f"\n{'='*60}")
    print("CONFIGURATION SUMMARY")
    print(f"{'='*60}")
    
    near_ma_threshold = config['continuation_params'].get('near_ma_threshold', 0)
    print(f"Current Near MA Threshold: {near_ma_threshold*100:.1f}%")
    
    if near_ma_threshold == 0.05:
        print("⚠️  Scanner is using 5% threshold (default)")
        print("   But you mentioned using 6% threshold")
        print("   This might explain the discrepancy!")
    elif near_ma_threshold == 0.06:
        print("✅ Scanner is using 6% threshold as expected")
    else:
        print(f"❓ Scanner is using {near_ma_threshold*100:.1f}% threshold")

if __name__ == "__main__":
    main()