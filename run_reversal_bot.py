#!/usr/bin/env python3
"""
Simple script to run the reversal trading bot using LiveTradingOrchestrator
"""

import sys
import os
import psutil
import portalocker
sys.path.append('src')

from trading.live_trading.main import LiveTradingOrchestrator

def kill_duplicate_processes():
    """Kill any other Python processes running trading bots"""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)

    killed_count = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.pid == current_pid:
                continue

            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('run_reversal_bot.py' in arg or 'run_live_bot.py' in arg for arg in cmdline):
                    print(f"🔪 Killing duplicate bot process: PID {proc.pid}")
                    proc.kill()
                    killed_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if killed_count > 0:
        print(f"✅ Killed {killed_count} duplicate bot processes")

def acquire_singleton_lock():
    """Ensure only one instance of the bot runs"""
    try:
        lock_file = os.path.join(os.path.dirname(__file__), 'bot.lock')
        # Check if lock file exists and contains a running PID
        if os.path.exists(lock_file):
            try:
                with open(lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                if psutil.pid_exists(old_pid):
                    print(f"❌ Another instance is already running (PID: {old_pid})!")
                    sys.exit(1)
                else:
                    print(f"🧹 Removing stale lock file from dead process (PID: {old_pid})")
                    os.remove(lock_file)
            except (ValueError, psutil.NoSuchProcess):
                os.remove(lock_file)

        # Create new lock file with current PID
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        print("🔒 Singleton lock acquired")
        return lock_file
    except Exception as e:
        print(f"❌ Error acquiring lock: {e}")
        sys.exit(1)

def main():
    """Run the reversal trading bot"""
    print("🚀 Starting Reversal Trading Bot...")

    # Create orchestrator in reversal mode
    orchestrator = LiveTradingOrchestrator(reversal_mode=True)

    try:
        orchestrator.run()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        orchestrator.stop()
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
    finally:
        orchestrator.cleanup()

    print("✅ Bot shutdown complete")

if __name__ == "__main__":
    # Kill any duplicate processes first
    kill_duplicate_processes()

    # Acquire singleton lock to prevent multiple instances
    lock = acquire_singleton_lock()

    try:
        main()
    finally:
        # Release lock on exit
        try:
            if os.path.exists(lock):
                os.remove(lock)
        except:
            pass
