#!/usr/bin/env python3
"""
Test the exact API endpoint that the frontend is calling to see what it returns
vs what the frontend is displaying.
"""

import sys
import os
import requests
import json
from datetime import date

# Add src to path
sys.path.append('src')

def test_api_endpoint():
    """Test the exact API endpoint that the frontend is calling"""
    print("🔍 TESTING API ENDPOINT")
    print("=" * 60)
    
    try:
        # Test the continuation scan API endpoint
        url = "http://localhost:8001/api/scanner/continuation"
        
        # Use the same parameters as your frontend
        payload = {
            "date": None,  # Auto-detect latest date
            "filters": {
                "min_price": 100,
                "max_price": 10000,  # Your frontend setting
                "near_ma_threshold": 6,  # Your frontend setting
                "max_body_percentage": 4  # Your frontend setting
            }
        }
        
        print(f"1. CALLING API ENDPOINT: {url}")
        print(f"   Parameters: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        result = response.json()
        print(f"✅ API call successful")
        print(f"   Response: {json.dumps(result, indent=2)}")
        
        operation_id = result.get('operation_id')
        if not operation_id:
            print("❌ No operation_id in response")
            return
        
        # Poll for results
        print(f"\n2. POLLING FOR RESULTS (operation_id: {operation_id})")
        
        for i in range(60):  # Poll for up to 60 seconds
            status_url = f"http://localhost:8001/api/scanner/status/{operation_id}"
            status_response = requests.get(status_url, timeout=10)
            
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   Progress: {status.get('progress', 0)}% - {status.get('message', '...')}")
                
                if status.get('status') == 'completed':
                    print(f"✅ Scan completed!")
                    
                    # Check the results
                    scan_results = status.get('result', {}).get('results', [])
                    print(f"   Found {len(scan_results)} candidates")
                    
                    # Look for MMFL, TENNIND, SAATVIKGL
                    target_stocks = ['MMFL', 'TENNIND', 'SAATVIKGL']
                    found_stocks = []
                    
                    for stock in scan_results:
                        symbol = stock.get('symbol', '')
                        if symbol in target_stocks:
                            found_stocks.append(symbol)
                            print(f"   🎯 FOUND {symbol} in API results!")
                            print(f"      Close: {stock.get('close', 'N/A')}")
                            print(f"      SMA20: {stock.get('sma20', 'N/A')}")
                            print(f"      Dist to MA: {stock.get('dist_to_ma_pct', 'N/A')}%")
                    
                    if found_stocks:
                        print(f"\n❌ PROBLEM: API returned {found_stocks} which are below 20 MA!")
                        print("   This confirms the bug is in the backend scanner logic")
                    else:
                        print(f"\n✅ GOOD: API correctly filtered out {target_stocks}")
                        print("   The bug might be in the frontend display logic")
                    
                    return
                    
                elif status.get('status') == 'error':
                    print(f"❌ Scan failed: {status.get('error', 'Unknown error')}")
                    return
            
            # Wait before next poll
            import time
            time.sleep(1)
        
        print("❌ Scan polling timed out")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running on http://localhost:8001")
        print("   Run: python server.py")
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

def test_direct_scanner():
    """Test the scanner directly with the same parameters"""
    print("\n" + "="*60)
    print("🔍 TESTING DIRECT SCANNER")
    print("=" * 60)
    
    try:
        from src.scanner.scanner import scanner
        
        # Apply the same parameters as your frontend
        scanner.update_price_filters(100, 10000)  # Your frontend settings
        scanner.update_near_ma_threshold(6)       # Your frontend setting
        scanner.update_max_body_percentage(4)     # Your frontend setting
        
        print("1. APPLIED FRONTEND PARAMETERS:")
        print(f"   Min Price: 100")
        print(f"   Max Price: 10000")
        print(f"   Near MA Threshold: 6%")
        print(f"   Max Body Size: 4%")
        
        # Run the scanner directly
        print("\n2. RUNNING DIRECT SCANNER:")
        results = scanner.run_continuation_scan(scan_date=None)
        
        print(f"   Found {len(results)} candidates")
        
        # Look for MMFL, TENNIND, SAATVIKGL
        target_stocks = ['MMFL', 'TENNIND', 'SAATVIKGL']
        found_stocks = []
        
        for stock in results:
            symbol = stock.get('symbol', '')
            if symbol in target_stocks:
                found_stocks.append(symbol)
                print(f"   🎯 FOUND {symbol} in direct scanner!")
                print(f"      Close: {stock.get('close', 'N/A')}")
                print(f"      SMA20: {stock.get('sma20', 'N/A')}")
                print(f"      Dist to MA: {stock.get('dist_to_ma_pct', 'N/A')}%")
        
        if found_stocks:
            print(f"\n❌ PROBLEM: Direct scanner returned {found_stocks} which are below 20 MA!")
            print("   This confirms the bug is in the scanner logic")
        else:
            print(f"\n✅ GOOD: Direct scanner correctly filtered out {target_stocks}")
            print("   The bug might be in the API or frontend logic")
        
    except Exception as e:
        print(f"❌ Error testing direct scanner: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("🔍 API ENDPOINT VS DIRECT SCANNER TEST")
    print("=" * 60)
    print("Testing to identify where the 20 MA bug occurs")
    
    # Test the API endpoint
    test_api_endpoint()
    
    # Test the direct scanner
    test_direct_scanner()
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("Compare the results to identify where the bug occurs:")
    print("1. If API returns wrong results but direct scanner is correct → API bug")
    print("2. If both return wrong results → Scanner logic bug")
    print("3. If both return correct results but frontend shows wrong → Frontend bug")

if __name__ == "__main__":
    main()