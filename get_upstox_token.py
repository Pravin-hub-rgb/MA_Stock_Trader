#!/usr/bin/env python3
"""
Helper script to exchange Upstox authorization code for access token
"""

import requests
import json

def exchange_code_for_token(auth_code: str) -> dict:
    """Exchange authorization code for access token"""

    url = "https://api.upstox.com/v3/login/authorization/token"

    data = {
        "code": auth_code,
        "client_id": "6ec86817-5a40-4d0f-929f-45486fb7193c",
        "client_secret": "5yqgvu4mst",
        "redirect_uri": "http://localhost:3000",
        "grant_type": "authorization_code"
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    try:
        response = requests.post(url, data=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            print(" SUCCESS! Access token obtained:")
            print("=" * 50)
            print(result.get("access_token"))
            print("=" * 50)
            print("\n Copy this token and paste it in the frontend.")
            return result
        else:
            print(f" ERROR: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f" ERROR: {e}")
        return None

if __name__ == "__main__":
    print("🔑 Upstox Token Exchange Helper")
    print("=" * 40)
    print("Paste your authorization code (from the URL after logging in):")

    auth_code = input().strip()

    if auth_code:
        exchange_code_for_token(auth_code)
    else:
        print(" No code provided")
