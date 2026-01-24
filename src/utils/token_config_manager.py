#!/usr/bin/env python3
"""
Token Configuration Manager for MA Stock Trader
Handles real-time monitoring and management of upstox_config.json
"""

import json
import os
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

class TokenConfigManager:
    """Manages upstox_config.json with real-time file monitoring"""
    
    def __init__(self, config_file: str = 'upstox_config.json'):
        self.config_file = config_file
        self._config_cache = {}
        self._last_modified = 0
        self._lock = threading.RLock()
        self._watcher_thread = None
        self._stop_watching = threading.Event()
        
        # Load initial config
        self._load_config()
        
        # Start file watcher
        self._start_file_watcher()
    
    def _load_config(self) -> Dict:
        """Load config from file with thread safety"""
        with self._lock:
            try:
                if os.path.exists(self.config_file):
                    stat = os.stat(self.config_file)
                    current_modified = stat.st_mtime
                    
                    # Only reload if file has changed
                    if current_modified != self._last_modified:
                        with open(self.config_file, 'r') as f:
                            self._config_cache = json.load(f)
                            self._last_modified = current_modified
                            logger.info(f"Config reloaded from {self.config_file}")
                
                return self._config_cache.copy()
                
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return {}
    
    def get_config(self) -> Dict:
        """Get current config (with automatic reload if file changed)"""
        return self._load_config()
    
    def get_token(self) -> Optional[str]:
        """Get current access token"""
        config = self.get_config()
        return config.get('access_token')
    
    def get_api_credentials(self) -> Dict:
        """Get all API credentials"""
        config = self.get_config()
        return {
            'api_key': config.get('api_key'),
            'access_token': config.get('access_token'),
            'api_secret': config.get('api_secret')
        }
    
    def update_token(self, token: str) -> bool:
        """Update access token in config file"""
        try:
            with self._lock:
                # Load current config
                config = self.get_config()
                
                # Update token
                config['access_token'] = token
                
                # Save config
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                # Update cache and timestamp
                self._config_cache = config
                self._last_modified = os.stat(self.config_file).st_mtime
                
                logger.info("Access token updated in config file")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update token: {e}")
            return False
    
    def _start_file_watcher(self):
        """Start background thread to monitor config file changes"""
        if self._watcher_thread is None or not self._watcher_thread.is_alive():
            self._stop_watching.clear()
            self._watcher_thread = threading.Thread(target=self._watch_file_changes, daemon=True)
            self._watcher_thread.start()
            logger.info("Config file watcher started")
    
    def _watch_file_changes(self):
        """Monitor config file for changes"""
        while not self._stop_watching.is_set():
            try:
                if os.path.exists(self.config_file):
                    current_modified = os.stat(self.config_file).st_mtime
                    if current_modified != self._last_modified:
                        # File changed, reload config
                        self._load_config()
                
                # Check every 2 seconds
                self._stop_watching.wait(2)
                
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                self._stop_watching.wait(5)  # Wait longer on error
    
    def stop_watcher(self):
        """Stop the file watcher"""
        if self._watcher_thread and self._watcher_thread.is_alive():
            self._stop_watching.set()
            self._watcher_thread.join(timeout=2)
            logger.info("Config file watcher stopped")
    
    def is_valid_config(self) -> bool:
        """Check if config has valid credentials"""
        config = self.get_config()
        return all([
            config.get('api_key'),
            config.get('access_token'),
            config.get('api_secret')
        ])
    
    def get_status(self) -> Dict:
        """Get current config status"""
        config = self.get_config()
        token = config.get('access_token')
        
        return {
            'token': token,  # Return real token
            'exists': bool(token),
            'has_api_key': bool(config.get('api_key')),
            'has_api_secret': bool(config.get('api_secret')),
            'token_length': len(token) if token else 0,
            'masked_token': f"{'*' * 10}...{token[-4:]}" if token else None,
            'last_modified': datetime.fromtimestamp(self._last_modified).isoformat() if self._last_modified else None,
            'is_valid': self.is_valid_config()
        }

# Global instance
token_config_manager = TokenConfigManager()