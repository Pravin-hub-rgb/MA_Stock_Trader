#!/usr/bin/env python3
import requests
import json

# Test the token API endpoint
try:
    response = requests.get('http://localhost:8000/api/token/current')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Also test the config file directly
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    token = config.get('upstox_access_token')
    print(f"\nDirect config read - Token exists: {bool(token)}")
    if token:
        print(f"Token length: {len(token)}")
        print(f"Token starts with: {token[:20]}...")
except Exception as e:
    print(f"Config read error: {e}")
