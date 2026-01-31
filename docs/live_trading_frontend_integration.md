# Live Trading Frontend Integration

## Overview

This document outlines the plan to integrate live trading functionality into the MA Stock Trader web interface. The goal is to provide web-based monitoring and control while maintaining the high-speed performance of the terminal-based bot.

## Priority: Speed Optimization

**CRITICAL**: The web interface must NOT impact trading speed. All performance optimizations prioritize:

- ✅ **Zero latency impact** on trading decisions
- ✅ **Background processing** - bot runs independently
- ✅ **Minimal overhead** - lightweight WebSocket streaming
- ✅ **Async operations** - non-blocking API calls

## Architecture

### Backend Components
- **Existing Bot**: `run_live_bot.py` runs as background process
- **New API Layer**: REST endpoints for control and monitoring
- **WebSocket Server**: Real-time log streaming
- **Process Manager**: Handles bot lifecycle

### Frontend Components
- **Live Trading Page**: New React page with controls and monitoring
- **WebSocket Client**: Receives real-time updates
- **API Client**: Sends control commands
- **State Management**: Tracks bot status and logs

## Implementation Plan

### Phase 1: Basic Infrastructure

#### 1.1 Add Navbar Tab
```typescript
// frontend/src/components/Navbar.tsx
const navItems = [
  { path: '/scanner', label: 'Scanner' },
  { path: '/market-breadth', label: 'Market Breadth' },
  { path: '/live-trading', label: 'Live Trading' },  // NEW
  // ... other items
];
```

#### 1.2 Create LiveTrading Page
```typescript
// frontend/src/pages/LiveTrading.tsx
const LiveTrading = () => {
  const [botStatus, setBotStatus] = useState<'stopped' | 'running'>('stopped');
  const [selectedMode, setSelectedMode] = useState<'continuation' | 'reversal'>('continuation');
  const [logs, setLogs] = useState<string[]>([]);

  // WebSocket connection for real-time logs
  // API calls for control
  // State management

  return (
    <div className="live-trading-container">
      <ModeSelector value={selectedMode} onChange={setSelectedMode} />
      <BotControls status={botStatus} onStart={handleStart} onStop={handleStop} />
      <LogDisplay logs={logs} />
    </div>
  );
};
```

### Phase 2: Backend API Endpoints

#### 2.1 REST API Endpoints
```python
# server.py - Add to existing Flask app

@app.route('/api/live-trading/start', methods=['POST'])
def start_live_trading():
    """Start live trading bot with specified mode"""
    data = request.get_json()
    mode = data.get('mode', 'continuation')  # 'continuation' or 'reversal'

    # Validate mode
    if mode not in ['continuation', 'reversal']:
        return jsonify({'error': 'Invalid mode'}), 400

    # Check if bot already running
    if is_bot_running():
        return jsonify({'error': 'Bot already running'}), 409

    # Start bot process
    try:
        start_bot_process(mode)
        return jsonify({'status': 'started', 'mode': mode})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-trading/stop', methods=['POST'])
def stop_live_trading():
    """Stop live trading bot"""
    try:
        stop_bot_process()
        return jsonify({'status': 'stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-trading/status')
def get_live_trading_status():
    """Get current bot status"""
    return jsonify({
        'running': is_bot_running(),
        'mode': get_current_mode(),
        'start_time': get_bot_start_time(),
        'active_stocks': get_active_stock_count()
    })

@app.route('/api/live-trading/validate-lists')
def validate_trading_lists():
    """Validate continuation and reversal lists"""
    from validate_trading_lists import TradingListValidator

    validator = TradingListValidator()
    # Capture output and return as JSON
    import io
    import sys
    from contextlib import redirect_stdout

    f = io.StringIO()
    with redirect_stdout(f):
        validator.print_results()

    output = f.getvalue()

    # Parse output into structured data
    return jsonify({
        'validation_output': output,
        'timestamp': datetime.now().isoformat()
    })
```

