#!/usr/bin/env python3
"""
Final comprehensive verification that all cached stocks have Jan 6 data
"""

from src.utils.cache_manager import cache_manager
import pandas as pd
from pathlib import Path

def final_verification():
    """Comprehensive verification of Jan 6 data coverage"""

    print(' COMPREHENSIVE VERIFICATION: ALL CACHED STOCKS HAVE JAN 6 DATA')
    print('=' * 80)

    # Get all cached stocks
    cache_dir = Path('data/cache')
    cached_files = list(cache_dir.glob('*.pkl'))
    total_cached = len(cached_files)

    print(f'Total cached stocks: {total_cached}')
    print(f'Expected Jan 6 data coverage: 100% ({total_cached}/{total_cached})')

    # Check Jan 6 data coverage
    target_date = pd.Timestamp('2026-01-06')
    with_jan6 = 0
    without_jan6 = 0
    errors = 0

    print('\n Checking each stock individually...')
    missing_stocks = []

    for i, cache_file in enumerate(cached_files):
        symbol = cache_file.stem
        try:
            df = cache_manager.load_cached_data(symbol)
            if df is not None and target_date in df.index:
                with_jan6 += 1
            else:
                without_jan6 += 1
                missing_stocks.append(symbol)
        except Exception as e:
            errors += 1
            without_jan6 += 1
            missing_stocks.append(f'{symbol} (error: {str(e)[:30]})')

        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f'   Verified {i + 1}/{total_cached} stocks...')

    print('\n' + '=' * 80)
    print(' FINAL VERIFICATION RESULTS:')
    print(f' Stocks WITH Jan 6 data: {with_jan6}')
    print(f' Stocks WITHOUT Jan 6 data: {without_jan6}')
    print(f' Errors during checking: {errors}')
    print(f' Coverage: {with_jan6}/{total_cached} ({with_jan6/total_cached*100:.2f}%)')

    if without_jan6 > 0:
        print(f'\n  MISSING STOCKS ({len(missing_stocks)}):')
        for i, stock in enumerate(missing_stocks[:10]):  # Show first 10
            print(f'   {i+1}. {stock}')
        if len(missing_stocks) > 10:
            print(f'   ... and {len(missing_stocks) - 10} more')

    # Additional verification: Sample some stocks to show their data
    if with_jan6 > 0:
        print(f'\n SAMPLE STOCK VERIFICATION:')
        sample_indices = [0, 100, 500, 1000, 1500, 2000, -1]  # First, middle, last
        for idx in sample_indices:
            if 0 <= idx < len(cached_files):
                symbol = cached_files[idx].stem
                try:
                    df = cache_manager.load_cached_data(symbol)
                    if df is not None and target_date in df.index:
                        row = df.loc[target_date]
                        print(f'   {symbol}: O:{row["open"]:.2f} H:{row["high"]:.2f} L:{row["low"]:.2f} C:{row["close"]:.2f} V:{row["volume"]:.0f}')
                    else:
                        print(f'   {symbol}:  Missing Jan 6 data')
                except Exception as e:
                    print(f'   {symbol}:  Error - {str(e)[:30]}')

    print('\n' + '=' * 50)
    if with_jan6 == total_cached and without_jan6 == 0:
        print('🎉 VERIFICATION COMPLETE: ALL STOCKS HAVE JAN 6 DATA!')
        print(' 100% coverage achieved')
        print(' NSE bhavcopy integration successful')
        print(' System ready for production')
    elif with_jan6/total_cached >= 0.99:
        print(' NEARLY COMPLETE: 99%+ coverage achieved')
    else:
        print('  INCOMPLETE: Significant gaps remain')

if __name__ == "__main__":
    final_verification()