"""
Stock classification for live trading bot
Handles parsing of stock lists and situation classification
"""

import os
from typing import Dict, List, Tuple

class StockClassifier:
    """Classifies stocks into trading situations"""

    def __init__(self, trading_root: str = 'src/trading'):
        self.trading_root = trading_root

    def load_continuation_stocks(self) -> List[str]:
        """
        Load stocks from continuation_list.txt

        Returns:
            List[str]: List of stock symbols
        """
        filepath = os.path.join(self.trading_root, 'continuation_list.txt')

        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                symbols = [s.strip() for s in content.split(',') if s.strip()]

            # Removed verbose logging - now handled in main orchestrator
            return symbols

        except FileNotFoundError:
            print(f"Continuation list not found: {filepath}")
            return []
        except Exception as e:
            print(f"Error loading continuation list: {e}")
            return []

    def load_reversal_stocks(self) -> Tuple[List[str], Dict[str, str]]:
        """
        Load stocks from reversal_list.txt and classify situations (SYMBOL-TREND-DAYS format)

        Returns:
            Tuple[List[str], Dict[str, str]]: (symbols, symbol_to_situation_map)
        """
        filepath = os.path.join(self.trading_root, 'reversal_list.txt')

        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                raw_entries = [s.strip() for s in content.split(',') if s.strip()]

            symbols = []
            situations = {}

            for entry in raw_entries:
                # Parse SYMBOL-TREND-DAYS format (e.g., "ELECON-u6")
                parts = entry.split('-')
                if len(parts) != 2:
                    print(f"Warning: Invalid format {entry}, expected SYMBOL-TRENDDAYS")
                    continue

                symbol = parts[0]
                trend_days = parts[1]

                # Parse trend and days
                if len(trend_days) < 2:
                    print(f"Warning: Invalid trend-days {trend_days} in {entry}")
                    continue

                trend = trend_days[0]  # 'u' or 'd'
                try:
                    days = int(trend_days[1:])
                except ValueError:
                    print(f"Warning: Invalid days format {trend_days[1:]} in {entry}")
                    continue

                if trend not in ['u', 'd']:
                    print(f"Warning: Invalid trend {trend} in {entry}, expected 'u' or 'd'")
                    continue

                # Classify situation based on simplified trend logic
                if days >= 7:
                    situation = 'reversal_s2'  # 7+ days, any trend = OOPS
                elif trend == 'u':
                    situation = 'reversal_s1'  # 3-6 days, uptrend = Strong Start
                else:  # trend == 'd'
                    situation = 'reversal_s2'  # 3-6 days, downtrend = OOPS

                symbols.append(symbol)
                situations[symbol] = situation

            # ✅ REMOVED: Skip verbose logging for pure first-come-first-serve
            # Classification is handled internally, no need to print details

            return symbols, situations

        except FileNotFoundError:
            print(f"Reversal list not found: {filepath}")
            return [], {}
        except Exception as e:
            print(f"Error loading reversal list: {e}")
            return [], {}

    def get_stock_configuration(self, mode: str) -> Dict:
        """
        Get stock configuration based on trading mode

        Args:
            mode: 'c' for continuation, 'r' for reversal

        Returns:
            Dict: Configuration with symbols and classifications
        """
        if mode == 'c':
            symbols = self.load_continuation_stocks()
            situations = {symbol: 'continuation' for symbol in symbols}
        elif mode == 'r':
            symbols, situations = self.load_reversal_stocks()
        else:
            raise ValueError(f"Invalid mode: {mode}")

        return {
            'symbols': symbols,
            'situations': situations,
            'total_stocks': len(symbols)
        }

    def get_continuation_stock_configuration(self) -> Dict:
        """
        Get continuation stock configuration

        Returns:
            Dict: Configuration with symbols and classifications for continuation mode
        """
        symbols = self.load_continuation_stocks()
        situations = {symbol: 'continuation' for symbol in symbols}

        return {
            'symbols': symbols,
            'situations': situations,
            'total_stocks': len(symbols)
        }

    def get_reversal_stock_configuration(self) -> Dict:
        """
        Get reversal stock configuration

        Returns:
            Dict: Configuration with symbols and classifications for reversal mode
        """
        symbols, situations = self.load_reversal_stocks()

        return {
            'symbols': symbols,
            'situations': situations,
            'total_stocks': len(symbols)
        }