#### 2.2 WebSocket for Real-time Logs
```python
# server.py - Add WebSocket support

from flask_socketio import SocketIO, emit
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    """Client connected for live trading updates"""
    emit('status', {'message': 'Connected to live trading stream'})

@socketio.on('join_live_trading')
def handle_join_live_trading():
    """Client wants to receive live trading updates"""
    # Join room for live trading updates
    join_room('live_trading')

# Function to broadcast logs to connected clients
def broadcast_log(message: str):
    """Broadcast log message to all connected clients"""
    socketio.emit('log', {'message': message, 'timestamp': datetime.now().isoformat()}, room='live_trading')
```

#### 2.3 Process Management
```python
# live_trading_process.py - New module

import subprocess
import psutil
import os
from typing import Optional

class LiveTradingProcessManager:
    """Manages the live trading bot process"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.mode: Optional[str] = None

    def start_bot(self, mode: str) -> bool:
        """Start the live trading bot"""
        if self.is_running():
            return False

        try:
            # Start bot as subprocess
            cmd = ['python', 'run_live_bot.py', mode]
            self.process = subprocess.Popen(
                cmd,
                cwd=os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.mode = mode

            # Start log streaming thread
            import threading
            threading.Thread(target=self._stream_logs, daemon=True).start()

            return True
        except Exception as e:
            print(f"Failed to start bot: {e}")
            return False

    def stop_bot(self) -> bool:
        """Stop the live trading bot"""
        if not self.is_running():
            return False

        try:
            # Send SIGTERM to process group
            os.killpg(os.getpgid(self.process.pid), 15)
            self.process.wait(timeout=10)
            self.process = None
            self.mode = None
            return True
        except Exception as e:
            print(f"Failed to stop bot gracefully: {e}")
            # Force kill if needed
            try:
                self.process.kill()
                return True
            except:
                return False

    def is_running(self) -> bool:
        """Check if bot is running"""
        if self.process is None:
            return False

        return self.process.poll() is None

    def get_status(self) -> dict:
        """Get bot status"""
        return {
            'running': self.is_running(),
            'mode': self.mode,
            'pid': self.process.pid if self.process else None
        }

    def _stream_logs(self):
        """Stream logs from bot process to WebSocket"""
        if self.process and self.process.stdout:
            for line in iter(self.process.stdout.readline, ''):
                if line.strip():
                    # Send to WebSocket clients
                    broadcast_log(line.strip())

# Global instance
process_manager = LiveTradingProcessManager()
```

### Phase 3: Frontend Components

#### 3.1 LiveTrading Page Structure
```typescript
// frontend/src/pages/LiveTrading.tsx
import React, { useState, useEffect } from 'react';
import { io, Socket } from 'socket.io-client';

interface LogEntry {
  message: string;
  timestamp: string;
}

const LiveTrading: React.FC = () => {
  const [botStatus, setBotStatus] = useState<'stopped' | 'running'>('stopped');
  const [selectedMode, setSelectedMode] = useState<'continuation' | 'reversal'>('continuation');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [socket, setSocket] = useState<Socket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    newSocket.on('log', (data: LogEntry) => {
      setLogs(prev => [...prev.slice(-99), data]); // Keep last 100 logs
    });

    return () => {
      newSocket.close();
    };
  }, []);

  const handleStart = async () => {
    try {
      const response = await fetch('/api/live-trading/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: selectedMode })
      });

      if (response.ok) {
        setBotStatus('running');
        addLog('Bot started successfully');
      }
    } catch (error) {
      addLog(`Failed to start bot: ${error}`);
    }
  };

  const handleStop = async () => {
    try {
      const response = await fetch('/api/live-trading/stop', {
        method: 'POST'
      });

      if (response.ok) {
        setBotStatus('stopped');
        addLog('Bot stopped successfully');
      }
    } catch (error) {
      addLog(`Failed to stop bot: ${error}`);
    }
  };

  const handleValidateLists = async () => {
    try {
      const response = await fetch('/api/live-trading/validate-lists');
      const data = await response.json();

      // Display validation results
      addLog('=== LIST VALIDATION RESULTS ===');
      data.validation_output.split('\n').forEach((line: string) => {
        if (line.trim()) addLog(line);
      });
    } catch (error) {
      addLog(`Validation failed: ${error}`);
    }
  };

  const addLog = (message: string) => {
    const entry: LogEntry = {
      message,
      timestamp: new Date().toISOString()
    };
    setLogs(prev => [...prev.slice(-99), entry]);
  };

  return (
    <div className="live-trading-page">
      <div className="controls-section">
        <div className="mode-selector">
          <label>Trading Mode:</label>
          <select
            value={selectedMode}
            onChange={(e) => setSelectedMode(e.target.value as 'continuation' | 'reversal')}
            disabled={botStatus === 'running'}
          >
            <option value="continuation">Continuation Trading</option>
            <option value="reversal">Reversal Trading</option>
          </select>
        </div>

        <div className="bot-controls">
          <button
            onClick={handleStart}
            disabled={botStatus === 'running'}
            className="start-btn"
          >
            Start Bot
          </button>
          <button
            onClick={handleStop}
            disabled={botStatus === 'stopped'}
            className="stop-btn"
          >
            Stop Bot
          </button>
          <button onClick={handleValidateLists} className="validate-btn">
            Validate Lists
          </button>
        </div>

        <div className="status-indicator">
          Status: <span className={`status-${botStatus}`}>{botStatus.toUpperCase()}</span>
          {botStatus === 'running' && <span> ({selectedMode})</span>}
        </div>
      </div>

      <div className="logs-section">
        <h3>Live Trading Logs</h3>
        <div className="logs-container">
          {logs.map((log, index) => (
            <div key={index} className="log-entry">
              <span className="timestamp">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              <span className="message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default LiveTrading;
```

