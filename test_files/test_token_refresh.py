#!/usr/bin/env python3
"""
Test script to check if we can refresh the corrupted token
"""

import requests
import json

def test_token_refresh():
    config = {
        'api_key': '6ec86817-5a40-4d0f-929f-45486fb7193c',
        'api_secret': '5yqgvu4mst',
        'access_token': '**********...mjZc'  # This is the corrupted token
    }

    print('Trying to refresh token...')
    try:
        # This won't work with the corrupted token, but let's see what happens
        response = requests.get('https://api.upstox.com/v2/profile', 
                              headers={'Authorization': f'Bearer {config["access_token"]}'})
        print(f'Response: {response.status_code}')
        print(f'Response text: {response.text}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_token_refresh()