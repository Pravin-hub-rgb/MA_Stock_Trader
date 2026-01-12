"""
Market Breadth Analyzer
Generates daily market breadth metrics from cached stock data
"""

import sys
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import pickle

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton, QProgressBar,
    QTextEdit, QSplitter, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from src.utils.cache_manager import cache_manager
from src.scanner.color_utils import get_up_4_5_color

logger = logging.getLogger(__name__)


class BreadthCacheManager:
    """Manages caching of breadth calculation results"""

    def __init__(self):
        self.cache_dir = Path('data/breadth_cache')
        self.breadth_cache_file = self.cache_dir / 'breadth_data.pkl'
        self.breadth_cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Dict]:
        """Load cached breadth data"""
        try:
            if self.breadth_cache_file.exists():
                with open(self.breadth_cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load breadth cache: {e}")
        return {}

    def _save_cache(self):
        """Save breadth cache to disk"""
        try:
            self.cache_dir.mkdir(exist_ok=True)
            with open(self.breadth_cache_file, 'wb') as f:
                pickle.dump(self.breadth_cache, f)
        except Exception as e:
            logger.error(f"Failed to save breadth cache: {e}")

    def get_cached_breadth(self, date_key: str) -> Optional[Dict]:
        """Get cached breadth data for a specific date"""
        return self.breadth_cache.get(date_key)

    def update_breadth_cache(self, date_key: str, breadth_data: Dict):
        """Update cache with new breadth data"""
        self.breadth_cache[date_key] = breadth_data
        self._save_cache()

    def get_all_cached_dates(self) -> List[str]:
        """Get all dates that have cached breadth data"""
        return list(self.breadth_cache.keys())

    def needs_update(self, target_date: date, all_stock_symbols: List[str]) -> bool:
        """Check if breadth needs to be recalculated for this date"""
        date_key = target_date.strftime('%Y-%m-%d')

        # Always recalculate recent dates to ensure latest data
        # Only keep cached results for dates more than 7 days old
        today = date.today()
        if (today - target_date).days <= 7:
            return True

        # For older dates, check if we have cached data
        return date_key not in self.breadth_cache


# Global breadth cache manager
breadth_cache = BreadthCacheManager()


class BreadthCalculator(QThread):
    """Worker thread for calculating breadth metrics"""
    progress = pyqtSignal(str)  # Progress message
    finished = pyqtSignal(list)  # Results list

    def __init__(self):
        super().__init__()

    def run(self):
        """Calculate market breadth metrics"""
        try:
            results = self._calculate_breadth()
            self.finished.emit(results)
        except Exception as e:
            logger.error(f"Breadth calculation failed: {e}")
            self.finished.emit([])

    def _calculate_breadth(self) -> List[Dict]:
        """Calculate breadth metrics for all available dates using caching"""
        self.progress.emit("Loading cached stock data...")

        # Get all cached stock files
        cache_dir = Path('data/cache')
        cached_files = list(cache_dir.glob('*.pkl'))

        if not cached_files:
            raise Exception("No cached stock data found")

        self.progress.emit(f"Found {len(cached_files)} cached stocks")

        # Load all stock data
        all_stocks_data = {}
        all_stock_symbols = []
        for i, cache_file in enumerate(cached_files[:2000]):  # Limit for testing
            symbol = cache_file.stem
            try:
                df = cache_manager.load_cached_data(symbol)
                if df is not None and not df.empty:
                    all_stocks_data[symbol] = df
                    all_stock_symbols.append(symbol)
                if (i + 1) % 500 == 0:
                    self.progress.emit(f"Loaded {i + 1} stocks...")
            except Exception as e:
                continue

        available_stocks = len(all_stocks_data)
        self.progress.emit(f"Loaded {available_stocks} stocks with data")

        if available_stocks == 0:
            raise Exception("No valid stock data found")

        # Find common date range (dates where most stocks have data)
        all_dates = set()
        for df in all_stocks_data.values():
            all_dates.update(df.index.date)

        # Filter to only weekdays (Monday=0 to Friday=4, exclude Saturday=5, Sunday=6)
        weekday_dates = {d for d in all_dates if d.weekday() < 5}

        # Sort dates
        sorted_dates = sorted(weekday_dates)

        # Check cache and calculate only needed dates
        breadth_results = {}
        dates_to_calculate = []

        # First, load all cached results into a dict
        cached_dates = breadth_cache.get_all_cached_dates()
        self.progress.emit(f"Found {len(cached_dates)} cached dates")

        for date_key in cached_dates:
            try:
                cached_data = breadth_cache.get_cached_breadth(date_key)
                if cached_data:
                    breadth_results[date_key] = {
                        'date': date_key,
                        'up_4_5_pct': cached_data.get('up_4_5', 0),
                        'down_4_5_pct': cached_data.get('down_4_5', 0),
                        'up_20_pct_5d': cached_data.get('up_20_5d', 0),
                        'down_20_pct_5d': cached_data.get('down_20_5d', 0),
                        'above_20ma': cached_data.get('above_20ma', 0),
                        'below_20ma': cached_data.get('below_20ma', 0),
                        'above_50ma': cached_data.get('above_50ma', 0),
                        'below_50ma': cached_data.get('below_50ma', 0)
                    }
            except Exception as e:
                continue

        self.progress.emit(f"Loaded {len(breadth_results)} results from cache")

        # Find dates that need calculation
        for target_date in sorted_dates:
            date_key = target_date.strftime('%Y-%m-%d')
            if breadth_cache.needs_update(target_date, all_stock_symbols):
                dates_to_calculate.append(target_date)

        self.progress.emit(f"Using {len(breadth_results)} cached results, calculating {len(dates_to_calculate)} new dates")

        # Calculate new dates
        total_dates = len(dates_to_calculate)
        for i, target_date in enumerate(dates_to_calculate):
            if i % 5 == 0:
                self.progress.emit(f"Calculating date {i+1}/{total_dates}: {target_date}")

            # Count stocks meeting each criterion
            counts = self._calculate_date_breadth(all_stocks_data, target_date)

            if counts:  # Only add if we have data
                result = {
                    'date': target_date.strftime('%Y-%m-%d'),
                    'up_4_5_pct': counts['up_4_5'],
                    'down_4_5_pct': counts['down_4_5'],
                    'up_20_pct_5d': counts['up_20_5d'],
                    'down_20_pct_5d': counts['down_20_5d'],
                    'above_20ma': counts['above_20ma'],
                    'below_20ma': counts['below_20ma'],
                    'above_50ma': counts['above_50ma'],
                    'below_50ma': counts['below_50ma']
                }
                breadth_results[date_key] = result

                # Cache the result
                breadth_cache.update_breadth_cache(target_date.strftime('%Y-%m-%d'), counts)

        # Convert dict to list and sort by date (most recent first)
        breadth_results_list = list(breadth_results.values())
        breadth_results_list.sort(key=lambda x: x['date'], reverse=True)

        # Always include the most recent trading day, even if incomplete
        today = date.today()
        recent_dates = []
        for i in range(7):  # Check last 7 days
            check_date = today - timedelta(days=i)
            if check_date.weekday() < 5:  # Weekday
                recent_dates.append(check_date)

        for recent_date in recent_dates:
            date_key = recent_date.strftime('%Y-%m-%d')
            if date_key not in breadth_results:
                # Try to calculate this date even if it might be incomplete
                counts = self._calculate_date_breadth(all_stocks_data, recent_date)
                if counts:  # At least some data
                    result = {
                        'date': date_key,
                        'up_4_5_pct': counts['up_4_5'],
                        'down_4_5_pct': counts['down_4_5'],
                        'up_20_pct_5d': counts['up_20_5d'],
                        'down_20_pct_5d': counts['down_20_5d'],
                        'above_20ma': counts['above_20ma'],
                        'below_20ma': counts['below_20ma'],
                        'above_50ma': counts['above_50ma'],
                        'below_50ma': counts['below_50ma']
                    }
                    breadth_results[date_key] = result
                    breadth_results_list.insert(0, result)  # Add to front

        self.progress.emit(f"Completed breadth analysis: {len(breadth_results_list)} total dates (cached + calculated)")
        return breadth_results_list

    def _calculate_date_breadth(self, all_stocks_data: Dict[str, pd.DataFrame], target_date: date) -> Dict[str, int]:
        """Calculate breadth counts for a specific date"""
        counts = {
            'up_4_5': 0,
            'down_4_5': 0,
            'up_20_5d': 0,
            'down_20_5d': 0,
            'above_20ma': 0,
            'below_20ma': 0,
            'above_50ma': 0,
            'below_50ma': 0
        }

        stocks_with_data = 0

        for symbol, df in all_stocks_data.items():
            try:
                # Check if stock has data for this date
                if target_date not in [idx.date() for idx in df.index]:
                    continue

                # Get data for this date
                date_data = df[df.index.date == target_date]
                if date_data.empty:
                    continue

                latest = date_data.iloc[-1]
                stocks_with_data += 1

                # Calculate metrics
                price_change = latest.get('price_change', 0)
                price_change_5d = latest.get('price_change_5d', 0)
                close = latest.get('close', 0)
                ma_20 = latest.get('ma_20', None)

                # 4.5% daily change
                if price_change >= 0.045:
                    counts['up_4_5'] += 1
                elif price_change <= -0.045:
                    counts['down_4_5'] += 1

                # 20% in 5 days
                if price_change_5d >= 0.20:
                    counts['up_20_5d'] += 1
                elif price_change_5d <= -0.20:
                    counts['down_20_5d'] += 1

                # 20-day MA (only if we have MA data)
                if ma_20 is not None and not pd.isna(ma_20):
                    if close >= ma_20:
                        counts['above_20ma'] += 1
                    else:
                        counts['below_20ma'] += 1

                # 50-day MA (calculate on-the-fly)
                if len(df) >= 50:
                    # Get last 50 days ending on target_date
                    date_idx = pd.Timestamp(target_date)
                    if date_idx in df.index:
                        end_idx = df.index.get_loc(date_idx)
                        if end_idx >= 49:
                            ma_50_window = df.iloc[end_idx-49:end_idx+1]['close'].mean()
                            if close >= ma_50_window:
                                counts['above_50ma'] += 1
                            else:
                                counts['below_50ma'] += 1

            except Exception as e:
                continue

        # Only return counts if we have sufficient data
        if stocks_with_data >= 100:  # Minimum threshold
            return counts
        return {}


class BreadthAnalyzerGUI(QMainWindow):
    """GUI for displaying market breadth analysis"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MA Stock Trader - Market Breadth Analyzer")
        self.setGeometry(100, 100, 1000, 700)

        self.results_data = []
        self.init_ui()
        self.start_analysis()



    def init_ui(self):
        """Initialize the user interface"""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Market Breadth Analysis")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Progress area
        progress_group = QWidget()
        progress_layout = QVBoxLayout()

        self.progress_label = QLabel("Initializing...")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)

        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(9)
        self.results_table.setHorizontalHeaderLabels([
            "Date", "Up 4.5%", "Down 4.5%", "Up 20% 5d", "Down 20% 5d",
            "Above 20MA", "Below 20MA", "Above 50MA", "Below 50MA"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)

        # Style the table with dark theme - removed item background styling to allow programmatic colors
        self.results_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #666666;
                background-color: #1a1a1a;
                alternate-background-color: #2a2a2a;
                border: 2px solid #888888;
                border-radius: 3px;
                color: #ffffff;
                selection-background-color: #444444;
            }
            QTableWidget::item {
                border: 1px solid #555555;
                padding: 5px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background-color: #555555 !important;
                color: #ffffff !important;
            }
            QHeaderView::section {
                background-color: #333333;
                border: 1px solid #888888;
                padding: 8px;
                font-weight: bold;
                text-align: center;
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: #333333;
            }
        """)

        main_layout.addWidget(self.results_table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_csv)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        self.refresh_btn = QPushButton("Refresh Analysis")
        self.refresh_btn.clicked.connect(self.start_analysis)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def start_analysis(self):
        """Start breadth analysis"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting analysis...")
        self.export_btn.setEnabled(False)
        self.results_table.setRowCount(0)

        # Start worker thread
        self.worker = BreadthCalculator()
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.start()

    def update_progress(self, message: str):
        """Update progress display"""
        self.progress_label.setText(message)
        self.status_bar.showMessage(message)

        # Update progress bar based on message
        if "Loaded" in message and "stocks" in message:
            self.progress_bar.setValue(25)
        elif "Processing date" in message:
            self.progress_bar.setValue(75)
        elif "Completed" in message:
            self.progress_bar.setValue(100)

    def analysis_finished(self, results: List[Dict]):
        """Handle analysis completion"""
        self.results_data = results

        if results:
            self.display_results(results)
            self.export_btn.setEnabled(True)
            self.status_bar.showMessage(f"Analysis complete: {len(results)} dates analyzed")

            # Auto-export
            self.export_csv(silent=True)
        else:
            QMessageBox.warning(self, "Analysis Failed", "No breadth data could be calculated")
            self.status_bar.showMessage("Analysis failed - no data")

    def display_results(self, results: List[Dict]):
        """Display results in table"""
        self.results_table.setRowCount(len(results))

        for row, result in enumerate(results):
            # Date
            date_item = QTableWidgetItem(result['date'])
            date_item.setFlags(date_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(row, 0, date_item)

            # Breadth counts
            for col, key in enumerate([
                'up_4_5_pct', 'down_4_5_pct', 'up_20_pct_5d', 'down_20_pct_5d',
                'above_20ma', 'below_20ma', 'above_50ma', 'below_50ma'
            ], 1):
                value = result.get(key, 0)
                count_item = QTableWidgetItem(str(value))
                count_item.setFlags(count_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Apply color coding to Up 4.5% column (col 1)
                if col == 1 and key == 'up_4_5_pct':
                    background_color = get_up_4_5_color(value)
                    count_item.setData(Qt.ItemDataRole.BackgroundRole, background_color)
                    count_item.setForeground(QColor(0, 0, 0))  # Black text



                self.results_table.setItem(row, col, count_item)

        self.results_table.resizeColumnsToContents()
        # Force refresh to show colors
        self.results_table.update()
        self.results_table.repaint()

    def export_csv(self, silent: bool = False):
        """Export results to CSV"""
        if not self.results_data:
            if not silent:
                QMessageBox.warning(self, "Export Error", "No data to export")
            return

        # Create output directory
        output_dir = Path('market_breadth_reports')
        output_dir.mkdir(exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f'market_breadth_{timestamp}.csv'

        try:
            # Convert to DataFrame and save
            df = pd.DataFrame(self.results_data)
            df.to_csv(filename, index=False)

            if not silent:
                QMessageBox.information(self, "Export Complete",
                                      f"Results exported to {filename}")

            self.status_bar.showMessage(f"Exported to {filename}")

        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {str(e)}")
            logger.error(f"Export failed: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = BreadthAnalyzerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
