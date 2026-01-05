#!/usr/bin/env python3
"""
MA Stock Trader - Terminal Version
Simple terminal-based market scanner for continuation and reversal setups
"""

import sys
import os
import logging
from datetime import date
from typing import List, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scanner.scanner import scanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def display_continuation_results(results: List[Dict]):
    """Display continuation scan results in clean terminal format"""
    if not results:
        print("\n❌ No stocks met continuation criteria")
        return
    
    print(f"\n=== CONTINUATION SCANNER RESULTS ===")
    print(f"Date: {date.today().strftime('%Y-%m-%d')}")
    print(f"Total candidates: {len(results)}")
    print("\nQualified Stocks:")
    print("-" * 80)
    print(f"{'Symbol':<12} {'Price (₹)':<12} {'ADR %':<8} {'MA Status':<15} {'Volume':<10} {'Notes'}")
    print("-" * 80)
    
    for result in results:
        symbol = result['symbol']
        price = f"₹{result['price']:.2f}"
        adr = f"{result.get('adr_percent', 0):.2f}%"
        ma_status = "✅ Rising"
        volume = "✅ Confirmed"
        notes = result.get('notes', '')
        
        print(f"{symbol:<12} {price:<12} {adr:<8} {ma_status:<15} {volume:<10} {notes}")

def display_reversal_results(results: List[Dict]):
    """Display reversal scan results in clean terminal format"""
    if not results:
        print("\n❌ No stocks met reversal criteria")
        return
    
    print(f"\n=== REVERSAL SCANNER RESULTS ===")
    print(f"Date: {date.today().strftime('%Y-%m-%d')}")
    print(f"Total candidates: {len(results)}")
    print("\nQualified Stocks:")
    print("-" * 100)
    print(f"{'Symbol':<12} {'Price (₹)':<12} {'ADR %':<8} {'Decline %':<10} {'Volume':<10} {'Score':<6} {'Notes'}")
    print("-" * 100)
    
    for result in results:
        symbol = result['symbol']
        price = f"₹{result.get('price', 0):.2f}"
        adr = f"{result.get('adr_percent', 0):.2f}%"
        decline = f"{result.get('decline_percent', 0)*100:.1f}%"
        score = f"{result.get('score', 0)}"
        volume = "✅ Confirmed"
        notes = result.get('notes', '')
        
        print(f"{symbol:<12} {price:<12} {adr:<8} {decline:<10} {volume:<10} {score:<6} {notes}")

def run_continuation_scan():
    """Run continuation scan with clean output"""
    print("🔍 Running Continuation Scan...")
    print("Criteria: Price ₹100-2000, ADR > 3%, Rising 20MA, 1M+ volume")
    
    try:
        results = scanner.run_continuation_scan()
        display_continuation_results(results)
        return results
    except Exception as e:
        print(f"❌ Error running continuation scan: {e}")
        return []

def run_reversal_scan():
    """Run reversal scan with clean output"""
    print("🔍 Running Reversal Scan...")
    print("Criteria: Price ₹100-2000, ADR > 3%, Extended decline, 1M+ volume")
    
    try:
        results = scanner.run_individual_reversal_scan()
        display_reversation_results()
        return results
    except Exception as e:
        print(f"❌ Error running reversal scan: {e}")
        return []

def main():
    """Main menu for MA Stock Trader Terminal"""
    print("🚀 MA Stock Trader - Terminal Version")
    print("=" * 50)
    print("1. Run Continuation Scan")
    print("2. Run Reversal Scan") 
    print("3. Run Both Scans")
    print("4. Exit")
    
    while True:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            results = run_continuation_scan()
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            results = run_reversedan()
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            print("\n" + "="*80)
            cont_results = run_continuation_scan()
            print("\n" + "="*80)
            rev_results = run_reversal_scan()
            print(f"\n📊 SUMMARY:")
            print(f"Continuation candidates: {len(cont_results)}")
            print(f"Reversal candidates: {len(rev_results)}")
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please select 1-4")

if __name__ == "__main__":
    main()
