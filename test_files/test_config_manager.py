#!/usr/bin/env python3
"""
Test script to check TokenConfigManager status
"""

from src.utils.token_config_manager import token_config_manager

def test_config_manager():
    print('=== Testing TokenConfigManager ===')
    
    status = token_config_manager.get_status()
    print('TokenConfigManager Status:')
    print(f'  Token: {status.get("token")}')
    print(f'  Masked: {status.get("masked_token")}')
    print(f'  Exists: {status.get("exists")}')
    
    # Check what's actually in the config file
    print('\n=== Direct Config File Check ===')
    import json
    with open('upstox_config.json', 'r') as f:
        config = json.load(f)
        print(f'Raw token from file: {config.get("access_token")}')

if __name__ == '__main__':
    test_config_manager()