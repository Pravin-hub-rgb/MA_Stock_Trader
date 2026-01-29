# NSE Bhavcopy Integration for Latest Data

## Overview
Bhavcopy is NSE's official end-of-day data file containing complete trading data for all stocks. It's the authoritative source for same-day EOD data and is available after market close (typically by 6 PM IST).

## Why Bhavcopy?
- **Official Source**: Directly from NSE, most accurate
- **Complete Coverage**: All stocks, all data points
- **Same-Day Data**: Get today's data after market close
- **Free & Reliable**: No API limits, always available
- **Backup Source**: Works when Upstox has gaps

## Current Problem
Upstox API provides historical data but may not have the most recent trading day's data immediately. For example:
- Today: Jan 7, 2026
- Upstox latest: Jan 6, 2026 (yesterday)
- Need bhavcopy to get Jan 7 data after market close

## Integration Strategy
1. **Upstox for History**: Bulk historical data (past months)
2. **Bhavcopy for Today**: Latest trading day data
3. **Hybrid Cache**: Combine both sources seamlessly

## Bhavcopy File Structure

### File Format
- **Name**: `cmDDMMYYYYbhav.csv.zip` (e.g., `cm07JAN2026bhav.csv.zip`)
- **Location**: `https://archives.nseindia.com/content/historical/EQUITIES/YYYY/MMM/cmDDMMMYYYYbhav.csv.zip`
- **Size**: ~50MB uncompressed, ~5MB compressed

### Data Columns
```csv
SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY,TOTTRDVAL,TIMESTAMP,TOTALTRADES,ISIN
20MICRONS,EQ,195.35,197.85,194.20,195.80,195.80,194.53,56691,11000000,07-JAN-2026,1234,INE002A01018
```

**Key Columns:**
- `SYMBOL`: Stock symbol (e.g., "20MICRONS")
- `SERIES`: EQ for equity
- `OPEN/HIGH/LOW/CLOSE`: OHLC prices
- `TOTTRDQTY`: Volume
- `TIMESTAMP`: Date
- `ISIN`: International Security ID

## Implementation Code

### 1. Bhavcopy Fetcher Class

```python
#!/usr/bin/env python3
"""
NSE Bhavcopy Fetcher for MA Stock Trader
Handles same-day EOD data from NSE bhavcopy files
"""

import os
import logging
import requests
import pandas as pd
import zipfile
import io
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class NSEBhavcopyFetcher:
    """Fetches and processes NSE bhavcopy data"""

    def __init__(self, cache_dir: str = "bhavcopy_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_bhavcopy_url(self, target_date: date) -> str:
        """Generate bhavcopy URL for specific date"""
        date_str = target_date.strftime('%d%b%Y').upper()
        month_str = target_date.strftime('%b').upper()
        year_str = target_date.strftime('%Y')

        url = f"https://archives.nseindia.com/content/historical/EQUITIES/{year_str}/{month_str}/cm{date_str}bhav.csv.zip"
        return url

    def download_bhavcopy(self, target_date: date) -> Optional[pd.DataFrame]:
        """
        Download and parse bhavcopy for specific date
        Returns DataFrame with all stock data or None if not available
        """
        try:
            url = self.get_bhavcopy_url(target_date)
            date_str = target_date.strftime('%Y-%m-%d')

            logger.info(f"Downloading bhavcopy for {date_str}...")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Extract ZIP content
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                # Get the CSV file (usually named cmDDMMMYYYYbhav.csv)
                csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
                if not csv_files:
                    logger.error(f"No CSV file found in bhavcopy ZIP for {date_str}")
                    return None

                csv_file = csv_files[0]

                # Read CSV directly from ZIP
                with zf.open(csv_file) as f:
                    df = pd.read_csv(f, encoding='cp1252')  # NSE uses Windows-1252 encoding

            # Filter for equity series only
            df = df[df['SERIES'] == 'EQ']

            # Clean column names
            df.columns = df.columns.str.lower()

            # Add date column
            df['date'] = target_date

            # Rename columns to match our schema
            column_mapping = {
                'symbol': 'symbol',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'tottrdqty': 'volume',
                'tottrdval': 'value',
                'totaltrades': 'trades',
                'timestamp': 'date',
                'isin': 'isin'
            }

            df = df.rename(columns=column_mapping)

            # Select only required columns
            df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]

            # Convert data types
            df['volume'] = df['volume'].astype(int)
            df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

            logger.info(f"Successfully downloaded bhavcopy for {date_str}: {len(df)} stocks")
            return df

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Bhavcopy not yet available for {target_date.strftime('%Y-%m-%d')} (market may still be open)")
            else:
                logger.error(f"HTTP error downloading bhavcopy: {e}")
        except Exception as e:
            logger.error(f"Error downloading bhavcopy for {target_date.strftime('%Y-%m-%d')}: {e}")

        return None

    def get_latest_bhavcopy(self) -> Optional[pd.DataFrame]:
        """
        Get the latest available bhavcopy (usually yesterday or today after market close)
        Returns DataFrame with latest EOD data
        """
        # Try today first, then yesterday
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Try today first (if market closed)
        df = self.download_bhavcopy(today)
        if df is not None:
            return df

        # Fallback to yesterday
        df = self.download_bhavcopy(yesterday)
        if df is not None:
            logger.info("Using yesterday's bhavcopy (today's not available yet)")
            return df

        logger.warning("No bhavcopy available for today or yesterday")
        return None

    def get_stock_from_bhavcopy(self, symbol: str, bhavcopy_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract specific stock data from bhavcopy DataFrame
        Returns formatted DataFrame for cache storage
        """
        try:
            # Find the stock (case insensitive)
            stock_data = bhavcopy_df[bhavcopy_df['symbol'].str.upper() == symbol.upper()]

            if stock_data.empty:
                logger.warning(f"Stock {symbol} not found in bhavcopy")
                return pd.DataFrame()

            # Get the row (should be only one)
            row = stock_data.iloc[0]

            # Create DataFrame in our standard format
            df = pd.DataFrame([{
                'date': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }])

            # Set date as index
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error extracting {symbol} from bhavcopy: {e}")
            return pd.DataFrame()

# Global instance
nse_bhavcopy_fetcher = NSEBhavcopyFetcher()
```