#### 3.2 CSS Styling
```css
/* frontend/src/pages/LiveTrading.css */
.live-trading-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.controls-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.mode-selector select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-left: 10px;
}

.bot-controls button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-right: 10px;
  font-weight: bold;
}

.start-btn {
  background: #28a745;
  color: white;
}

.start-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.stop-btn {
  background: #dc3545;
  color: white;
}

.validate-btn {
  background: #007bff;
  color: white;
}

.status-indicator {
  font-weight: bold;
}

.status-running {
  color: #28a745;
}

.status-stopped {
  color: #6c757d;
}

.logs-section {
  background: #000;
  color: #0f0;
  font-family: 'Courier New', monospace;
  padding: 20px;
  border-radius: 8px;
  height: 600px;
  overflow-y: auto;
}

.logs-section h3 {
  margin-top: 0;
  color: #0f0;
}

.log-entry {
  margin-bottom: 2px;
  font-size: 12px;
}

.timestamp {
  color: #888;
  margin-right: 10px;
}

.message {
  color: #0f0;
}
```

## Performance Considerations

### Speed Optimizations
1. **Background Processing**: Bot runs as separate process, frontend only monitors
2. **WebSocket Streaming**: Direct log streaming with minimal latency
3. **Lazy Loading**: Only load active components
4. **Debounced Updates**: Batch UI updates to prevent blocking

### Memory Management
1. **Log Rotation**: Keep only last 100 log entries in memory
2. **Process Cleanup**: Proper cleanup of background processes
3. **Connection Limits**: Limit concurrent WebSocket connections

## Testing Strategy

### Backend Testing
- Unit tests for API endpoints
- WebSocket connection tests
- Process management tests

### Frontend Testing
- Component rendering tests
- WebSocket connection tests
- API integration tests

### Integration Testing
- End-to-end bot control flow
- Real-time log streaming verification
- Performance impact assessment

## Future Enhancements

### Advanced Features (Post-MVP)
1. **Real-time Charts**: Live price charts for monitored stocks
2. **Performance Analytics**: P&L tracking, win rates
3. **Alert System**: Custom alerts for specific events
4. **Historical Logs**: Persisted log storage and retrieval

### Scalability Improvements
1. **Multi-bot Support**: Run multiple bots simultaneously
2. **Load Balancing**: Distribute monitoring across instances
3. **Database Integration**: Store logs and performance data

## Deployment Notes

### Environment Setup
- Ensure WebSocket support in production
- Configure proper CORS settings
- Set up process monitoring and auto-restart

### Security Considerations
- API authentication for bot control
- WebSocket origin validation
- Process isolation for bot execution

## Conclusion

This frontend integration maintains the high-speed performance of the terminal bot while providing convenient web-based monitoring and control. The phased approach ensures stability and allows for incremental feature addition based on user feedback and performance metrics.
