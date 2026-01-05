"""
GUI for Market Scanner
Provides a user interface for running scans and managing watchlists
"""

import sys
import logging
from datetime import date, datetime
from typing import List, Dict
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QComboBox,
    QDateEdit, QCheckBox, QGroupBox, QSplitter, QTextEdit, QMessageBox,
    QFileDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from src.scanner.scanner import scanner
from src.utils.database import db

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for running scans"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(list, str)
    
    def __init__(self, scan_type: str, scan_date: date):
        super().__init__()
        self.scan_type = scan_type
        self.scan_date = scan_date
    
    def run(self):
        """Run the scan in background"""
        try:
            if self.scan_type == 'continuation':
                results = scanner.run_continuation_scan(self.scan_date)
                self.finished.emit(results, "Continuation scan completed")
            else:
                results = scanner.run_reversal_scan(self.scan_date)
                self.finished.emit(results, "Reversal scan completed")
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            self.finished.emit([], f"Scan failed: {str(e)}")


class ScannerGUI(QMainWindow):
    """Main GUI window for the scanner"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MA Stock Trader - Scanner")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()
        self.load_scan_results()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("MA Stock Trader - Market Scanner")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Scan Date:"))
        self.date_edit = QDateEdit(date.today())
        self.date_edit.setCalendarPopup(True)
        date_layout.addWidget(self.date_edit)
        
        header_layout.addLayout(date_layout)
        main_layout.addLayout(header_layout)
        
        # Control panel
        control_group = QGroupBox("Scan Controls")
        control_layout = QHBoxLayout()
        
        # Scan type selection
        scan_type_layout = QVBoxLayout()
        scan_type_layout.addWidget(QLabel("Scan Type:"))
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems(["Continuation", "Reversal"])
        scan_type_layout.addWidget(self.scan_type_combo)
        control_layout.addLayout(scan_type_layout)
        
        # Scan button
        self.scan_button = QPushButton("Run Scan")
        self.scan_button.clicked.connect(self.run_scan)
        control_layout.addWidget(self.scan_button)
        
        # Progress bar
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(QLabel("Progress:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)
        control_layout.addLayout(progress_layout)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Results area
        results_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Results table
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Symbol", "Score", "MA Angle", "Distance from High", "ADR %", "Notes"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.cellDoubleClicked.connect(self.add_to_watchlist)
        
        left_layout.addWidget(QLabel("Scan Results:"))
        left_layout.addWidget(self.results_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        self.add_to_watchlist_btn = QPushButton("Add to Watchlist")
        self.add_to_watchlist_btn.clicked.connect(self.add_selected_to_watchlist)
        action_layout.addWidget(self.add_to_watchlist_btn)
        
        self.export_btn = QPushButton("Export Results")
        self.export_btn.clicked.connect(self.export_results)
        action_layout.addWidget(self.export_btn)
        
        left_layout.addLayout(action_layout)
        left_panel.setLayout(left_layout)
        
        # Right panel: Details and watchlists
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Details section
        details_group = QGroupBox("Stock Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        right_layout.addWidget(details_group)
        
        # Watchlists section
        watchlist_group = QGroupBox("Watchlists")
        watchlist_layout = QVBoxLayout()
        
        self.watchlist_combo = QComboBox()
        self.load_watchlists()
        watchlist_layout.addWidget(self.watchlist_combo)
        
        watchlist_buttons_layout = QHBoxLayout()
        self.create_watchlist_btn = QPushButton("Create Watchlist")
        self.create_watchlist_btn.clicked.connect(self.create_watchlist)
        watchlist_buttons_layout.addWidget(self.create_watchlist_btn)
        
        self.view_watchlist_btn = QPushButton("View Watchlist")
        self.view_watchlist_btn.clicked.connect(self.view_watchlist)
        watchlist_buttons_layout.addWidget(self.view_watchlist_btn)
        
        watchlist_layout.addLayout(watchlist_buttons_layout)
        
        # Watchlist items table
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(4)
        self.watchlist_table.setHorizontalHeaderLabels(["Symbol", "Name", "Sector", "Added Date"])
        self.watchlist_table.horizontalHeader().setStretchLastSection(True)
        
        watchlist_layout.addWidget(QLabel("Watchlist Items:"))
        watchlist_layout.addWidget(self.watchlist_table)
        
        watchlist_group.setLayout(watchlist_layout)
        right_layout.addWidget(watchlist_group)
        
        right_panel.setLayout(right_layout)
        
        # Add panels to splitter
        results_splitter.addWidget(left_panel)
        results_splitter.addWidget(right_panel)
        results_splitter.setSizes([600, 400])
        
        main_layout.addWidget(results_splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
    
    def run_scan(self):
        """Run the selected scan"""
        scan_type = self.scan_type_combo.currentText().lower()
        scan_date = self.date_edit.date().toPyDate()
        
        self.scan_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Running {scan_type} scan for {scan_date}...")
        
        # Start worker thread
        self.worker = ScanWorker(scan_type, scan_date)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()
    
    def update_progress(self, value: int, message: str):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
    
    def scan_finished(self, results: List[Dict], message: str):
        """Handle scan completion"""
        self.scan_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_bar.showMessage(message)
        
        if results:
            self.display_results(results)
            QMessageBox.information(self, "Scan Complete", 
                                  f"{message}\nFound {len(results)} candidates")
        else:
            QMessageBox.warning(self, "Scan Complete", 
                              f"{message}\nNo candidates found")
    
    def display_results(self, results: List[Dict]):
        """Display scan results in table"""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Symbol
            symbol_item = QTableWidgetItem(result['symbol'])
            symbol_item.setFlags(symbol_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 0, symbol_item)
            
            # Score (only for reversal scans)
            if 'score' in result:
                score_item = QTableWidgetItem(f"{result['score']}")
            else:
                score_item = QTableWidgetItem("N/A")
            score_item.setFlags(score_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 1, score_item)
            
            # MA Angle
            ma_angle = result.get('ma_angle', 0)
            ma_item = QTableWidgetItem(f"{ma_angle:.2f}")
            ma_item.setFlags(ma_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 2, ma_item)
            
            # Distance from High
            distance = result.get('distance_from_high', 0)
            distance_item = QTableWidgetItem(f"{distance*100:.2f}%")
            distance_item.setFlags(distance_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 3, distance_item)
            
            # ADR %
            adr = result.get('adr_percent', 0)
            adr_item = QTableWidgetItem(f"{adr:.2f}%")
            adr_item.setFlags(adr_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 4, adr_item)
            
            # Notes
            notes = result.get('notes', '')
            notes_item = QTableWidgetItem(notes)
            notes_item.setFlags(notes_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.results_table.setItem(row, 5, notes_item)
        
        self.results_table.resizeColumnsToContents()
    
    def add_to_watchlist(self, row: int, column: int):
        """Add selected stock to watchlist"""
        symbol = self.results_table.item(row, 0).text()
        score = self.results_table.item(row, 1).text()
        
        watchlist_name = self.watchlist_combo.currentText()
        if not watchlist_name:
            QMessageBox.warning(self, "Error", "Please select a watchlist")
            return
        
        # Get stock ID
        stock_id = db.get_stock_id(symbol)
        if stock_id is None:
            QMessageBox.warning(self, "Error", f"Stock {symbol} not found in database")
            return
        
        # Add to watchlist
        try:
            # Find watchlist ID
            watchlists = db.get_watchlists()
            watchlist_id = None
            for wl in watchlists:
                if wl['name'] == watchlist_name:
                    watchlist_id = wl['id']
                    break
            
            if watchlist_id:
                db.add_to_watchlist(
                    watchlist_id, 
                    stock_id, 
                    scan_source=self.scan_type_combo.currentText().lower(),
                    manual_notes=f"Score: {score}"
                )
                QMessageBox.information(self, "Success", f"Added {symbol} to {watchlist_name}")
            else:
                QMessageBox.warning(self, "Error", "Watchlist not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add to watchlist: {str(e)}")
    
    def add_selected_to_watchlist(self):
        """Add selected rows to watchlist"""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "Error", "Please select rows to add")
            return
        
        watchlist_name = self.watchlist_combo.currentText()
        if not watchlist_name:
            QMessageBox.warning(self, "Error", "Please select a watchlist")
            return
        
        added_count = 0
        for row in selected_rows:
            symbol = self.results_table.item(row, 0).text()
            score = self.results_table.item(row, 1).text()
            
            stock_id = db.get_stock_id(symbol)
            if stock_id:
                try:
                    # Find watchlist ID
                    watchlists = db.get_watchlists()
                    watchlist_id = None
                    for wl in watchlists:
                        if wl['name'] == watchlist_name:
                            watchlist_id = wl['id']
                            break
                    
                    if watchlist_id:
                        db.add_to_watchlist(
                            watchlist_id, 
                            stock_id, 
                            scan_source=self.scan_type_combo.currentText().lower(),
                            manual_notes=f"Score: {score}"
                        )
                        added_count += 1
                except Exception as e:
                    logger.error(f"Failed to add {symbol}: {e}")
        
        QMessageBox.information(self, "Success", f"Added {added_count} stocks to {watchlist_name}")
    
    def export_results(self):
        """Export results to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    # Write header
                    f.write("Symbol,Score,MA_Angle,Distance_from_High,ADR_Percent,Notes\n")
                    
                    # Write data
                    for row in range(self.results_table.rowCount()):
                        row_data = []
                        for col in range(self.results_table.columnCount()):
                            item = self.results_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        f.write(",".join(row_data) + "\n")
                
                QMessageBox.information(self, "Export Complete", f"Results exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")
    
    def load_watchlists(self):
        """Load watchlists into combo box"""
        self.watchlist_combo.clear()
        watchlists = db.get_watchlists()
        for wl in watchlists:
            self.watchlist_combo.addItem(wl['name'])
    
    def create_watchlist(self):
        """Create a new watchlist"""
        from PyQt6.QtWidgets import QInputDialog
        
        watchlist_name, ok = QInputDialog.getText(
            self, "Create Watchlist", "Enter watchlist name:"
        )
        
        if ok and watchlist_name:
            try:
                watchlist_type = "next_day_trades"  # Default type
                db.create_watchlist(watchlist_name, watchlist_type)
                self.load_watchlists()
                QMessageBox.information(self, "Success", f"Created watchlist: {watchlist_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create watchlist: {str(e)}")
    
    def view_watchlist(self):
        """View selected watchlist"""
        watchlist_name = self.watchlist_combo.currentText()
        if not watchlist_name:
            return
        
        try:
            # Find watchlist ID
            watchlists = db.get_watchlists()
            watchlist_id = None
            for wl in watchlists:
                if wl['name'] == watchlist_name:
                    watchlist_id = wl['id']
                    break
            
            if watchlist_id:
                items = db.get_watchlist(watchlist_id)
                self.display_watchlist_items(items)
            else:
                QMessageBox.warning(self, "Error", "Watchlist not found")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load watchlist: {str(e)}")
    
    def display_watchlist_items(self, items: List[Dict]):
        """Display watchlist items in table"""
        self.watchlist_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            # Symbol
            symbol_item = QTableWidgetItem(item['symbol'])
            symbol_item.setFlags(symbol_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.watchlist_table.setItem(row, 0, symbol_item)
            
            # Name
            name_item = QTableWidgetItem(item['name'])
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.watchlist_table.setItem(row, 1, name_item)
            
            # Sector
            sector_item = QTableWidgetItem(item.get('sector', ''))
            sector_item.setFlags(sector_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.watchlist_table.setItem(row, 2, sector_item)
            
            # Added Date
            date_item = QTableWidgetItem(item['added_date'])
            date_item.setFlags(date_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.watchlist_table.setItem(row, 3, date_item)
        
        self.watchlist_table.resizeColumnsToContents()
    
    def load_scan_results(self):
        """Load recent scan results"""
        try:
            results = db.get_scan_results(days=7)
            if results:
                # Group by scan type and date
                continuation_results = [r for r in results if r['scan_type'] == 'continuation']
                reversal_results = [r for r in results if r['scan_type'] == 'reversal']
                
                logger.info(f"Loaded {len(continuation_results)} continuation and {len(reversal_results)} reversal results")
        except Exception as e:
            logger.error(f"Failed to load scan results: {e}")


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = ScannerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
