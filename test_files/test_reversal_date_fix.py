#!/usr/bin/env python3
"""
Test to verify that the reversal scanner is also fixed and using the correct date.
This test confirms that the reversal scanner is now using 1 Feb 2026 (Budget Day) 
instead of 30 Jan 2026, and properly filtering reversal candidates.
"""

import sys
import os
from datetime import date, datetime
import pandas as pd

# Add src to path
sys.path.append('src')

from src.scanner.scanner import scanner
from src.utils.data_fetcher import data_fetcher

def test_reversal_scanner_date_detection():
    """Test that reversal scanner uses the correct date (1 Feb 2026)"""
    print("🔍 TESTING REVERSAL SCANNER DATE DETECTION")
    print("=" * 60)
    
    try:
        # Test what date the reversal scanner automatically detects
        print("Running reversal scanner to see auto-detected date...")
        
        # Create a custom progress callback to capture the date
        detected_date = None
        
        def progress_callback(value, message):
            nonlocal detected_date
            if message.startswith("SCAN_DATE:"):
                detected_date = message.split(":", 1)[1]
                print(f"   📅 Reversal scanner detected date: {detected_date}")
        
        results = scanner.run_reversal_scan(
            scan_date=None,  # Auto-detect
            progress_callback=progress_callback
        )
        
        if detected_date:
            print(f"✅ Reversal scanner used date: {detected_date}")
        else:
            print("❌ Could not detect reversal scanner date")
        
        print(f"   Found {len(results)} reversal candidates")
        
        # Check if any problematic stocks are in results
        # (Stocks that should be filtered out on 1 Feb but might pass on 30 Jan)
        target_stocks = ['MMFL', 'TENNIND']  # These were problematic in continuation
        found_stocks = []
        
        for stock in results:
            symbol = stock.get('symbol', '')
            if symbol in target_stocks:
                found_stocks.append(symbol)
                print(f"   🎯 FOUND {symbol} in reversal results!")
                print(f"      Close: {stock.get('close', 'N/A')}")
                print(f"      Period: {stock.get('period', 'N/A')}")
                print(f"      Decline: {stock.get('decline_percent', 'N/A')}%")
        
        if found_stocks:
            print(f"\n❌ POTENTIAL ISSUE: Reversal scanner returned {found_stocks}")
            print("   This might indicate the scanner is still using old data")
        else:
            print(f"\n✅ GOOD: Reversal scanner correctly filtered out {target_stocks}")
        
        return detected_date, len(results)
        
    except Exception as e:
        print(f"❌ Error testing reversal scanner date: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

def test_reversal_scanner_different_dates():
    """Test reversal scanner with different dates to see the difference"""
    print("\n" + "="*60)
    print("🔍 TESTING REVERSAL SCANNER WITH DIFFERENT DATES")
    print("=" * 60)
    
    # Test dates
    test_dates = [
        date(2026, 1, 30),  # Friday before 1st Feb
        date(2026, 2, 1),   # Saturday (Budget Day - market open)
    ]
    
    target_stocks = ['MMFL', 'TENNIND']
    
    for test_date in test_dates:
        print(f"\n{'='*20} TESTING DATE: {test_date} {'='*20}")
        
        try:
            # Test each target stock individually
            for symbol in target_stocks:
                print(f"\n--- {symbol} on {test_date} ---")
                
                # Get data for this specific date
                data = data_fetcher.get_data_for_date_range(
                    symbol,
                    test_date - pd.Timedelta(days=50),  # Need 50 days for reversal analysis
                    test_date
                )
                
                if data.empty:
                    print(f"   ❌ No data for {symbol}")
                    continue
                
                # Calculate technical indicators
                data = data_fetcher.calculate_technical_indicators(data)
                latest = data.iloc[-1]
                
                # Check if the date exists in the data
                target_timestamp = pd.Timestamp(test_date)
                has_date = target_timestamp in data.index
                
                if not has_date:
                    print(f"   ❌ Date {test_date} not found in data")
                    continue
                
                # Get the row for the specific date
                date_row = data.loc[target_timestamp]
                
                print(f"   Close: {date_row['close']:.2f}")
                print(f"   SMA20: {date_row['ma_20']:.2f}")
                print(f"   Above MA: {date_row['close'] > date_row['ma_20']}")
                
                # Check ADR
                adr_pct = date_row.get('adr_percent', 0)
                print(f"   ADR: {adr_pct:.2f}%")
                
                # Check if this stock would pass basic reversal filters
                adr_pass = adr_pct >= 0.03  # 3% ADR threshold
                price_pass = 100 <= date_row['close'] <= 10000  # Price filter
                
                print(f"   ADR filter pass: {adr_pass}")
                print(f"   Price filter pass: {price_pass}")
                
        except Exception as e:
            print(f"   ❌ Error testing {symbol}: {e}")

def test_reversal_api_endpoint():
    """Test the reversal API endpoint to see if it's also fixed"""
    print("\n" + "="*60)
    print("🔍 TESTING REVERSAL API ENDPOINT")
    print("=" * 60)
    
    try:
        import requests
        import time
        import json
        
        # Call the reversal API endpoint
        print("Calling reversal API endpoint...")
        
        url = "http://localhost:8001/api/scanner/reversal"
        payload = {
            "date": None,
            "filters": {
                "min_price": 100,
                "max_price": 10000,
                "min_decline_percent": 10
            }
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            operation_id = result.get('operation_id')
            
            print(f"✅ API call successful")
            print(f"   Operation ID: {operation_id}")
            
            # Poll for results
            print("   Polling for results...")
            
            for i in range(20):  # Wait up to 200 seconds
                time.sleep(10)
                
                status_url = f"http://localhost:8001/api/scanner/status/{operation_id}"
                status_response = requests.get(status_url)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    progress = status_data.get('progress', 0)
                    message = status_data.get('message', '')
                    
                    print(f"   Progress: {progress}% - {message}")
                    
                    if status == 'completed':
                        results_count = status_data.get('result', {}).get('results_count', 0)
                        print(f"✅ Reversal scan completed!")
                        print(f"   Found {results_count} candidates")
                        
                        # Check if MMFL/TENNIND are in results
                        target_stocks = ['MMFL', 'TENNIND']
                        found_stocks = []
                        
                        if 'result' in status_data and 'results' in status_data['result']:
                            for stock in status_data['result']['results']:
                                symbol = stock.get('symbol', '')
                                if symbol in target_stocks:
                                    found_stocks.append(symbol)
                                    print(f"   🎯 FOUND {symbol} in API results!")
                                    print(f"      Close: {stock.get('close', 'N/A')}")
                                    print(f"      Period: {stock.get('period', 'N/A')}")
                                    print(f"      Decline: {stock.get('decline_percent', 'N/A')}%")
                        
                        if found_stocks:
                            print(f"\n❌ POTENTIAL ISSUE: API returned {found_stocks}")
                        else:
                            print(f"\n✅ GOOD: API correctly filtered out {target_stocks}")
                        
                        return True
                    
                    elif status == 'error':
                        error = status_data.get('error', 'Unknown error')
                        print(f"❌ Scan failed: {error}")
                        return False
                        
                else:
                    print(f"❌ Status check failed: {status_response.status_code}")
                    return False
            
            print("❌ Scan timed out")
            return False
            
        else:
            print(f"❌ API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing reversal API: {e}")
        return False

def main():
    """Main test function"""
    print("🔍 REVERSAL SCANNER DATE FIX VERIFICATION")
    print("=" * 60)
    print("Testing to verify that the reversal scanner is also fixed")
    print("and using the correct date (1 Feb 2026) instead of 30 Jan 2026")
    
    # Test 1: Reversal scanner date detection
    detected_date, candidate_count = test_reversal_scanner_date_detection()
    
    # Test 2: Test with different dates
    test_reversal_scanner_different_dates()
    
    # Test 3: Test reversal API endpoint
    api_success = test_reversal_api_endpoint()
    
    print("\n" + "="*60)
    print("REVERSAL SCANNER VERIFICATION COMPLETE")
    print("=" * 60)
    
    if detected_date and "2026-02-01" in detected_date:
        print("✅ SUCCESS: Reversal scanner is using the correct date (1 Feb 2026)")
    else:
        print("❌ ISSUE: Reversal scanner may still be using wrong date")
    
    if candidate_count > 0:
        print(f"✅ SUCCESS: Reversal scanner found {candidate_count} candidates")
    else:
        print("⚠️  WARNING: Reversal scanner found no candidates")
    
    if api_success:
        print("✅ SUCCESS: Reversal API endpoint is working correctly")
    else:
        print("❌ ISSUE: Reversal API endpoint may have issues")

if __name__ == "__main__":
    main()