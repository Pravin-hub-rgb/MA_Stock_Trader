#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Continuation Bot Launcher

This script:
1. Kills all Python processes
2. Sets current time + 2 minutes in config.json for MARKET_OPEN
3. Runs the continuation bot
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime, timedelta
import pytz

def kill_python_processes():
    """Kill all Python processes"""
    print("KILLING all Python processes...")
    try:
        # Kill all Python processes
        subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                      capture_output=True, text=True, timeout=10)
        print("✓ All Python processes killed")
        time.sleep(2)  # Wait for processes to fully terminate
    except Exception as e:
        print(f"Warning: Could not kill all Python processes: {e}")

def update_market_open_time():
    """Update MARKET_OPEN time in config.py to current time + 2 minutes"""
    print("UPDATING market open time in config.py...")
    
    config_path = 'src/trading/live_trading/config.py'
    
    try:
        # Get current IST time
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        
        # Add 2 minutes
        market_open_time = current_time + timedelta(minutes=2)
        
        # Format as time string (HH:MM:SS)
        market_open_str = market_open_time.strftime('%H, %M')
        
        print(f"Current time: {current_time.strftime('%H:%M:%S')}")
        print(f"Market open time set to: {market_open_time.strftime('%H:%M:%S')}")
        
        # Read current config
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Update MARKET_OPEN line
        import re
        pattern = r'MARKET_OPEN = time\(\d+,\s*\d+\)'
        replacement = f'MARKET_OPEN = time({market_open_str})'
        
        updated_content = re.sub(pattern, replacement, config_content)
        
        # Write back to file
        with open(config_path, 'w') as f:
            f.write(updated_content)
        
        print("✓ Market open time updated in config.py")
        
    except Exception as e:
        print(f"ERROR updating config.py: {e}")
        return False
    
    return True

def launch_continuation_bot():
    """Launch the continuation bot"""
    print("LAUNCHING continuation bot...")
    
    try:
        # Launch the bot
        subprocess.run([sys.executable, 'src/trading/live_trading/run_continuation.py'], 
                      check=True)
        print("✓ Continuation bot launched successfully")
    except subprocess.CalledProcessError as e:
        print(f"ERROR launching continuation bot: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("CONTINUATION BOT AUTOMATED LAUNCHER")
    print("=" * 60)
    
    # Step 1: Kill Python processes
    kill_python_processes()
    
    # Step 2: Update market open time
    if not update_market_open_time():
        print("Failed to update market open time. Exiting.")
        return
    
    # Step 3: Launch bot
    if launch_continuation_bot():
        print("\n🎉 CONTINUATION BOT LAUNCHED SUCCESSFULLY!")
    else:
        print("\n❌ FAILED TO LAUNCH CONTINUATION BOT")
    
    print("=" * 60)

if __name__ == "__main__":
    main()