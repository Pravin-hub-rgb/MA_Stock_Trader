"""
OOPS Reversal Trading System
Implements OOPS-based reversal trading with VIP elite-first priority
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, time
import pytz
import os

IST = pytz.timezone('Asia/Kolkata')

class ReversalMonitor:
    """Handles OOPS-based reversal trading logic"""

    def __init__(self):
        # Priority-based stock classification
        self.vip_stocks = []      # Priority 1: 7+ days (any trend)
        self.secondary_stocks = [] # Priority 2: 3-6 days + downtrend
        self.tertiary_stocks = []  # Priority 3: 3-6 days + uptrend

        # Trading state
        self.active_positions = 0
        self.max_positions = 2
        self.watchlist_loaded = False

    def load_watchlist(self, reversal_list_path: str = "src/trading/reversal_list.txt") -> bool:
        """
        Load and classify stocks from reversal_list.txt (SYMBOL-TREND-DAYS format)

        Args:
            reversal_list_path: Path to reversal list file

        Returns:
            bool: True if loaded successfully
        """
        try:
            if not os.path.exists(reversal_list_path):
                print(f"Reversal list not found: {reversal_list_path}")
                return False

            with open(reversal_list_path, 'r') as f:
                content = f.read().strip()

            if not content:
                print("Reversal list is empty")
                return False

            # Reset classifications
            self.vip_stocks = []
            self.secondary_stocks = []
            self.tertiary_stocks = []

            # Parse each entry
            entries = content.split(',')
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue

                parts = entry.split('-')
                if len(parts) != 2:
                    print(f"Invalid entry format: {entry} (expected SYMBOL-TRENDDAYS)")
                    continue

                symbol = parts[0]
                trend_days = parts[1]  # 'd7' or 'u5'

                # Parse trend and days from combined field
                if len(trend_days) < 2:
                    print(f"Invalid trend-days format: {trend_days} in {entry}")
                    continue

                trend = trend_days[0]  # 'd' or 'u'
                days_str = trend_days[1:]  # '7' or '5'

                try:
                    days = int(days_str)
                except ValueError:
                    print(f"Invalid days format: {days_str} in {entry}")
                    continue

                if trend not in ['u', 'd']:
                    print(f"Invalid trend format: {trend} in {entry} (expected 'u' or 'd')")
                    continue

                # Classify by priority
                stock_info = {
                    'symbol': symbol,
                    'trend': trend,
                    'days': days,
                    'triggered': False,
                    'entry_price': None,
                    'stop_loss': None
                }

                if days >= 7:
                    self.vip_stocks.append(stock_info)
                    print(f"✓ VIP Stock: {symbol}-{trend}{days} (7+ days, any trend)")
                elif days >= 3:
                    if trend == 'd':
                        self.secondary_stocks.append(stock_info)
                        print(f"✓ Secondary Stock: {symbol}-{trend}{days} (3-6 days, downtrend)")
                    else:  # trend == 'u'
                        self.tertiary_stocks.append(stock_info)
                        print(f"✓ Tertiary Stock: {symbol}-{trend}{days} (3-6 days, uptrend)")
                else:
                    print(f"⚠ Skipping {symbol}: Only {days} days (minimum 3)")

            total_stocks = len(self.vip_stocks) + len(self.secondary_stocks) + len(self.tertiary_stocks)
            print(f"Loaded {total_stocks} reversal stocks: {len(self.vip_stocks)} VIP, {len(self.secondary_stocks)} secondary, {len(self.tertiary_stocks)} tertiary")

            self.watchlist_loaded = True
            return True

        except Exception as e:
            print(f"Error loading reversal watchlist: {e}")
            return False

    def check_oops_trigger(self, symbol: str, open_price: float, prev_close: float, current_price: float) -> bool:
        """
        Check if OOPS reversal conditions are met

        Args:
            symbol: Stock symbol
            open_price: Opening price
            prev_close: Previous day's close
            current_price: Current price

        Returns:
            bool: True if OOPS conditions met
        """
        if None in [open_price, prev_close, current_price]:
            return False

        # Condition 1: Gap down
        gap_down = open_price < (prev_close * 0.98)  # 2%+ gap down

        # Condition 2: Price crosses above previous close
        crosses_prev_close = current_price > prev_close

        return gap_down and crosses_prev_close

    def check_strong_start_trigger(self, symbol: str, open_price: float, prev_close: float, current_low: float) -> bool:
        """
        Check if Strong Start conditions are met

        Args:
            symbol: Stock symbol
            open_price: Opening price
            prev_close: Previous day's close
            current_low: Current low

        Returns:
            bool: True if Strong Start conditions met
        """
        if None in [open_price, prev_close, current_low]:
            return False

        # Condition 1: Gap up (2%+ above prev close)
        gap_up = open_price > (prev_close * 1.02)

        # Condition 2: Open ≈ low within 1%
        open_equals_low = abs(open_price - current_low) / open_price <= 0.01

        return gap_up and open_equals_low

    def find_stock_in_watchlist(self, symbol: str) -> Optional[Dict]:
        """Find stock in watchlist by symbol"""
        for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
            for stock in category:
                if stock['symbol'] == symbol:
                    return stock
        return None

    def log_paper_trade(self, symbol: str, action: str, price: float, reason: str) -> None:
        """
        Log paper trading activity

        Args:
            symbol: Stock symbol
            action: Action taken (ENTRY, EXIT, etc.)
            price: Price at action
            reason: Reason for action
        """
        timestamp = datetime.now(IST).strftime("%H:%M:%S")
        print(f"📊 PAPER TRADE [{timestamp}] {symbol}: {action} at ₹{price:.2f} - {reason}")

    def execute_vip_first_logic(self, market_data: Dict[str, Any], current_time: time) -> None:
        """
        Execute VIP elite-first trading logic

        Args:
            market_data: Dict of symbol -> price data
            current_time: Current market time
        """
        if not self.watchlist_loaded:
            print("Watchlist not loaded - call load_watchlist() first")
            return

        # Check for triggered stocks in priority order
        triggered_stocks = []

        # Check VIP stocks first (highest priority)
        for stock in self.vip_stocks:
            if stock['triggered']:
                continue

            symbol = stock['symbol']
            if symbol not in market_data:
                continue

            data = market_data[symbol]
            open_price = data.get('open')
            prev_close = data.get('prev_close')
            current_price = data.get('ltp')

            # Check OOPS trigger
            if self.check_oops_trigger(symbol, open_price, prev_close, current_price):
                triggered_stocks.append({
                    'stock': stock,
                    'priority': 1,
                    'method': 'OOPS',
                    'price': current_price
                })

        # Check secondary stocks (only if slots available)
        if self.active_positions < self.max_positions:
            for stock in self.secondary_stocks:
                if stock['triggered']:
                    continue

                symbol = stock['symbol']
                if symbol not in market_data:
                    continue

                data = market_data[symbol]
                open_price = data.get('open')
                prev_close = data.get('prev_close')
                current_price = data.get('ltp')
                current_low = data.get('low')

                # Check OOPS first, then Strong Start
                if self.check_oops_trigger(symbol, open_price, prev_close, current_price):
                    triggered_stocks.append({
                        'stock': stock,
                        'priority': 2,
                        'method': 'OOPS',
                        'price': current_price
                    })
                elif self.check_strong_start_trigger(symbol, open_price, prev_close, current_low):
                    # Check time window for Strong Start (first 5 min)
                    market_open = time(9, 15)
                    five_min_later = time(9, 20)
                    if market_open <= current_time <= five_min_later:
                        triggered_stocks.append({
                            'stock': stock,
                            'priority': 2,
                            'method': 'Strong Start',
                            'price': current_price
                        })

        # Sort by priority (lower number = higher priority)
        triggered_stocks.sort(key=lambda x: x['priority'])

        # Execute trades (first-come-first-served within priority)
        for trigger in triggered_stocks:
            if self.active_positions >= self.max_positions:
                break

            stock = trigger['stock']
            if stock['triggered']:
                continue

            # Execute entry
            stock['triggered'] = True
            stock['entry_price'] = trigger['price']
            stock['stop_loss'] = trigger['price'] * 0.96  # 4% below

            self.active_positions += 1

            # Log paper trade
            self.log_paper_trade(
                stock['symbol'],
                "ENTRY",
                trigger['price'],
                f"Priority {trigger['priority']} - {trigger['method']}"
            )

    def reset_daily_state(self) -> None:
        """Reset daily trading state"""
        self.active_positions = 0

        # Reset all stock triggers but keep classifications
        for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
            for stock in category:
                stock['triggered'] = False
                stock['entry_price'] = None
                stock['stop_loss'] = None

        print("Daily reversal trading state reset")
