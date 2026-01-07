#!/usr/bin/env python3
"""
Add CHOLAFIN and ANURAS to cache with fixed instrument key mapping
"""

from src.utils.data_fetcher import data_fetcher
from datetime import date, timedelta

def add_cholafin_anuras():
    """Add CHOLAFIN and ANURAS to the cache"""
    print("📈 ADDING CHOLAFIN & ANURAS TO CACHE")
    print("=" * 50)

    from src.utils.cache_manager import cache_manager
    from src.utils.upstox_fetcher import upstox_fetcher

    # Stocks to add
    stocks = ['CHOLAFIN', 'ANURAS']

    # Date range (last 5 months)
    end_date = date.today()
    start_date = end_date - timedelta(days=150)

    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"📊 Stocks to add: {', '.join(stocks)}")

    for symbol in stocks:
        print(f"\n🔄 Adding {symbol} to cache...")
        try:
            # Fetch historical data using Upstox (with fixed instrument keys)
            df = upstox_fetcher.fetch_historical_data(symbol, start_date, end_date)

            if not df.empty:
                # Update cache with the fetched data
                cache_manager.update_cache(symbol, df)
                print("✅ Successfully added to cache")
                print(f"   📊 Data points: {len(df)} days")
                print(f"   📅 Date range: {df.index.min()} to {df.index.max()}")
                print(f"   💰 Latest close: ₹{df.iloc[-1]['close']:.2f}")
            else:
                print("❌ Failed to fetch data from Upstox")
        except Exception as e:
            print(f"❌ Error adding {symbol}: {e}")

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("CHOLAFIN and ANURAS should now be available in your scanner!")
    print("Run a continuation scan to verify they appear in results.")

if __name__ == "__main__":
    add_cholafin_anuras()
