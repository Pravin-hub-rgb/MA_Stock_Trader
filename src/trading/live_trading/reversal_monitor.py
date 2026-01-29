"""
OOPS Reversal Trading System
Implements OOPS-based reversal trading with VIP elite-first priority and quality scoring
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, time
import pytz
import os

IST = pytz.timezone('Asia/Kolkata')

class ReversalStock:
    """Individual stock tracking for reversal trading"""
    
    def __init__(self, symbol: str, trend: str, days: int):
        self.symbol = symbol
        self.trend = trend
        self.days = days
        self.triggered = False
        self.entry_price = None
        self.stop_loss = None
        
        # API-based opening prices only - NO TICK-BASED CAPTURE
        self.open_price = None  # Set via API only
        self.current_low = float('inf')
        self.gap_calculated = False

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
        
        # Opening price tracking for gap analysis
        self.opening_prices = {}  # symbol -> opening_price
        self.market_opened = False

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

            with open(reversal_list_path, 'r', encoding='utf-8') as f:
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

                # Create ReversalStock object
                stock = ReversalStock(symbol, trend, days)

                # Classify by priority
                if days >= 7:
                    self.vip_stocks.append(stock)
                    print(f"VIP Stock: {symbol}-{trend}{days} (7+ days, any trend)")
                elif days >= 3:
                    if trend == 'd':
                        self.secondary_stocks.append(stock)
                        print(f"Secondary Stock: {symbol}-{trend}{days} (3-6 days, downtrend)")
                    else:  # trend == 'u'
                        self.tertiary_stocks.append(stock)
                        print(f"Tertiary Stock: {symbol}-{trend}{days} (3-6 days, uptrend)")
                else:
                    print(f"Skipping {symbol}: Only {days} days (minimum 3)")

            total_stocks = len(self.vip_stocks) + len(self.secondary_stocks) + len(self.tertiary_stocks)
            print(f"Loaded {total_stocks} reversal stocks: {len(self.vip_stocks)} VIP, {len(self.secondary_stocks)} secondary, {len(self.tertiary_stocks)} tertiary")

            self.watchlist_loaded = True
            return True

        except Exception as e:
            print(f"Error loading reversal watchlist: {e}")
            return False

    def set_prev_closes(self, prev_closes: Dict[str, float]) -> None:
        """
        Set previous close prices for all stocks in the watchlist
        
        Args:
            prev_closes: Dict of symbol -> previous_close
        """
        for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
            for stock in category:
                if stock.symbol in prev_closes:
                    stock.prev_close = prev_closes[stock.symbol]
                    print(f"Set prev_close for {stock.symbol}: ₹{stock.prev_close:.2f}")
                else:
                    print(f"No prev_close found for {stock.symbol}")


    def get_opening_price_from_api(self, symbol: str) -> Optional[float]:
        """
        Get opening price from Upstox OHLC API with interval=1d for session data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            float: Opening price or None if not available
        """
        try:
            # Import Upstox fetcher
            from src.utils.upstox_fetcher import upstox_fetcher
            
            # Get OHLC data with interval=1d for session data
            ohlc_data = upstox_fetcher.get_current_ohlc([symbol])
            
            if symbol in ohlc_data and 'open' in ohlc_data[symbol]:
                opening_price = ohlc_data[symbol]['open']
                print(f"{symbol}: API opening price = ₹{opening_price:.2f}")
                return opening_price
            else:
                print(f"{symbol}: No opening price from API")
                return None
                
        except Exception as e:
            print(f"Error getting opening price from API for {symbol}: {e}")
            return None

    def calculate_stock_gap(self, stock: ReversalStock):
        """Calculate gap percentage for a stock"""
        if not stock.open_price or not hasattr(stock, 'prev_close') or not stock.prev_close:
            return None

        gap_pct = ((stock.open_price - stock.prev_close) / stock.prev_close) * 100
        stock.gap_calculated = True
        print(f"{stock.symbol}: Gap % = {gap_pct:.2f}% (Open: ₹{stock.open_price:.2f}, Prev Close: ₹{stock.prev_close:.2f})")
        return gap_pct

    def check_oops_conditions(self, stock: ReversalStock, current_price: float) -> bool:
        """Check OOPS reversal conditions for a stock"""
        if not stock.gap_calculated:
            return False
            
        gap_pct = ((stock.open_price - stock.prev_close) / stock.prev_close) * 100
        crosses_prev_close = current_price > stock.prev_close
        
        if gap_pct <= -2.0 and crosses_prev_close:
            print(f"{stock.symbol}: OOPS conditions met! Gap: {gap_pct:.2f}%, Crossed Prev Close: ₹{current_price:.2f}")
            return True
        return False

    def check_strong_start_conditions(self, stock: ReversalStock, current_low: float) -> bool:
        """Check Strong Start conditions for a stock"""
        if not stock.gap_calculated:
            return False
            
        # Import config to get configurable Strong Start gap percentage
        from .config import FLAT_GAP_THRESHOLD
        
        gap_pct = ((stock.open_price - stock.prev_close) / stock.prev_close) * 100
        open_equals_low = abs(stock.open_price - current_low) / stock.open_price <= 0.01
        
        if gap_pct >= (FLAT_GAP_THRESHOLD * 100) and open_equals_low:
            print(f"{stock.symbol}: Strong Start conditions met! Gap: {gap_pct:.2f}%, Open≈Low: ₹{current_low:.2f}")
            return True
        return False

    def rank_stocks_by_quality(self) -> None:
        """
        Rank stocks within each category by quality score (ADR + Price)
        Higher ranked stocks get monitoring priority
        """
        try:
            # Lazy import to avoid circular dependencies
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from src.trading.live_trading.stock_scorer import stock_scorer

            # Get all symbols to rank
            all_symbols = []
            for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
                all_symbols.extend([stock.symbol for stock in category])

            if not all_symbols:
                print("No stocks to rank")
                return

            # Preload metadata for all stocks (prev_closes can be empty dict for ranking)
            stock_scorer.preload_metadata(all_symbols, prev_closes={})

            # Rank each category separately
            self._rank_category_stocks(self.vip_stocks, stock_scorer, "VIP")
            self._rank_category_stocks(self.secondary_stocks, stock_scorer, "Secondary")
            self._rank_category_stocks(self.tertiary_stocks, stock_scorer, "Tertiary")

            print("Stock ranking completed - higher ranked stocks will be monitored first")

        except Exception as e:
            print(f"Error ranking stocks: {e}")
            # Continue without ranking - use original order as fallback

    def _rank_category_stocks(self, category_stocks: List[ReversalStock], stock_scorer, category_name: str) -> None:
        """Rank stocks within a specific category"""
        if not category_stocks:
            return

        symbols = [stock.symbol for stock in category_stocks]

        # Get top ranked stocks (no volume data yet, so early_volume=0)
        ranked_stocks = stock_scorer.get_top_stocks(symbols, {symbol: 0 for symbol in symbols}, len(symbols))

        # Update stocks with ranking information
        for rank, score_data in enumerate(ranked_stocks, 1):
            symbol = score_data['symbol']
            total_score = score_data['total_score']

            # Find and update the stock in our category
            for stock in category_stocks:
                if stock.symbol == symbol:
                    stock.quality_rank = rank
                    stock.quality_score = total_score
                    stock.adr_percent = score_data['adr_percent']
                    stock.current_price = score_data['current_price']
                    print(f"  {category_name} #{rank}: {symbol} (Score: {total_score}, ADR: {score_data['adr_percent']:.1f}%)")
                    break

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

        # Import config to get configurable Strong Start gap percentage
        from .config import FLAT_GAP_THRESHOLD
        
        # Condition 1: Gap up (configurable percentage above prev close)
        gap_up = open_price > (prev_close * (1.0 + FLAT_GAP_THRESHOLD))

        # Condition 2: Open ≈ low within 1%
        open_equals_low = abs(open_price - current_low) / open_price <= 0.01

        return gap_up and open_equals_low

    def find_stock_in_watchlist(self, symbol: str) -> Optional[ReversalStock]:
        """Find stock in watchlist by symbol"""
        for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
            for stock in category:
                if stock.symbol == symbol:
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
        print(f"PAPER TRADE [{timestamp}] {symbol}: {action} at ₹{price:.2f} - {reason}")

    def track_opening_prices(self, market_data: Dict[str, Any], current_time: time):
        """
        Track opening prices from first tick after market open
        
        Args:
            market_data: Dict of symbol -> price data
            current_time: Current market time
        """
        from .config import MARKET_OPEN
        
        # Only track opening prices after market opens
        if current_time >= MARKET_OPEN and not self.market_opened:
            self.market_opened = True
            print("Market opened - starting opening price tracking")
        
        if self.market_opened:
            for symbol, data in market_data.items():
                # If we don't have an opening price for this symbol yet, use current LTP as opening price
                if symbol not in self.opening_prices and 'ltp' in data:
                    self.opening_prices[symbol] = data['ltp']
            print(f"Tracked opening price for {symbol}: ₹{data['ltp']:.2f}")

    def execute_market_context_logic(self, market_data: Dict[str, Any], current_time: time, oops_candidates=None, strong_start_candidates=None) -> None:
        """
        Execute market-context-aware trading logic based on OOPS candidate count

        Args:
            market_data: Dict of symbol -> price data
            current_time: Current market time
            oops_candidates: Pre-computed OOPS candidates (optional)
            strong_start_candidates: Pre-computed Strong Start candidates (optional)
        """
        if not self.watchlist_loaded:
            print("Watchlist not loaded - call load_watchlist() first")
            return

        # Step 1: Use provided candidates or identify from market data
        if oops_candidates is not None and strong_start_candidates is not None:
            # Use pre-computed gap analysis - filter Strong Start for 1% movement
            final_oops_candidates = oops_candidates
            final_strong_start_candidates = self._filter_strong_start_for_movement(strong_start_candidates, market_data)
        else:
            # Fallback: analyze gaps from market data (for testing)
            final_oops_candidates = []
            final_strong_start_candidates = []

            for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
                for stock in category:
                    if stock.triggered:
                        continue

                    symbol = stock.symbol
                    if symbol not in market_data:
                        continue

                    data = market_data[symbol]
                    open_price = data.get('open')
                    prev_close = data.get('prev_close')

                    if open_price is None or prev_close is None:
                        continue

                    gap_pct = (open_price - prev_close) / prev_close
                    if gap_pct <= -0.02:  # 2%+ gap down
                        final_oops_candidates.append(stock)
                    elif gap_pct >= 0.02:  # 2%+ gap up
                        final_strong_start_candidates.append(stock)

        oops_count = len(final_oops_candidates)

        # Step 2: Execute based on market context
        triggered_stocks = []

        # Only log market context once per minute to avoid flooding
        import time
        current_minute = int(time.time() // 60)
        if not hasattr(self, '_last_context_log') or self._last_context_log != current_minute:
            self._last_context_log = current_minute
            if oops_count >= 2:
                # GAP DOWN REVERSAL DAY: Execute only OOPS
                print(f"GAP DOWN DAY: {oops_count} OOPS candidates - Executing OOPS only")
            elif oops_count == 1:
                # MIXED DAY: Execute OOPS + fill remaining slot with Strong Start
                print(f"MIXED DAY: 1 OOPS candidate - Executing OOPS + Strong Start")
            else:
                # GAP UP STRENGTH DAY: Execute only Strong Start
                print(f"GAP UP DAY: 0 OOPS candidates - Executing Strong Start only")
        else:
            # Silent execution - no logging to avoid flood
            pass

        # Still execute the logic
        if oops_count >= 2:
            self._execute_oops_only(final_oops_candidates, market_data, triggered_stocks)
        elif oops_count == 1:
            self._execute_oops_plus_ss(final_oops_candidates, final_strong_start_candidates, market_data, current_time, triggered_stocks)
        else:
            self._execute_strong_start_only(final_strong_start_candidates, market_data, current_time, triggered_stocks)

        # Step 3: Execute trades
        self._execute_trades(triggered_stocks)

    def _execute_oops_only(self, oops_candidates, market_data, triggered_stocks):
        """Execute only OOPS triggers (gap down reversal day)"""
        # Sort by quality rank for priority
        oops_candidates_sorted = sorted(oops_candidates, key=lambda x: getattr(x, 'quality_rank', 999))

        for stock in oops_candidates_sorted:
            symbol = stock.symbol
            data = market_data[symbol]
            open_price = data.get('open')
            prev_close = data.get('prev_close')
            current_price = data.get('ltp')

            if self.check_oops_trigger(symbol, open_price, prev_close, current_price):
                triggered_stocks.append({
                    'stock': stock,
                    'method': 'OOPS',
                    'price': current_price
                })

    def _execute_oops_plus_ss(self, oops_candidates, strong_start_candidates, market_data, current_time, triggered_stocks):
        """Execute 1 OOPS + fill remaining slot with Strong Start (mixed day)"""
        # Execute the OOPS candidate first
        stock = oops_candidates[0]  # Only 1 in this scenario
        symbol = stock.symbol
        data = market_data[symbol]
        open_price = data.get('open')
        prev_close = data.get('prev_close')
        current_price = data.get('ltp')

        if self.check_oops_trigger(symbol, open_price, prev_close, current_price):
            triggered_stocks.append({
                'stock': stock,
                'method': 'OOPS',
                'price': current_price
            })

        # Fill remaining slot with best Strong Start
        if self.active_positions < self.max_positions:
            strong_start_candidates_sorted = sorted(strong_start_candidates, key=lambda x: getattr(x, 'quality_rank', 999))

            for stock in strong_start_candidates_sorted:
                symbol = stock.symbol
                data = market_data[symbol]
                open_price = data.get('open')
                prev_close = data.get('prev_close')
                current_low = data.get('low')

                # Check time window for Strong Start (until entry time)
                from .config import MARKET_OPEN, ENTRY_TIME
                market_open = MARKET_OPEN
                entry_time = ENTRY_TIME
                if market_open <= current_time <= entry_time:
                    if self.check_strong_start_trigger(symbol, open_price, prev_close, current_low):
                        triggered_stocks.append({
                            'stock': stock,
                            'method': 'Strong Start',
                            'price': data.get('ltp')
                        })
                        break  # Take only the best one

    def _execute_strong_start_only(self, strong_start_candidates, market_data, current_time, triggered_stocks):
        """Execute only Strong Start triggers (gap up strength day)"""
        # Check time window for Strong Start (until entry time)
        from .config import MARKET_OPEN, ENTRY_TIME
        market_open = MARKET_OPEN
        entry_time = ENTRY_TIME

        if not (market_open <= current_time <= entry_time):
            return  # Strong Start only in confirmation window

        # Sort by quality rank and execute
        strong_start_candidates_sorted = sorted(strong_start_candidates, key=lambda x: getattr(x, 'quality_rank', 999))

        for stock in strong_start_candidates_sorted:
            symbol = stock.symbol
            data = market_data[symbol]
            open_price = data.get('open')
            prev_close = data.get('prev_close')
            current_low = data.get('low')

            if self.check_strong_start_trigger(symbol, open_price, prev_close, current_low):
                triggered_stocks.append({
                    'stock': stock,
                    'method': 'Strong Start',
                    'price': data.get('ltp')
                })

    def _execute_trades(self, triggered_stocks):
        """Execute the triggered trades"""
        for trigger in triggered_stocks:
            if self.active_positions >= self.max_positions:
                break

            stock = trigger['stock']
            if stock.triggered:
                continue

            # Execute entry
            stock.triggered = True
            stock.entry_price = trigger['price']
            stock.stop_loss = trigger['price'] * 0.96  # 4% below

            self.active_positions += 1

            # Log paper trade
            self.log_paper_trade(
                stock.symbol,
                "ENTRY",
                trigger['price'],
                f"{trigger['method']}"
            )

    def reset_daily_state(self) -> None:
        """Reset daily trading state"""
        self.active_positions = 0

        # Reset all stock triggers but keep classifications
        for category in [self.vip_stocks, self.secondary_stocks, self.tertiary_stocks]:
            for stock in category:
                stock.triggered = False
                stock.entry_price = None
                stock.stop_loss = None

        print("Daily reversal trading state reset")

    def _filter_strong_start_for_movement(self, strong_start_candidates, market_data):
        """Filter Strong Start candidates that have moved >1% from opening price"""
        filtered_candidates = []

        for stock in strong_start_candidates:
            symbol = stock.symbol
            required_target = getattr(stock, 'required_move_target', None)

            if required_target is None:
                continue  # No movement requirement set

            if symbol in market_data:
                current_price = market_data[symbol].get('ltp')
                opening_price = market_data[symbol].get('open')

                if current_price is not None and opening_price is not None:
                    # Check if moved >1% from opening price
                    if current_price >= required_target:
                        filtered_candidates.append(stock)
                        print(f"{symbol}: Strong Start qualified - moved to ₹{current_price:.2f} (>1% from ₹{opening_price:.2f})")
                    else:
                        print(f"{symbol}: Strong Start rejected - only at ₹{current_price:.2f} (needs ₹{required_target:.2f} for >1% move)")
                else:
                    print(f"{symbol}: Missing price data for Strong Start check")

        return filtered_candidates
