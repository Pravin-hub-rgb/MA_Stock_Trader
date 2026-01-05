"""
Data fetching utilities for MA Stock Trader
Handles data retrieval from various sources (yfinance, NSEpy)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import requests
from pathlib import Path
import io

from src.utils.cache_manager import cache_manager

logger = logging.getLogger(__name__)


class DataFetcher:
    """Handles data fetching from various sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_nse_stocks(self) -> List[Dict]:
        """
        Fetch complete NSE stock list
        Returns list of all NSE equities
        """
        try:
            # Download from NSE website
            url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(io.StringIO(response.text))
            
            # Filter for active equities only
            stocks = []
            for _, row in df.iterrows():
                if row[' SERIES'] == 'EQ':  # Equity series
                    stocks.append({
                        'symbol': row['SYMBOL'],
                        'name': row['NAME OF COMPANY'],
                        'series': row[' SERIES'],
                        'industry': row.get('INDUSTRY', 'Unknown'),
                        'market_cap': row.get('ISSUED CAPITAL', None)
                    })
            
            logger.info(f"Fetched {len(stocks)} NSE equities")
            return stocks
            
        except Exception as e:
            logger.error(f"Error fetching NSE stocks: {e}")
            return []
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        source: str = 'yfinance'
    ) -> pd.DataFrame:
        """
        Fetch historical data for given symbol
        Returns pandas DataFrame with OHLCV data
        """
        try:
            if source == 'yfinance':
                return self._fetch_yfinance_data(symbol, start_date, end_date)
            elif source == 'nsepy':
                return self._fetch_nsepy_data(symbol, start_date, end_date)
            else:
                raise ValueError(f"Unsupported data source: {source}")
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_yfinance_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from Yahoo Finance"""
        try:
            # Add .NS suffix for NSE stocks (only if not already present and not a US stock)
            if not symbol.endswith(('.NS', '.US', '.BE', '.BO', '.MC', '.SA')):
                ticker = f"{symbol}.NS"
            else:
                ticker = symbol
            
            logger.info(f"Fetching data for {ticker} from {start_date} to {end_date}")
            
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            # Debug: Print actual column structure
            logger.info(f"Raw data shape: {data.shape}")
            logger.info(f"Raw data columns: {list(data.columns)}")
            logger.info(f"Raw data column type: {type(data.columns)}")
            
            # Handle multi-index from yfinance
            if isinstance(data.columns, pd.MultiIndex):
                logger.info(f"MultiIndex detected with levels: {data.columns.levels}")
                logger.info(f"MultiIndex codes: {data.columns.codes}")
                # The structure is (OHLCV, Symbol), so we need to get OHLCV from level 0
                data.columns = data.columns.get_level_values(0)
                logger.info(f"After flattening columns: {list(data.columns)}")
            
            # Ensure we have the expected column names
            available_columns = list(data.columns)
            logger.info(f"Available columns after flattening: {available_columns}")
            
            # Map available columns to our expected format
            column_mapping = {
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            # Check if we have all required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in available_columns for col in required_columns):
                logger.warning(f"Missing required columns. Available: {available_columns}, Required: {required_columns}")
                return pd.DataFrame()
            
            # Rename columns to match our schema
            data = data.rename(columns=column_mapping)
            
            # Add missing adj_close column (use close as fallback)
            if 'adj_close' not in data.columns:
                data['adj_close'] = data['close']
            
            # Add VWAP calculation
            data['vwap'] = (data['high'] + data['low'] + data['close']) / 3
            
            # Reset index to make date a column
            data = data.reset_index()
            data['date'] = data['Date'].dt.date
            data = data.drop('Date', axis=1)
            
            logger.info(f"Fetched {len(data)} days of data for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching yfinance data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_nsepy_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch data from NSEpy (alternative source)"""
        try:
            from nsepy import get_history
            from datetime import datetime
            
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            data = get_history(symbol=symbol, start=start, end=end)
            
            if data.empty:
                logger.warning(f"No data found for {symbol} from NSEpy")
                return pd.DataFrame()
            
            # Convert to our format
            data = data.reset_index()
            data['date'] = data['Date'].dt.date
            data = data.drop('Date', axis=1)
            
            logger.info(f"Fetched {len(data)} days of data for {symbol} from NSEpy")
            return data
            
        except ImportError:
            logger.warning("NSEpy not available, falling back to yfinance")
            return self._fetch_yfinance_data(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Error fetching NSEpy data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_realtime_data(self, symbol: str) -> Dict:
        """
        Fetch real-time data for given symbol
        Returns current price information
        """
        try:
            # Add .NS suffix for NSE stocks (only if not already present and not a US stock)
            if not symbol.endswith(('.NS', '.US', '.BE', '.BO', '.MC', '.SA')):
                ticker = f"{symbol}.NS"
            else:
                ticker = symbol
            stock = yf.Ticker(ticker)
            
            info = stock.info
            hist = stock.history(period="1d")
            
            if hist.empty:
                return {}
            
            current_data = {
                'symbol': symbol,
                'current_price': hist['Close'].iloc[-1],
                'open_price': hist['Open'].iloc[-1],
                'high_price': hist['High'].iloc[-1],
                'low_price': hist['Low'].iloc[-1],
                'volume': hist['Volume'].iloc[-1],
                'prev_close': info.get('previousClose', 0),
                'day_change': hist['Close'].iloc[-1] - info.get('previousClose', 0),
                'day_change_percent': ((hist['Close'].iloc[-1] - info.get('previousClose', 0)) / info.get('previousClose', 1)) * 100
            }
            
            return current_data
            
        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {e}")
            return {}
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for given data
        Returns DataFrame with additional indicator columns
        """
        try:
            if data.empty:
                return data
            
            # Calculate 20-day moving average
            data['ma_20'] = data['close'].rolling(window=20).mean()
            
            # Calculate moving average angle (slope)
            data['ma_angle'] = self._calculate_ma_angle(data['ma_20'])
            
            # Calculate Average Daily Range (ADR)
            data['daily_range'] = data['high'] - data['low']
            data['adr'] = data['daily_range'].rolling(window=14).mean()
            # Calculate ADR as percentage of close price
            data['adr_percent'] = (data['adr'] / data['close']) * 100
            
            # Calculate price change
            data['price_change'] = data['close'].pct_change()
            data['price_change_5d'] = data['close'].pct_change(5)
            data['price_change_20d'] = data['close'].pct_change(20)
            
            # Calculate distance from 20-day high
            data['high_20d'] = data['high'].rolling(window=20).max()
            data['distance_from_high'] = (data['close'] - data['high_20d']) / data['high_20d']
            
            # Calculate distance from 20-day low
            data['low_20d'] = data['low'].rolling(window=20).min()
            data['distance_from_low'] = (data['close'] - data['low_20d']) / data['low_20d']
            
            return data
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return data
    
    def _calculate_ma_angle(self, ma_series: pd.Series) -> pd.Series:
        """Calculate moving average angle (slope)"""
        try:
            # Calculate angle using linear regression over last 5 points
            angles = []
            
            for i in range(len(ma_series)):
                if i < 4:  # Need at least 5 points
                    angles.append(0)
                    continue
                
                # Get last 5 points
                recent_ma = ma_series.iloc[i-4:i+1]
                
                # Calculate linear regression slope
                x = np.arange(5)
                y = recent_ma.values
                
                if np.isnan(y).any():
                    angles.append(0)
                    continue
                
                # Calculate slope
                slope = np.polyfit(x, y, 1)[0]
                
                # Convert to angle in degrees
                angle = np.degrees(np.arctan(slope))
                angles.append(angle)
            
            return pd.Series(angles, index=ma_series.index)
            
        except Exception as e:
            logger.error(f"Error calculating MA angle: {e}")
            return pd.Series([0] * len(ma_series), index=ma_series.index)
    
    def detect_volume_surge(self, data: pd.DataFrame, threshold: float = 1.5) -> bool:
        """
        Detect volume surge in recent data
        Returns True if volume surge detected
        """
        try:
            if len(data) < 20:
                return False
            
            recent_volume = data['volume'].iloc[-1]
            volume_ma = data['volume_ma'].iloc[-1]
            
            return recent_volume > (volume_ma * threshold)
            
        except Exception as e:
            logger.error(f"Error detecting volume surge: {e}")
            return False
    
    def get_latest_data(self, symbol: str, days: int = 1) -> Dict:
        """
        Get latest market data for a symbol
        Returns dictionary with current market information
        """
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            data = self.fetch_historical_data(symbol, start_date, end_date)
            
            if data.empty:
                return {}
            
            latest = data.iloc[-1]
            
            return {
                'symbol': symbol,
                'date': latest['date'],
                'open': latest['open'],
                'high': latest['high'],
                'low': latest['low'],
                'close': latest['close'],
                'volume': latest['volume'],
                'vwap': latest.get('vwap', 0),
                'ma_20': latest.get('ma_20', 0),
                'ma_angle': latest.get('ma_angle', 0),
                'adr': latest.get('adr', 0),
                'adr_percent': latest.get('adr_percent', 0),
                'distance_from_high': latest.get('distance_from_high', 0),
                'distance_from_low': latest.get('distance_from_low', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting latest data for {symbol}: {e}")
            return {}
    
    def get_data_for_date_range(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Get data for specific date range from cache
        Returns DataFrame with OHLCV data
        """
        try:
            return cache_manager.get_data_for_date_range(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Error getting cached data for {symbol}: {e}")
            return pd.DataFrame()

    def prepare_market_data(self, days_back: int = 30, max_stocks: int = 500) -> Dict[str, int]:
        """
        Prepare market data by downloading and caching recent data for NSE stocks
        Returns summary of update operations
        """
        try:
            logger.info(f"Starting market data preparation for last {days_back} days")

            # Get NSE stocks list
            nse_stocks = self.fetch_nse_stocks()
            if not nse_stocks:
                logger.error("Failed to fetch NSE stocks list")
                return {'error': 'Failed to fetch NSE stocks'}

            # Limit number of stocks to process
            stocks_to_process = nse_stocks[:max_stocks]
            logger.info(f"Processing {len(stocks_to_process)} stocks (limited from {len(nse_stocks)})")

            summary = {
                'total_stocks': len(stocks_to_process),
                'updated': 0,
                'skipped': 0,
                'errors': 0,
                'total_days_added': 0
            }

            # Process each stock
            for i, stock in enumerate(stocks_to_process):
                try:
                    symbol = stock['symbol']

                    if (i + 1) % 50 == 0:
                        logger.info(f"Processed {i + 1}/{len(stocks_to_process)} stocks - Updated: {summary['updated']}, Errors: {summary['errors']}")

                    # Check if stock needs update
                    if not cache_manager.needs_update(symbol, days_back=3):
                        summary['skipped'] += 1
                        continue

                    # Fetch recent data
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

                    data = self.fetch_historical_data(symbol, start_date, end_date)
                    if data.empty:
                        summary['errors'] += 1
                        continue

                    # Update cache
                    cache_manager.update_cache(symbol, data)
                    summary['updated'] += 1
                    summary['total_days_added'] += len(data)

                except Exception as e:
                    logger.error(f"Error preparing data for {stock['symbol']}: {e}")
                    summary['errors'] += 1
                    continue

            logger.info(f"Market data preparation completed: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Error in market data preparation: {e}")
            return {'error': str(e)}


# Global data fetcher instance
data_fetcher = DataFetcher()
