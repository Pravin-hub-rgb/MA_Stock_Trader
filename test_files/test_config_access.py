#!/usr/bin/env python3
"""
Test Config File Access for Reversal Bot
"""

import sys
import os

def test_config_access():
    """Test if the config file can be accessed correctly"""

    print("Testing Config File Access")
    print("=" * 40)

    # Step 1: Check config file exists
    config_path = os.path.abspath('upstox_config.json')
    print(f"Config path: {config_path}")
    print(f"File exists: {os.path.exists(config_path)}")

    if not os.path.exists(config_path):
        print("❌ Config file not found")
        return False

    # Step 2: Try to read config file
    try:
        with open(config_path, 'r') as f:
            import json
            config = json.load(f)
        print("✅ Config file readable")
        print(f"   API Key: {'*' * 10}...{config.get('api_key', 'MISSING')[-4:] if config.get('api_key') else 'MISSING'}")
        print(f"   Access Token: {'*' * 10}...{config.get('access_token', 'MISSING')[-4:] if config.get('access_token') else 'MISSING'}")
    except Exception as e:
        print(f"❌ Cannot read config file: {e}")
        return False

    # Step 3: Test UpstoxFetcher initialization
    print("\nTesting UpstoxFetcher initialization...")

    # Save current directory
    original_cwd = os.getcwd()

    try:
        # Simulate reversal bot directory change
        sys.path.insert(0, os.path.join(original_cwd, 'src'))

        # Get absolute path to config file BEFORE changing directory
        config_file_path = os.path.abspath('upstox_config.json')
        print(f"Absolute config path: {config_file_path}")

        # Change to src directory (like reversal bot does)
        os.chdir(os.path.join(original_cwd, 'src'))
        print(f"Changed to directory: {os.getcwd()}")

        # Try to initialize UpstoxFetcher with absolute path
        from utils.upstox_fetcher import UpstoxFetcher
        fetcher = UpstoxFetcher(config_file=config_file_path)
        print("✅ UpstoxFetcher initialized with absolute config path")

        # Test API call
        test_result = fetcher.get_ltp_data('RELIANCE')
        if test_result and 'cp' in test_result:
            print(f"✅ API test successful: RELIANCE prev close = ₹{test_result['cp']}")
            return True
        else:
            print(f"❌ API test failed: {test_result}")
            return False

    except Exception as e:
        print(f"❌ UpstoxFetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original directory
        os.chdir(original_cwd)

def main():
    """Main test function"""
    try:
        success = test_config_access()
        if success:
            print("\n✅ Config access test PASSED")
        else:
            print("\n❌ Config access test FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