### 2. Cache Manager Updates

```python
def update_with_bhavcopy(self, symbol: str, bhavcopy_data: pd.DataFrame):
    """Update existing cache with latest bhavcopy data"""
    existing_data = self.load_cached_data(symbol)

    if existing_data is not None:
        # Combine existing with new data
        combined = pd.concat([existing_data, bhavcopy_data])
        # Remove duplicates and sort
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
    else:
        combined = bhavcopy_data

    # Add technical indicators
    from src.utils.data_fetcher import data_fetcher
    combined = data_fetcher.calculate_technical_indicators(combined)

    # Save updated cache
    self.save_cached_data(symbol, combined)
    logger.info(f"Updated {symbol} cache with bhavcopy data: {len(combined)} total days")
```

### 3. Daily Update Script

```python
#!/usr/bin/env python3
"""
Daily bhavcopy update script
Run after market close (6 PM+) to get latest data
"""

import logging
from datetime import datetime
from src.utils.nse_fetcher import nse_bhavcopy_fetcher
from src.utils.cache_manager import cache_manager

logging.basicConfig(level=logging.INFO)

def update_all_stocks_with_bhavcopy():
    """Update all cached stocks with latest bhavcopy data"""
    print("Starting daily bhavcopy update...")

    # Get latest bhavcopy
    bhavcopy_df = nse_bhavcopy_fetcher.get_latest_bhavcopy()

    if bhavcopy_df is None:
        print("❌ No bhavcopy available")
        return

    print(f"📊 Downloaded bhavcopy with {len(bhavcopy_df)} stocks")

    # Get list of cached stocks
    import os
    cache_dir = "data/cache"
    cached_symbols = []

    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            if file.endswith('.pkl'):
                symbol = file.replace('.pkl', '')
                cached_symbols.append(symbol)

    print(f"📁 Found {len(cached_symbols)} cached stocks")

    # Update each cached stock
    updated = 0
    for symbol in cached_symbols:
        try:
            stock_data = nse_bhavcopy_fetcher.get_stock_from_bhavcopy(symbol, bhavcopy_df)
            if not stock_data.empty:
                cache_manager.update_with_bhavcopy(symbol, stock_data)
                updated += 1
                if updated % 10 == 0:
                    print(f"Updated {updated}/{len(cached_symbols)} stocks...")
        except Exception as e:
            print(f"❌ Error updating {symbol}: {e}")

    print(f"✅ Updated {updated} stocks with latest bhavcopy data")

if __name__ == "__main__":
    update_all_stocks_with_bhavcopy()
```

### 4. Integration with Data Fetcher

