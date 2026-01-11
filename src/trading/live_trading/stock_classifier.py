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

            print(f"📋 Loaded {len(symbols)} continuation stocks: {symbols}")
            return symbols

        except FileNotFoundError:
            print(f"❌ Continuation list not found: {filepath}")
            return []
        except Exception as e:
            print(f"❌ Error loading continuation list: {e}")
            return []

    def load_reversal_stocks(self) -> Tuple[List[str], Dict[str, str]]:
        """
        Load stocks from reversal_list.txt and classify situations

        Returns:
            Tuple[List[str], Dict[str, str]]: (symbols, symbol_to_situation_map)
        """
        filepath = os.path.join(self.trading_root, 'reversal_list.txt')

        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                raw_symbols = [s.strip() for s in content.split(',') if s.strip()]

            symbols = []
            situations = {}

            for raw_symbol in raw_symbols:
                if raw_symbol.endswith('-u'):
                    symbol = raw_symbol[:-2]  # Remove -u
                    situation = 'reversal_s1'  # Uptrend reversal
                elif raw_symbol.endswith('-d'):
                    symbol = raw_symbol[:-2]  # Remove -d
                    situation = 'reversal_s2'  # Downtrend reversal
                else:
                    print(f"⚠️ Warning: {raw_symbol} has no -u/-d flag, skipping")
                    continue

                symbols.append(symbol)
                situations[symbol] = situation

            print(f"📋 Loaded {len(symbols)} reversal stocks:")
            for symbol, situation in situations.items():
                desc = "Uptrend (Continuation method)" if situation == 'reversal_s1' else "Downtrend (Gap down required)"
                print(f"   {symbol}: {desc}")

            return symbols, situations

        except FileNotFoundError:
            print(f"❌ Reversal list not found: {filepath}")
            return [], {}
        except Exception as e:
            print(f"❌ Error loading reversal list: {e}")
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
