# -*- coding: utf-8 -*-
"""
Selection Engine - Selects which stocks to trade from qualified candidates
"""

import sys
import os
import logging
from typing import List, Dict, Optional

# Import from local config file
from .config import MAX_STOCKS_TO_TRADE
from stock_monitor import StockState

logger = logging.getLogger(__name__)


class SelectionEngine:
    """Engine for selecting stocks to trade"""

    def __init__(self):
        self.selection_method = "quality_score"  # Use quality scoring for better selection

    def select_stocks(self, qualified_stocks: List[StockState], max_to_select: int = MAX_STOCKS_TO_TRADE) -> List[StockState]:
        """
        Select stocks to trade from qualified candidates

        Args:
            qualified_stocks: List of stocks that passed all validation
            max_to_select: Maximum number of stocks to select

        Returns:
            List of selected stocks
        """
        if not qualified_stocks:
            logger.info("No qualified stocks to select from")
            return []

        if len(qualified_stocks) <= max_to_select:
            logger.info(f"All {len(qualified_stocks)} qualified stocks selected")
            return qualified_stocks

        # Apply selection method
        if self.selection_method == "alphabetical":
            selected = self._select_alphabetical(qualified_stocks, max_to_select)
        elif self.selection_method == "quality_score":
            selected = self._select_by_quality_score(qualified_stocks, max_to_select)
        elif self.selection_method == "market_cap":
            selected = self._select_by_market_cap(qualified_stocks, max_to_select)
        elif self.selection_method == "adr":
            selected = self._select_by_adr(qualified_stocks, max_to_select)
        else:
            logger.warning(f"Unknown selection method: {self.selection_method}, using alphabetical")
            selected = self._select_alphabetical(qualified_stocks, max_to_select)

        logger.info(f"Selected {len(selected)} stocks using {self.selection_method} method: "
                   f"{[s.symbol for s in selected]}")

        return selected

    def _select_alphabetical(self, stocks: List[StockState], max_count: int) -> List[StockState]:
        """Select stocks alphabetically"""
        sorted_stocks = sorted(stocks, key=lambda s: s.symbol)
        return sorted_stocks[:max_count]

    def _select_by_market_cap(self, stocks: List[StockState], max_count: int) -> List[StockState]:
        """Select stocks by market cap (placeholder - needs market cap data)"""
        # For now, fall back to alphabetical
        # In future, would need market cap data from somewhere
        logger.warning("Market cap selection not implemented, using alphabetical")
        return self._select_alphabetical(stocks, max_count)

    def _select_by_adr(self, stocks: List[StockState], max_count: int) -> List[StockState]:
        """Select stocks by ADR (placeholder - needs ADR data)"""
        # For now, fall back to alphabetical
        # In future, would calculate ADR for each stock
        logger.warning("ADR selection not implemented, using alphabetical")
        return self._select_alphabetical(stocks, max_count)

    def _select_by_quality_score(self, stocks: List[StockState], max_count: int) -> List[StockState]:
        """Select stocks by quality score (ADR + Price + Volume)"""
        try:
            # Lazy import to avoid circular dependencies
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from scanner.stock_scorer import stock_scorer

            # Get symbols and calculate early volumes from current monitoring
            symbols = [stock.symbol for stock in stocks]
            early_volumes = {stock.symbol: getattr(stock, 'early_volume', 0) for stock in stocks}

            # Get top stocks by score
            top_scored = stock_scorer.get_top_stocks(symbols, early_volumes, max_count)

            # Convert back to StockState objects
            symbol_to_stock = {stock.symbol: stock for stock in stocks}
            selected_stocks = []

            for score_data in top_scored:
                symbol = score_data['symbol']
                if symbol in symbol_to_stock:
                    selected_stocks.append(symbol_to_stock[symbol])
                    logger.info(f"Selected {symbol}: Score {score_data['total_score']} "
                               f"(ADR: {score_data['adr_score']}, Price: {score_data['price_score']}, "
                               f"Volume: {score_data['volume_score']})")

            return selected_stocks

        except Exception as e:
            logger.error(f"Error in quality score selection: {e}")
            # Return empty list - no fallback to alphabetical
            return []

    def set_selection_method(self, method: str):
        """Set the selection method"""
        valid_methods = ["alphabetical", "quality_score", "market_cap", "adr"]
        if method not in valid_methods:
            logger.warning(f"Invalid selection method: {method}, valid: {valid_methods}")
            return

        self.selection_method = method
        logger.info(f"Selection method set to: {method}")

    def get_selection_criteria(self) -> Dict[str, any]:
        """Get current selection criteria"""
        return {
            'method': self.selection_method,
            'max_stocks': MAX_STOCKS_TO_TRADE,
            'available_methods': ["alphabetical", "quality_score", "market_cap", "adr"]
        }

    def rank_stocks(self, stocks: List[StockState]) -> List[Dict[str, any]]:
        """Rank stocks by various criteria for analysis"""
        rankings = []

        for stock in stocks:
            # Calculate ranking scores
            score = {
                'symbol': stock.symbol,
                'gap_up_pct': ((stock.open_price - stock.previous_close) / stock.previous_close) if stock.open_price else 0,
                'high_low_ratio': stock.daily_high / stock.daily_low if stock.daily_low > 0 else 0,
                'distance_from_open': abs(stock.current_price - stock.open_price) / stock.open_price if stock.open_price and stock.current_price else 0,
                # Add more ranking criteria as needed
            }

            rankings.append(score)

        # Sort by composite score (can be customized)
        rankings.sort(key=lambda x: x['gap_up_pct'], reverse=True)

        return rankings
