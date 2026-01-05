"""
Database utilities for MA Stock Trader
Handles SQLite database operations and schema management
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "data/stocks.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Stocks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT UNIQUE NOT NULL,
                        name TEXT,
                        sector TEXT,
                        industry TEXT,
                        market_cap REAL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Daily price data
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_data (
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
                    )
                """)
                
                # 20-day moving average
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS moving_averages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_id INTEGER,
                        date DATE NOT NULL,
                        ma_20 REAL,
                        ma_angle REAL,
                        FOREIGN KEY (stock_id) REFERENCES stocks (id),
                        UNIQUE(stock_id, date)
                    )
                """)
                
                # Scan results
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scan_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        scan_type TEXT NOT NULL,
                        scan_date DATE NOT NULL,
                        stock_id INTEGER,
                        score REAL,
                        notes TEXT,
                        FOREIGN KEY (stock_id) REFERENCES stocks (id)
                    )
                """)
                
                # Watchlists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS watchlists (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Watchlist items
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS watchlist_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        watchlist_id INTEGER,
                        stock_id INTEGER,
                        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        scan_source TEXT,
                        manual_notes TEXT,
                        FOREIGN KEY (watchlist_id) REFERENCES watchlists (id),
                        FOREIGN KEY (stock_id) REFERENCES stocks (id)
                    )
                """)
                
                # Trades
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        stock_id INTEGER,
                        entry_date DATE NOT NULL,
                        exit_date DATE,
                        entry_price REAL,
                        exit_price REAL,
                        quantity INTEGER,
                        position_type TEXT,
                        entry_reason TEXT,
                        exit_reason TEXT,
                        pnl REAL,
                        pnl_percent REAL,
                        risk_percent REAL,
                        FOREIGN KEY (stock_id) REFERENCES stocks (id)
                    )
                """)
                
                # Configuration
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        description TEXT
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def insert_stock(self, symbol: str, name: str = None, sector: str = None, 
                    industry: str = None, market_cap: float = None) -> int:
        """Insert or update stock information"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO stocks (symbol, name, sector, industry, market_cap, last_updated)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (symbol, name, sector, industry, market_cap))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error inserting stock {symbol}: {e}")
            raise
    
    def insert_daily_data(self, stock_id: int, date: date, open_price: float,
                         high: float, low: float, close: float, volume: int, vwap: float = None):
        """Insert daily price data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_data 
                    (stock_id, date, open, high, low, close, volume, vwap)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (stock_id, date, open_price, high, low, close, volume, vwap))
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting daily data for stock {stock_id}: {e}")
            raise
    
    def insert_moving_average(self, stock_id: int, date: date, ma_20: float, ma_angle: float):
        """Insert moving average data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO moving_averages (stock_id, date, ma_20, ma_angle)
                    VALUES (?, ?, ?, ?)
                """, (stock_id, date, ma_20, ma_angle))
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting moving average for stock {stock_id}: {e}")
            raise
    
    def insert_scan_result(self, scan_type: str, scan_date: date, stock_id: int,
                          score: float = None, notes: str = None):
        """Insert scan result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO scan_results (scan_type, scan_date, stock_id, score, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (scan_type, scan_date, stock_id, score, notes))
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting scan result: {e}")
            raise
    
    def get_stock_id(self, symbol: str) -> Optional[int]:
        """Get stock ID by symbol"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM stocks WHERE symbol = ?", (symbol,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting stock ID for {symbol}: {e}")
            return None
    
    def get_daily_data(self, stock_id: int, days: int = 200) -> List[Dict]:
        """Get daily price data for a stock"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, open, high, low, close, volume, vwap
                    FROM daily_data 
                    WHERE stock_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                """, (stock_id, days))
                
                columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'vwap']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting daily data for stock {stock_id}: {e}")
            return []
    
    def get_moving_averages(self, stock_id: int, days: int = 200) -> List[Dict]:
        """Get moving average data for a stock"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, ma_20, ma_angle
                    FROM moving_averages 
                    WHERE stock_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                """, (stock_id, days))
                
                columns = ['date', 'ma_20', 'ma_angle']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting moving averages for stock {stock_id}: {e}")
            return []
    
    def get_scan_results(self, scan_type: str = None, days: int = 30) -> List[Dict]:
        """Get scan results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT sr.scan_type, sr.scan_date, s.symbol, s.name, sr.score, sr.notes
                    FROM scan_results sr
                    JOIN stocks s ON sr.stock_id = s.id
                    WHERE sr.scan_date >= date('now', '-{} days')
                """.format(days)
                
                params = []
                if scan_type:
                    query += " AND sr.scan_type = ?"
                    params.append(scan_type)
                
                query += " ORDER BY sr.scan_date DESC, sr.score DESC"
                
                cursor.execute(query, params)
                
                columns = ['scan_type', 'scan_date', 'symbol', 'name', 'score', 'notes']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting scan results: {e}")
            return []
    
    def create_watchlist(self, name: str, watchlist_type: str) -> int:
        """Create a new watchlist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO watchlists (name, type)
                    VALUES (?, ?)
                """, (name, watchlist_type))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating watchlist {name}: {e}")
            raise
    
    def add_to_watchlist(self, watchlist_id: int, stock_id: int, 
                        scan_source: str = None, manual_notes: str = None):
        """Add stock to watchlist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO watchlist_items (watchlist_id, stock_id, scan_source, manual_notes)
                    VALUES (?, ?, ?, ?)
                """, (watchlist_id, stock_id, scan_source, manual_notes))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding stock to watchlist: {e}")
            raise
    
    def get_watchlist(self, watchlist_id: int) -> List[Dict]:
        """Get watchlist items"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.symbol, s.name, s.sector, w.scan_source, w.manual_notes, w.added_date
                    FROM watchlist_items w
                    JOIN stocks s ON w.stock_id = s.id
                    WHERE w.watchlist_id = ?
                    ORDER BY w.added_date DESC
                """, (watchlist_id,))
                
                columns = ['symbol', 'name', 'sector', 'scan_source', 'manual_notes', 'added_date']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting watchlist {watchlist_id}: {e}")
            return []
    
    def get_watchlists(self) -> List[Dict]:
        """Get all watchlists"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, type, created_date, last_updated
                    FROM watchlists
                    ORDER BY created_date DESC
                """)
                
                columns = ['id', 'name', 'type', 'created_date', 'last_updated']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting watchlists: {e}")
            return []
    
    def save_config(self, key: str, value: str, description: str = None):
        """Save configuration value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO config (key, value, description)
                    VALUES (?, ?, ?)
                """, (key, value, description))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving config {key}: {e}")
            raise
    
    def load_config(self, key: str, default: str = None) -> Optional[str]:
        """Load configuration value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result[0] if result else default
        except Exception as e:
            logger.error(f"Error loading config {key}: {e}")
            return default
    
    def close(self):
        """Close database connection"""
        pass  # SQLite connections are managed automatically


# Global database instance
db = DatabaseManager()
