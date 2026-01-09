#!/usr/bin/env python3
"""
Download and Process Jan 6, 2026 Bhavcopy Data
Simple script to get the latest trading day's data
"""

import requests
import json
import pandas as pd
import zipfile
import io
from datetime import date
from pathlib import Path

def download_jan6_bhavcopy():
    """Download Jan 6, 2026 bhavcopy data using direct URL (confirmed working pattern)"""
    target_date = date(2026, 1, 6)
    yyyymmdd = target_date.strftime('%Y%m%d')  # 20260106

    print(f"Downloading bhavcopy for {target_date}...")
    print("=" * 50)

    try:
        # Use confirmed direct URL pattern for post-2024 UDiFF bhavcopy
        zip_url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.nseindia.com/all-reports',
            'Accept': 'application/zip',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }

        # Create session and get cookies
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=10)

        print(f"Direct URL: {zip_url}")

        # Download the ZIP file directly
        print("Downloading ZIP file...")
        zip_response = session.get(zip_url, headers=headers, timeout=30)
        zip_response.raise_for_status()

        # Process ZIP content
        print("Processing data...")
        with zipfile.ZipFile(io.BytesIO(zip_response.content)) as zf:
            csv_files = [f for f in zf.namelist() if f.endswith('.csv')]
            if not csv_files:
                print("❌ No CSV file found in ZIP")
                return None

            with zf.open(csv_files[0]) as f:
                df = pd.read_csv(f)

        # Debug: Check what columns we have
        print(f"Available columns: {list(df.columns)}")

        # Process data - filter for equity series (UDiFF format)
        if 'SctySrs' in df.columns:
            df = df[df['SctySrs'] == 'EQ']  # Filter equities only
        else:
            print("⚠️  Warning: SctySrs column not found, processing all data")

        # Standardize columns (UDiFF format)
        column_mapping = {
            'TckrSymb': 'symbol',      # Ticker Symbol
            'TradDt': 'date',          # Trading Date
            'OpnPric': 'open',         # Open Price
            'HghPric': 'high',         # High Price
            'LwPric': 'low',           # Low Price
            'ClsPric': 'close',        # Close Price
            'TtlTradgVol': 'volume'    # Total Trading Volume
        }

        df = df.rename(columns=column_mapping)
        df['date'] = pd.to_datetime(df['date']).dt.date
        df = df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]

        # Convert data types
        df['volume'] = df['volume'].astype(int)
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)

        print(f"✅ SUCCESS: Processed {len(df)} stocks")

        # Show sample data
        if 'BLSE' in df['symbol'].values:
            blse = df[df['symbol'] == 'BLSE'].iloc[0]
            print(f"BLSE data: O:{blse['open']} H:{blse['high']} L:{blse['low']} C:{blse['close']} V:{blse['volume']}")

        print("\nFirst 5 stocks:")
        for _, row in df.head(5).iterrows():
            print(f"  {row['symbol']:<10}: Close={row['close']:>8.2f}, Volume={row['volume']:>10}")

        return df

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def update_cache_with_data(df):
    """Update cache with downloaded data"""
    print("\n💾 UPDATING CACHE...")
    print("=" * 30)

    from src.utils.cache_manager import cache_manager

    updated_count = 0
    for symbol in df['symbol'].unique():
        try:
            stock_data = df[df['symbol'] == symbol]
            row = stock_data.iloc[0]

            # Create DataFrame for cache
            cache_df = pd.DataFrame([{
                'date': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume']
            }])

            cache_df['date'] = pd.to_datetime(cache_df['date'])
            cache_df.set_index('date', inplace=True)

            # Update cache
            cache_manager.update_with_bhavcopy(symbol, cache_df)
            updated_count += 1

            if updated_count <= 3:
                print(f"  ✅ Updated {symbol}")

        except Exception as e:
            print(f"  ❌ Error updating {symbol}: {e}")

    print(f"\n📊 Updated {updated_count} stocks in cache")

if __name__ == "__main__":
    print("📰 JAN 6, 2026 BHAVCOPY DOWNLOADER")
    print("=" * 45)

    # Download data
    df = download_jan6_bhavcopy()

    if df is not None:
        # Update cache
        update_cache_with_data(df)

        print("\n🎉 COMPLETE!")
        print("Jan 6 data added to all cached stocks")
        print("Ready for Jan 7 trading analysis")
    else:
        print("\n❌ FAILED")
        print("Could not download Jan 6 data")
        print("Try again after 6-7 PM IST if before market close")