```python
def update_daily_bhavcopy(self) -> Dict[str, int]:
    """
    Update cache with latest bhavcopy data (same-day EOD)
    Call this after 6 PM to get today's complete data
    """
    try:
        logger.info("Updating daily bhavcopy data...")

        # Get latest bhavcopy
        bhavcopy_df = nse_bhavcopy_fetcher.get_latest_bhavcopy()

        if bhavcopy_df.empty:
            return {'error': 'No bhavcopy data available'}

        summary = {
            'total_stocks': len(bhavcopy_df['symbol'].unique()),
            'updated': 0,
            'errors': 0
        }

        # Update each stock's cache with today's data
        for symbol in bhavcopy_df['symbol'].unique():
            try:
                stock_data = nse_bhavcopy_fetcher.get_stock_from_bhavcopy(symbol, bhavcopy_df)
                if not stock_data.empty:
                    # Update existing cache
                    cache_manager.update_with_bhavcopy(symbol, stock_data)
                    summary['updated'] += 1
                else:
                    summary['errors'] += 1

            except Exception as e:
                logger.error(f"Error updating {symbol} with bhavcopy data: {e}")
                summary['errors'] += 1
                continue

        logger.info(f"Daily bhavcopy update completed: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Error in daily bhavcopy update: {e}")
        return {'error': str(e)}
```

## Usage Examples

### Basic Bhavcopy Download
```python
from src.utils.nse_fetcher import nse_bhavcopy_fetcher
from datetime import date

# Get today's bhavcopy (after market close)
bhavcopy_data = nse_bhavcopy_fetcher.get_latest_bhavcopy()

# Get specific stock
stock_data = nse_bhavcopy_fetcher.get_stock_from_bhavcopy('RELIANCE', bhavcopy_data)
```

### Update Cache with Latest Data
```python
from src.utils.data_fetcher import data_fetcher

# Update all cached stocks with latest bhavcopy
result = data_fetcher.update_daily_bhavcopy()
print(f"Updated {result['updated']} stocks")
```

### Cron Job for Daily Updates
```bash
# Add to crontab (run at 6:30 PM IST daily)
30 18 * * 1-5 python /path/to/ma_stock_trader/update_bhavcopy_daily.py
```

## Error Handling

### Common Issues
1. **404 Error**: Bhavcopy not yet available (market still open)
2. **Network Timeout**: Retry with exponential backoff
3. **Invalid Data**: Log and skip corrupted entries
4. **Date Mismatch**: Ensure date formats are consistent

### Fallback Strategy
```python
def get_latest_data_with_fallback(symbol: str):
    """Get latest data with bhavcopy fallback"""
    # Try Upstox first
    data = upstox_fetcher.get_latest_data(symbol)
    if data:
        return data

    # Fallback to bhavcopy
    bhavcopy_df = nse_bhavcopy_fetcher.get_latest_bhavcopy()
    if bhavcopy_df is not None:
        return nse_bhavcopy_fetcher.get_stock_from_bhavcopy(symbol, bhavcopy_df)

    return None
```

## Performance Considerations

### File Sizes
- **Compressed**: ~5MB per day
- **Uncompressed**: ~50MB per day
- **Storage**: Keep last 30 days locally

### API Limits
- **Rate Limiting**: Built-in delays prevent blocking
- **Concurrent Downloads**: Sequential to avoid overload
- **Caching**: Avoid re-downloading same files

### Memory Usage
- **Chunked Reading**: Process large files in chunks
- **Selective Loading**: Only load required stocks
- **Cleanup**: Remove temporary files after processing

## Testing

### Unit Tests
```python
def test_bhavcopy_download():
    from datetime import date
    fetcher = NSEBhavcopyFetcher()

    # Test download
    test_date = date.today() - timedelta(days=1)
    df = fetcher.download_bhavcopy(test_date)

    assert df is not None, "Bhavcopy download failed"
    assert 'symbol' in df.columns, "Missing symbol column"
    assert len(df) > 1000, "Too few stocks"

def test_stock_extraction():
    # Test extracting specific stock
    bhavcopy_df = fetcher.get_latest_bhavcopy()
    stock_df = fetcher.get_stock_from_bhavcopy('RELIANCE', bhavcopy_df)

    assert not stock_df.empty, "Stock extraction failed"
    assert len(stock_df) == 1, "Should return one row"
```

### Integration Tests
```python
def test_full_integration():
    """Test bhavcopy integration with cache system"""
    # Download bhavcopy
    bhavcopy_df = nse_bhavcopy_fetcher.get_latest_bhavcopy()

    # Update cache
    result = data_fetcher.update_daily_bhavcopy()

    # Verify data
    assert result['updated'] > 0, "No stocks updated"
    assert result['errors'] == 0, "Errors during update"
```

## Deployment

### Production Setup
1. **Schedule daily updates** after market close
2. **Monitor disk space** for cache files
3. **Backup cache** regularly
4. **Handle holidays** (no bhavcopy on holidays)

### Monitoring
- **Success rates** of downloads
- **Data quality** checks
- **Performance metrics** (download times)
- **Error rates** and alerts

This bhavcopy integration ensures you always have the most current NSE data for accurate trading decisions.