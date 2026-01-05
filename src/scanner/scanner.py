"""
Market Scanner for MA Stock Trader
Implements continuation and reversal scan algorithms
"""

import logging
from datetime import date
from typing import List, Dict, Optional

from src.utils.database import db
from src.utils.data_fetcher import data_fetcher
from .filters import FilterEngine
from .continuation_analyzer import ContinuationAnalyzer
from .reversal_analyzer import ReversalAnalyzer

logger = logging.getLogger(__name__)


class Scanner:
    """Main scanner class for continuation and reversal detection"""

    def __init__(self):
        # Scan parameters - only used ones
        self.continuation_params = {
            'min_volume_days': 1,            # At least 1 day with 1M+ volume
            'volume_threshold': 1000000,     # 1M shares
            'min_adr': 0.03,                 # 3% ADR
            'price_min': 100,                # ₹100 minimum
            'price_max': 2000,               # ₹2000 maximum
        }

        # Reversal scan parameters
        self.reversal_params = {
            'decline_days': (4, 7),          # 4-7 days decline
            'min_decline_percent': 0.10,     # 10% minimum decline
            'min_volume_days': 1,            # At least 1 day with 1M+ volume
            'volume_threshold': 1000000,     # 1M shares
            'min_adr': 0.03,                 # 3% ADR
            'price_min': 100,                # ₹100 minimum
            'price_max': 2000,               # ₹2000 maximum
        }

        # Initialize analyzer modules
        self.filter_engine = FilterEngine(self.continuation_params, self.reversal_params)
        self.continuation_analyzer = ContinuationAnalyzer(self.filter_engine)
        self.reversal_analyzer = ReversalAnalyzer(self.filter_engine, self.reversal_params)
    
    def run_continuation_scan(self, scan_date: date = None) -> List[Dict]:
        """
        Run continuation scan for given date (default: today)
        Returns list of potential continuation candidates
        """
        if scan_date is None:
            scan_date = date.today()
        
        logger.info(f"Running continuation scan for {scan_date}")
        
        try:
            # Get NSE stocks
            nse_stocks = data_fetcher.fetch_nse_stocks()
            candidates = []
            
            # Use first 100 stocks directly (skip price filtering for now)
            filtered_stocks = nse_stocks[:100]
            logger.info(f"Using first {len(filtered_stocks)} stocks for scanning")
            
            # Scan each stock
            for stock in filtered_stocks:
                try:
                    symbol = stock['symbol']
                    result = self.continuation_analyzer.analyze_continuation_setup(symbol, scan_date)

                    if result:
                        candidates.append(result)

                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Sort by price (highest first)
            candidates.sort(key=lambda x: x['price'], reverse=True)
            
            logger.info(f"Found {len(candidates)} continuation candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error in continuation scan: {e}")
            return []
    
    def run_reversal_scan(self, scan_date: date = None) -> List[Dict]:
        """
        Run reversal scan for given date (default: today)
        Returns list of potential reversal candidates
        """
        if scan_date is None:
            scan_date = date.today()
        
        logger.info(f"Running reversal scan for {scan_date}")
        
        try:
            # Get NSE stocks
            nse_stocks = data_fetcher.fetch_nse_stocks()
            candidates = []
            
            # Filter by price range (optimized - limit to first 100 stocks)
            filtered_stocks = []
            for stock in nse_stocks[:100]:  # Limit to first 100 stocks for testing
                try:
                    price = self._get_stock_price(stock['symbol'])
                    if self.reversal_params['price_min'] <= price <= self.reversal_params['price_max']:
                        filtered_stocks.append(stock)
                except:
                    continue  # Skip stocks that fail to fetch price
            
            logger.info(f"Filtered {len(filtered_stocks)} stocks by price range from {len(nse_stocks[:100])} candidates")
            
            # Scan each stock
            for stock in filtered_stocks:
                try:
                    symbol = stock['symbol']
                    result = self.reversal_analyzer.analyze_reversal_setup(symbol, scan_date)

                    if result and result['score'] > 0:
                        candidates.append(result)

                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
                    continue
            
            # Sort by score
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Save results to database
            for candidate in candidates:
                db.insert_scan_result(
                    scan_type='reversal',
                    scan_date=scan_date,
                    stock_id=candidate['stock_id'],
                    score=candidate['score'],
                    notes=candidate['notes']
                )
            
            logger.info(f"Found {len(candidates)} reversal candidates")
            return candidates
            
        except Exception as e:
            logger.error(f"Error in reversal scan: {e}")
            return []

    def _get_stock_price(self, symbol: str) -> float:
        """Get current stock price for filtering"""
        try:
            data = data_fetcher.get_latest_data(symbol, days=1)
            return data.get('close', 0)
        except:
            return 0



# Global scanner instance
scanner = Scanner()
