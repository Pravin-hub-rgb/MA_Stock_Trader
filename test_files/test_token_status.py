#!/usr/bin/env python3
"""
Test script to check token status after fix
"""

from src.utils.token_validator_module import token_validator_module

def test_token_status():
    print('=== Testing Token Status After Fix ===')
    
    status = token_validator_module.get_current_token_status()
    print('Token Validator Module Status:')
    print(f'  Token: {status.get("token")}')
    print(f'  Masked: {status.get("masked")}')
    print(f'  Exists: {status.get("exists")}')
    
    # Test refresh function
    print('\n=== Testing Refresh Function ===')
    refresh_result = token_validator_module.refresh_config()
    print(f'Refresh success: {refresh_result.get("success")}')
    if refresh_result.get('status'):
        refresh_status = refresh_result['status']
        print(f'  Token after refresh: {refresh_status.get("token")}')
        print(f'  Masked after refresh: {refresh_status.get("masked")}')

if __name__ == '__main__':
    test_token_status()