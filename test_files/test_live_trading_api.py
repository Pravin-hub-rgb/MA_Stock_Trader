#!/usr/bin/env python3
import requests
import time

def test_live_trading_api():
    """Test the live trading API endpoints"""

    print("Testing Live Trading API...")
    print("=" * 40)

    try:
        # Test start endpoint
        print("1. Testing START endpoint...")
        response = requests.post('http://localhost:8000/api/live-trading/start',
                               json={'mode': 'continuation'})

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API call successful!")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Process ID: {data.get('process_id', 'No PID')}")
            print(f"   Mode: {data.get('mode', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")

        # Wait a bit for logs to accumulate
        print("\n2. Waiting for logs to accumulate...")
        time.sleep(2)

        # Test logs endpoint
        print("3. Testing LOGS endpoint...")
        response = requests.get('http://localhost:8000/api/live-trading/logs')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            print(f"   Total logs: {len(logs)}")
            print(f"   Is running: {data.get('is_running', False)}")

            if logs:
                print("   Recent logs:")
                for log in logs[-3:]:  # Show last 3 logs
                    print(f"     {log['message']}")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")

        # Test status endpoint
        print("4. Testing STATUS endpoint...")
        response = requests.get('http://localhost:8000/api/live-trading/status')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Is running: {data.get('is_running', False)}")
            print(f"   Process ID: {data.get('process_id')}")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")

        print("\n5. Testing STOP endpoint...")
        response = requests.post('http://localhost:8000/api/live-trading/stop')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Stop successful!")
            print(f"   Message: {data.get('message', 'No message')}")
        else:
            print(f"   ❌ Error: {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_live_trading_api()
