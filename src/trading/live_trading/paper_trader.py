"""
Paper Trader - Logs trades for paper trading (no real orders)
"""

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Optional, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
from config import *
from continuation_stock_monitor import StockState

logger = logging.getLogger(__name__)


class PaperTrader:
    """Handles paper trading operations and logging"""

    def __init__(self, session_name: str = None):
        self.session_name = session_name or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.trades_log = []
        self.positions = {}  # instrument_key -> position data

        # Create logs directory
        os.makedirs(TRADE_LOG_DIR, exist_ok=True)

        # Setup logging
        self.setup_logging()

        logger.info(f"Paper Trader initialized for session: {self.session_name}")

    def setup_logging(self):
        """Setup logging to file"""
        log_file = os.path.join(TRADE_LOG_DIR, f"paper_trading_{self.session_name}.log")

        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)

        # Add to logger
        logger.addHandler(file_handler)

    def log_entry(self, stock: StockState, entry_price: float, entry_time: datetime):
        """Log entry trade"""
        trade = {
            'timestamp': entry_time.isoformat(),
            'type': 'ENTRY',
            'symbol': stock.symbol,
            'instrument_key': stock.instrument_key,
            'entry_price': round(entry_price, 2),
            'entry_high': round(stock.entry_high, 2),
            'stop_loss': round(stock.entry_sl, 2),
            'open_price': round(stock.open_price, 2),
            'previous_close': round(stock.previous_close, 2),
            'gap_pct': round((stock.open_price - stock.previous_close) / stock.previous_close * 100, 2),
            'session': self.session_name
        }

        self.trades_log.append(trade)

        # Store position
        self.positions[stock.instrument_key] = {
            'entry_price': entry_price,
            'entry_time': entry_time,
            'entry_high': stock.entry_high,
            'stop_loss': stock.entry_sl,
            'symbol': stock.symbol
        }

        # Log to file
        logger.info(f"PAPER ENTRY: {stock.symbol} at {entry_price:.2f} (High: {stock.entry_high:.2f}, SL: {stock.entry_sl:.2f})")

        # Save to JSON
        self._save_trades()

    def log_exit(self, stock: StockState, exit_price: float, exit_time: datetime, reason: str):
        """Log exit trade"""
        position = self.positions.get(stock.instrument_key)
        if not position:
            logger.warning(f"No position found for {stock.symbol} to exit")
            return

        pnl = round((exit_price - position['entry_price']) / position['entry_price'] * 100, 2)

        trade = {
            'timestamp': exit_time.isoformat(),
            'type': 'EXIT',
            'symbol': stock.symbol,
            'instrument_key': stock.instrument_key,
            'exit_price': round(exit_price, 2),
            'entry_price': round(position['entry_price'], 2),
            'pnl_pct': pnl,
            'pnl_abs': round(exit_price - position['entry_price'], 2),
            'hold_time_minutes': round((exit_time - position['entry_time']).total_seconds() / 60, 1),
            'exit_reason': reason,
            'stop_loss': round(position['stop_loss'], 2),
            'session': self.session_name
        }

        self.trades_log.append(trade)

        # Remove position
        del self.positions[stock.instrument_key]

        # Log to file
        logger.info(f"PAPER EXIT: {stock.symbol} at {exit_price:.2f} | P&L: {pnl:.2f}% | Reason: {reason}")

        # Save to JSON
        self._save_trades()

    def log_rejection(self, stock: StockState, reason: str):
        """Log stock rejection"""
        rejection = {
            'timestamp': datetime.now().isoformat(),
            'type': 'REJECTION',
            'symbol': stock.symbol,
            'instrument_key': stock.instrument_key,
            'reason': reason,
            'open_price': round(stock.open_price, 2) if stock.open_price else None,
            'daily_high': round(stock.daily_high, 2) if stock.daily_high != float('-inf') else None,
            'daily_low': round(stock.daily_low, 2) if stock.daily_low != float('inf') else None,
            'previous_close': round(stock.previous_close, 2),
            'session': self.session_name
        }

        self.trades_log.append(rejection)

        logger.info(f"PAPER REJECT: {stock.symbol} | Reason: {reason}")

        # Save to JSON
        self._save_trades()

    def log_session_summary(self, summary: Dict):
        """Log session summary"""
        session_summary = {
            'timestamp': datetime.now().isoformat(),
            'type': 'SESSION_SUMMARY',
            'session': self.session_name,
            'summary': summary
        }

        self.trades_log.append(session_summary)

        logger.info(f"SESSION SUMMARY: {summary}")

        # Final save
        self._save_trades()

    def _save_trades(self):
        """Save trades to JSON file"""
        try:
            json_file = os.path.join(TRADE_LOG_DIR, f"paper_trades_{self.session_name}.json")

            with open(json_file, 'w') as f:
                json.dump(self.trades_log, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving trades to JSON: {e}")

    def get_session_stats(self) -> Dict:
        """Get session statistics"""
        entries = [t for t in self.trades_log if t['type'] == 'ENTRY']
        exits = [t for t in self.trades_log if t['type'] == 'EXIT']
        rejections = [t for t in self.trades_log if t['type'] == 'REJECTION']

        total_pnl = sum(t.get('pnl_pct', 0) for t in exits)

        winning_trades = len([t for t in exits if t.get('pnl_pct', 0) > 0])
        losing_trades = len([t for t in exits if t.get('pnl_pct', 0) <= 0])

        return {
            'session': self.session_name,
            'total_entries': len(entries),
            'total_exits': len(exits),
            'total_rejections': len(rejections),
            'open_positions': len(self.positions),
            'total_pnl_pct': round(total_pnl, 2),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(winning_trades / max(len(exits), 1) * 100, 1),
            'avg_trade_duration_min': round(sum(t.get('hold_time_minutes', 0) for t in exits) / max(len(exits), 1), 1)
        }

    def export_trades_csv(self, filename: str = None):
        """Export trades to CSV"""
        if not filename:
            filename = f"paper_trades_{self.session_name}.csv"

        try:
            import pandas as pd

            df = pd.DataFrame(self.trades_log)
            csv_path = os.path.join(TRADE_LOG_DIR, filename)
            df.to_csv(csv_path, index=False)

            logger.info(f"Trades exported to CSV: {csv_path}")

        except ImportError:
            logger.warning("pandas not available for CSV export")
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")

    def close(self):
        """Close paper trader and save final state"""
        # Log final session stats
        stats = self.get_session_stats()
        self.log_session_summary(stats)

        logger.info(f"Paper Trader closed for session: {self.session_name}")
        logger.info(f"Session Stats: {stats}")
