# MA Stock Trader - Technical Specifications

## Overview

This document provides detailed technical specifications for implementing the MA Stock Trader system, including database schema, API specifications, and implementation details.

## Database Schema

### SQLite Database Structure

```sql
-- Stocks table
CREATE TABLE stocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    sector TEXT,
    industry TEXT,
    market_cap REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily price data
CREATE TABLE daily_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    vwap REAL,
    FOREIGN KEY (stock_id) REFERENCES stocks (id),
    UNIQUE(stock_id, date)
);

-- 20-day moving average
CREATE TABLE moving_averages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER,
    date DATE NOT NULL,
    ma_20 REAL,
    ma_angle REAL,
    FOREIGN KEY (stock_id) REFERENCES stocks (id),
    UNIQUE(stock_id, date)
);

-- Scan results
CREATE TABLE scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_type TEXT NOT NULL, -- 'continuation' or 'reversal'
    scan_date DATE NOT NULL,
    stock_id INTEGER,
    score REAL,
    notes TEXT,
    FOREIGN KEY (stock_id) REFERENCES stocks (id)
);

-- Watchlists
CREATE TABLE watchlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'continuation_candidates', 'reversal_candidates', 'next_day_trades'
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlist items
CREATE TABLE watchlist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER,
    stock_id INTEGER,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_source TEXT,
    manual_notes TEXT,
    FOREIGN KEY (watchlist_id) REFERENCES watchlists (id),
    FOREIGN KEY (stock_id) REFERENCES stocks (id)
);

-- Trades
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_id INTEGER,
    entry_date DATE NOT NULL,
    exit_date DATE,
    entry_price REAL,
    exit_price REAL,
    quantity INTEGER,
    position_type TEXT, -- 'continuation' or 'reversal'
    entry_reason TEXT,
    exit_reason TEXT,
    pnl REAL,
    pnl_percent REAL,
    risk_percent REAL,
    FOREIGN KEY (stock_id) REFERENCES stocks (id)
);

-- Configuration
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT
);
```

## API Specifications

### Scanner API

#### 1. Run Continuation Scan
```python
def run_continuation_scan(date: str = None) -> List[ScanResult]:
    """
    Run continuation scan for given date (default: today)
    Returns list of potential continuation candidates
    """
    pass

# Scan parameters
continuation_params = {
    'max_distance_from_high': 0.05,  # 5% from 1-month high
    'min_ma_angle': 0.0,             # Rising 20MA
    'min_volume_days': 1,            # At least 1 day with 1M+ volume
    'volume_threshold': 1000000,     # 1M shares
    'min_adr': 0.03,                 # 3% ADR
    'price_min': 100,                # ₹100 minimum
    'price_max': 2000,               # ₹2000 maximum
    'consolidation_days': (3, 7)     # 3-7 days consolidation
}
```

#### 2. Run Reversal Scan
```python
def run_reversal_scan(date: str = None) -> List[ScanResult]:
    """
    Run reversal scan for given date (default: today)
    Returns list of potential reversal candidates
    """
    pass

# Scan parameters
reversal_params = {
    'decline_days': (4, 7),          # 4-7 days decline
    'min_decline_percent': 0.10,     # 10% minimum decline
    'min_volume_days': 1,            # At least 1 day with 1M+ volume
    'volume_threshold': 1000000,     # 1M shares
    'min_adr': 0.03,                 # 3% ADR
    'price_min': 100,                # ₹100 minimum
    'price_max': 2000,               # ₹2000 maximum
}
```

#### 3. Calculate Technical Indicators
```python
def calculate_moving_average(stock_id: int, period: int = 20) -> List[MAData]:
    """
    Calculate moving average for given stock and period
    Returns list of MA values with dates
    """
    pass

def calculate_adr(stock_id: int, period: int = 20) -> float:
    """
    Calculate Average Daily Range for given stock
    Returns ADR percentage
    """
    pass

def detect_cup_pattern(stock_id: int, days: int = 30) -> bool:
    """
    Detect cup pattern formation
    Returns True if cup pattern detected
    """
    pass
```

### Trading API

#### 1. Position Sizing
```python
def calculate_position_size(
    account_size: float,
    risk_percent: float,
    entry_price: float,
    stop_loss_price: float
) -> int:
    """
    Calculate position size based on risk management
    Returns number of shares to buy
    """
    risk_amount = account_size * (risk_percent / 100)
    risk_per_share = abs(entry_price - stop_loss_price)
    shares = risk_amount / risk_per_share
    return int(shares)
```

#### 2. Strong Start Detection
```python
def detect_strong_start(symbol: str, timeframe: str = '3m') -> bool:
    """
    Detect strong start pattern
    Returns True if strong start detected
    """
    pass

# Strong start criteria
strong_start_criteria = {
    'open_equals_low_tolerance': 0.01,  # 1% tolerance
    'confirmation_time': 3,             # 3 minutes
    'volume_threshold': 0.25            # 25% of daily volume
}
```

#### 3. Gap Analysis
```python
def analyze_gap(symbol: str) -> GapAnalysis:
    """
    Analyze gap up/down for given symbol
    Returns gap analysis results
    """
    pass

# Gap analysis criteria
gap_criteria = {
    'gap_up_threshold': 0.02,    # 2% gap up
    'gap_down_threshold': 0.02,  # 2% gap down
    'confirmation_time': 5       # 5 minutes
}
```

