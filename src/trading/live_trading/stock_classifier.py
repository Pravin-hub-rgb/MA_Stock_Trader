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

                # Classify situation based on priority system
                if days >= 7:
                    situation = 'reversal_vip'  # 7+ days, any trend (elite)
                elif trend == 'd':
                    situation = 'reversal_secondary'  # 3-6 days, downtrend
                else:  # trend == 'u'
                    situation = 'reversal_tertiary'  # 3-6 days, uptrend

                symbols.append(symbol)
                situations[symbol] = situation

            print(f"Loaded {len(symbols)} reversal stocks:")

            # Create a mapping of symbol to its trend and days for printing
            symbol_details = {}
            for entry in raw_entries:
                parts = entry.split('-')
                if len(parts) == 2:
                    symbol = parts[0]
                    trend_days = parts[1]
                    if len(trend_days) >= 2:
                        trend = trend_days[0]
                        try:
                            days = int(trend_days[1:])
                            symbol_details[symbol] = (trend, days)
                        except ValueError:
                            pass

            for symbol, situation in situations.items():
                trend, days = symbol_details.get(symbol, ('?', 0))
                if situation == 'reversal_vip':
                    desc = f"7+ days ({trend}{days}) - ELITE VIP"
                elif situation == 'reversal_secondary':
                    desc = f"3-6 days + downtrend ({trend}{days})"
                else:  # reversal_tertiary
                    desc = f"3-6 days + uptrend ({trend}{days})"
                print(f"   {symbol}: {desc}")

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
