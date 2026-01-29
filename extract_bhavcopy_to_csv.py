#!/usr/bin/env python3
"""
Extract Complete Bhavcopy Data to CSV
Downloads latest bhavcopy and saves all OHLCV data to CSV file
"""

import pandas as pd
from datetime import date, datetime
from pathlib import Path
from src.utils.nse_fetcher import nse_bhavcopy_fetcher

def extract_bhavcopy_to_csv():
    """Download bhavcopy and save complete OHLCV data to CSV"""

    print("📊 EXTRACTING COMPLETE BHAVCOPY DATA TO CSV")
    print("=" * 55)

    # Get yesterday's date (latest available bhavcopy)
    target_date = date.today() - pd.Timedelta(days=1)
    print(f"Target Date: {target_date}")
    print(f"Time: {datetime.now()}")
    print()

    try:
        # Download bhavcopy data
        print("📥 Downloading bhavcopy data...")
        df = nse_bhavcopy_fetcher.download_bhavcopy(target_date)

        if df is None or df.empty:
            print("❌ FAILED: No bhavcopy data available")
            print("   Reason: NSE data retention (available ~6 PM IST daily)")
            return

        print(f" SUCCESS: Downloaded {len(df)} stocks")

        # Show data info
        print(f"\n📋 DATA INFO:")
        print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"   Columns: {list(df.columns)}")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

        # Show sample data
        print(f"\n📊 SAMPLE STOCK DATA (First 10):")
        sample = df.head(10)
        for _, row in sample.iterrows():
            print(f"   {row['symbol']:<12}: O:{row['open']:>8.2f} H:{row['high']:>8.2f} L:{row['low']:>8.2f} C:{row['close']:>8.2f} V:{row['volume']:>10.0f}")

        # Check for BLSE specifically
        if 'BLSE' in df['symbol'].values:
            blse_data = df[df['symbol'] == 'BLSE'].iloc[0]
            print(f"\n🎯 BLSE DATA: O:{blse_data['open']:.2f} H:{blse_data['high']:.2f} L:{blse_data['low']:.2f} C:{blse_data['close']:.2f} V:{blse_data['volume']}")

        # Save to CSV
        csv_filename = f"bhavcopy_complete_{target_date.strftime('%Y%m%d')}.csv"
        df.to_csv(csv_filename, index=False)

        # Get file size
        file_size = Path(csv_filename).stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        print(f"\n💾 SAVED TO CSV: {csv_filename}")
        print(f"   File size: {file_size_mb:.2f} MB")
        print("   Contains OHLCV data for ALL downloaded stocks")

        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"   Total stocks with data: {len(df)}")
        print("   All stocks have complete OHLCV data")
        print("   CSV file ready for analysis")

        # Show some statistics
        print(f"\n📊 DATA STATISTICS:")
        print(f"   Average volume: {df['volume'].mean():,.0f}")
        print(f"   Price range: ₹{df['low'].min():.2f} - ₹{df['high'].max():.2f}")
        print(f"   Trading value: ₹{df['volume'].sum():,.0f}")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("Failed to extract bhavcopy data")

if __name__ == "__main__":
    extract_bhavcopy_to_csv()