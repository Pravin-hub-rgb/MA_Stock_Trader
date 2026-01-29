#!/usr/bin/env python3
"""
Test script to verify the token status fix
"""

import requests
import json

def test_token_status_fix():
    print('=== Testing Token Status Fix ===')
    
    try:
        # 1. Get current token status (should return real token now)
        result = requests.get('http://localhost:8001/api/token/current').json()
        print('Current token status:')
        print(f'  Token: {result["token"][:20] if result["token"] else "None"}...')
        print(f'  Masked: {result["masked"]}')
        print(f'  Exists: {result["exists"]}')
        
        # 2. Test validation with the real token
        if result['token']:
            validate_result = requests.post('http://localhost:8001/api/token/validate', 
                                          headers={'Content-Type': 'application/json'}, 
                                          data=json.dumps({'token': result['token']})).json()
            print(f'\nValidation result: {validate_result["valid"]}')
            print(f'Validation message: {validate_result.get("message", "No message")}')
        else:
            print('\nNo token found to validate')
            
        print('\n=== Test Complete ===')
        
    except Exception as e:
        print(f'Error during test: {e}')

if __name__ == '__main__':
    test_token_status_fix()