## Implementation Details

### Data Fetching Module

#### 1. NSE Stock List
```python
def fetch_nse_stocks() -> List[StockInfo]:
    """
    Fetch complete NSE stock list
    Returns list of all NSE equities
    """
    # Download from NSE website
    # Filter for active equities only
    # Update monthly
    pass
```

#### 2. Historical Data
```python
def fetch_historical_data(
    symbol: str,
    start_date: str,
    end_date: str,
    source: str = 'yfinance'
) -> pd.DataFrame:
    """
    Fetch historical data for given symbol
    Returns pandas DataFrame with OHLCV data
    """
    pass
```

#### 3. Real-time Data
```python
def connect_websocket(symbol: str) -> WebSocket:
    """
    Connect to real-time data WebSocket
    Returns WebSocket connection object
    """
    pass
```

### Chart Analysis Module

#### 1. Pattern Recognition
```python
def detect_range_formation(data: pd.DataFrame, days: int = 5) -> RangeFormation:
    """
    Detect range formation in price data
    Returns range formation details
    """
    pass

def detect_cup_pattern(data: pd.DataFrame) -> CupPattern:
    """
    Detect cup pattern formation
    Returns cup pattern details
    """
    pass

def calculate_ma_angle(data: pd.DataFrame, period: int = 20) -> float:
    """
    Calculate moving average angle
    Returns angle in degrees
    """
    pass
```

#### 2. Volume Analysis
```python
def analyze_volume_profile(data: pd.DataFrame) -> VolumeProfile:
    """
    Analyze volume profile for given data
    Returns volume analysis results
    """
    pass

def detect_volume_surge(data: pd.DataFrame, threshold: float = 1.5) -> bool:
    """
    Detect volume surge in recent data
    Returns True if volume surge detected
    """
    pass
```

### Risk Management Module

#### 1. Position Sizing
```python
class PositionSizer:
    def __init__(self, account_size: float, risk_per_trade: float = 0.005):
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
    
    def calculate_size(
        self,
        entry_price: float,
        stop_loss: float,
        max_risk_percent: float = None
    ) -> int:
        """
        Calculate position size for trade
        Returns number of shares
        """
        if max_risk_percent is None:
            max_risk_percent = self.risk_per_trade
        
        risk_amount = self.account_size * max_risk_percent
        risk_per_share = abs(entry_price - stop_loss)
        shares = risk_amount / risk_per_share
        return int(shares)
```

#### 2. Drawdown Management
```python
class DrawdownManager:
    def __init__(self, max_drawdown: float = 0.05):
        self.max_drawdown = max_drawdown
        self.starting_balance = 0
        self.current_balance = 0
    
    def should_stop_trading(self) -> bool:
        """
        Check if trading should be stopped due to drawdown
        Returns True if trading should stop
        """
        if self.starting_balance == 0:
            return False
        
        drawdown_percent = (self.starting_balance - self.current_balance) / self.starting_balance
        return drawdown_percent >= self.max_drawdown
```

## Configuration System

### Settings Management
```python
class Settings:
    def __init__(self):
        self.base_filters = {
            'min_volume': 1000000,
            'price_min': 100,
            'price_max': 2000,
            'min_adr': 0.03
        }
        
        self.scan_params = {
            'continuation': {
                'max_distance_from_high': 0.05,
                'min_ma_angle': 0.0,
                'consolidation_days': (3, 7)
            },
            'reversal': {
                'decline_days': (4, 7),
                'min_decline_percent': 0.10
            }
        }
        
        self.trading_rules = {
            'risk_per_trade': 0.005,
            'max_drawdown': 0.05,
            'profit_target': 0.15,
            'time_exit_days': 3
        }
    
    def save(self):
        """Save settings to database"""
        pass
    
    def load(self):
        """Load settings from database"""
        pass
```

## Error Handling and Logging

### Error Handling Strategy
```python
class TradingError(Exception):
    """Base exception for trading operations"""
    pass

class DataError(TradingError):
    """Error related to data fetching or processing"""
    pass

class ExecutionError(TradingError):
    """Error related to order execution"""
    pass

class RiskError(TradingError):
    """Error related to risk management"""
    pass
```

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MA_Stock_Trader')
```

## Testing Framework

### Unit Tests
```python
import unittest
from unittest.mock import Mock, patch

class TestScanner(unittest.TestCase):
    def test_continuation_scan(self):
        """Test continuation scan functionality"""
        pass
    
    def test_reversal_scan(self):
        """Test reversal scan functionality"""
        pass

class TestTradingAPI(unittest.TestCase):
    def test_position_sizing(self):
        """Test position sizing calculations"""
        pass
    
    def test_strong_start_detection(self):
        """Test strong start detection"""
        pass

class TestRiskManagement(unittest.TestCase):
    def test_drawdown_management(self):
        """Test drawdown management"""
        pass
```

### Integration Tests
```python
class TestSystemIntegration(unittest.TestCase):
    def test_full_scan_workflow(self):
        """Test complete scan workflow"""
        pass
    
    def test_trading_workflow(self):
        """Test complete trading workflow"""
        pass
```

This technical specification provides the foundation for implementing the MA Stock Trader system with proper database design, API specifications, and implementation details.
