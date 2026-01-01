# Custom Stock Scanner Software: Requirements and Implementation Guide

## Overview
This document outlines the specifications for building a custom stock scanning software inspired by Spider Iris, a commercial tool for technical analysis and stock screening in the Indian markets (primarily NSE). The goal is to create a **free, open-source equivalent** that focuses on **daily timeframe (EOD) OHLCV data** (Open, High, Low, Close, Volume) for running scans after market hours to inform next-day trades. The software will be a **desktop application** (not web-based) for fast, responsive performance, similar to Spider Iris.

The software will:
- Fetch and cache data from free sources.
- Allow users to define and run scans (e.g., stocks at 52-week high).
- Display results in a list/table with quick chart viewing.
- Support saving and managing watchlists.
- Ensure quick scans by using local cached data after an initial/prep update.

This is targeted for personal use, built in **Python** (free and versatile), and will run on Windows/Mac/Linux. No paid tools or subscriptions are required.

**Key Principles**:
- **Free Everything**: Use open-source libraries and free data APIs.
- **Efficiency**: Minimize web calls; cache data locally for speed.
- **User-Friendly**: Desktop app feel with GUI, progress indicators, and intuitive controls.
- **Customizable**: Easy to add new scan conditions over time.
- **Data Focus**: Only daily OHLCV; no real-time or intraday.

## Target Users and Use Case
- Users: Individual traders like the requester, who have an Upstox account (optional fallback) but prefer free data.
- Primary Workflow:
  1. Open the app after market close (e.g., 4 PM IST).
  2. App performs a quick "prep/update" to fetch any new EOD data.
  3. User selects or defines a scan (e.g., "52-week highs").
  4. App scans all NSE stocks (or a watchlist) instantly using local data.
  5. Results show in a table; click any stock to view its chart.
  6. Save results as a watchlist, add/remove stocks, and re-scan on subsets.
- Run scans daily for next-day trading ideas.

## Best Way to Build It
Based on best practices for building custom financial desktop apps in Python (sourced from developer resources like Stack Overflow, RealPython, and GitHub repos for similar projects):
- **Language**: Python 3.10+ (widely supported, great for data analysis).
- **GUI Framework**: Use **PyQt6** or **PySide6** (free, Qt-based for professional, responsive desktop apps). Alternatives: Tkinter (built-in, simpler but less polished) or CustomTkinter (modern look). PyQt is recommended for its speed, custom widgets, and chart integration—it's used in apps like TradingView clones.
- **Data Handling**: yfinance library for fetching data (reliable, no API key). Cache using Pandas DataFrames saved as Pickle/CSV files.
- **Analysis**: TA-Lib for technical indicators and patterns (free, fast C-based).
- **Charts**: Matplotlib or Plotly (interactive, free). Embed in GUI for quick popups.
- **Development Tools**: VS Code (free IDE), Git for version control.
- **Best Practices**:
  - **Modular Design**: Separate modules for data fetching, caching, scanning, GUI.
  - **Threading**: Use QThread (in PyQt) for background updates to keep UI responsive during prep.
  - **Error Handling**: Retries for web fetches, logs for issues.
  - **Testing**: Unit tests for scans; simulate data for offline dev.
  - **Deployment**: Package as executable with PyInstaller (free, creates standalone .exe for Windows).
  - **Scalability**: Start with NSE equity list (~2000 stocks); optimize for 20-40 second scans.
  - **Security**: Local only; no user data stored.
  - **Inspiration Projects**: Open-source like "python-stock-screener" on GitHub or "Backtrader" for analysis patterns.

**Development Timeline Estimate** (for an experienced coder):
- Setup and data module: 1-2 days.
- GUI and basic scans: 2-3 days.
- Charts, watchlists, polish: 2 days.
- Testing and packaging: 1 day.
Total: 1 week.

## Software Functionality
### 1. Data Management
- **Source**: Primary: yfinance (Yahoo Finance API—free, reliable for NSE daily OHLCV). Fallback: Upstox API (if user provides credentials; supports daily historical data).
- **NSE Symbol List**: Download from NSE website (https://archives.nseindia.com/content/equities/EQUITY_L.csv) on first run; refresh monthly. Filter to active equities (~2000-2500 symbols, e.g., "RELIANCE.NS").
- **History Depth**: Default 2 years (configurable; needed for scans like 52-week high = max(high) over 252 days).
- **Caching System**:
  - Store in a local folder (e.g., ~/StockScanner/Data/).
  - Each stock: One file (e.g., RELIANCE.NS.pkl) with Pandas DataFrame of OHLCV + Date index.
  - Total size: ~50-100 MB.
- **Prep/Update Phase**:
  - On app open: Automatic background task with progress bar ("Updating data: 0/2000 stocks").
  - For each stock:
    - If no cache: Fetch full history.
    - If cache exists: Get last date in cache, fetch only new data (e.g., last 1-7 days) and append.
  - Time: First run: 5-15 min. Subsequent: 1-5 min (incremental).
  - Handle: Holidays (no new data), errors (retry 3x, skip, log).
  - Manual "Update Now" button.
- **Offline Mode**: If no internet, use existing cache with warning.

### 2. Scanning Engine
- **Core**: Load all cached DataFrames into memory (or on-demand for large lists).
- **Pre-defined Scans**: Dropdown menu with common ones (inspired by Spider Iris):
  - 52-week high: Close >= max(High over last 252 days).
  - 52-week low.
  - Near 52-week high (e.g., within 5%).
  - Above 200-day SMA: Close > SMA(Close, 200).
  - Volume breakout: Volume > 1.5x 20-day avg volume.
  - RSI oversold: RSI(14) < 30.
  - Bullish engulfing (using TA-Lib).
  - Custom: User-defined via simple UI (e.g., "Close > 100 AND Volume > 1e6").
- **Custom Scans**: Allow combining conditions with AND/OR (use a form builder or text input).
- **Scope**: Scan all NSE, or selected watchlist.
- **Performance**: <5 seconds for full scan (TA-Lib is optimized).
- **Results**: Table with columns: Symbol, Close, % Change, Volume, Scan-specific metrics (e.g., % from 52w high).

### 3. User Interface (GUI)
- **Main Window**: 
  - Top: Menu (File: Open/Save Watchlist; Data: Update; Help).
  - Left: Scan selector (dropdown + custom button).
  - Center: Results table (sortable, clickable rows).
  - Bottom: Status bar ("Ready" or "Scanning...").
- **Responsive Design**: No lag; use threading for long tasks.
- **Chart Viewing**: Click row → Popup window with interactive chart (daily candles, zoom, add indicators like MA/RSI).
- **Watchlist Management**:
  - Save results: Button to export as CSV/JSON (e.g., "52w_Highs_20251229.json").
  - Load watchlist: Import file, add to dropdown.
  - Edit: Add/remove stocks manually via search/add button.
  - Multiple lists: Tabbed or list view.
- **Settings**: History depth, data source, theme (light/dark).
- **Look and Feel**: Modern (flat design, colors like blue/grey); resizable window.

### 4. Additional Features
- **Alerts/Notifications**: Optional desktop popups for scan completion.
- **Export**: Results to CSV/Excel.
- **Logs**: Simple text file for errors/updates.
- **Updates**: Check for NSE symbol list changes monthly (manual prompt).
- **Extensibility**: Code structure allows adding new scans easily (e.g., via a scans.py module).

### 5. Technical Stack
- **Libraries** (all free, install via pip):
  - yfinance: Data fetching.
  - pandas: Data manipulation.
  - ta-lib: Indicators/patterns (install binary wheel if needed).
  - PyQt6/PySide6: GUI.
  - matplotlib/plotly: Charts.
  - Optional: requests (for NSE list download), pickle (caching).
- **No Dependencies**: Avoid heavy ML or unnecessary libs.

### 6. Potential Challenges and Solutions
- **Data Accuracy**: yfinance occasionally has gaps; cross-check with Upstox if critical.
- **Rate Limits**: yfinance has soft limits; space out fetches in prep.
- **Platform Compatibility**: Test on Windows (primary); PyQt handles cross-platform.
- **Maintenance**: User can update Python/libs; app can prompt for symbol list refresh.

This covers all discussed elements. Provide this doc to your coder—they can start with a prototype (data + basic scan script) and build up. If needed, add wireframes or expand sections. Let me know for revisions!


---
---
---

Excellent! Your clarifications give me a clear direction. Let me outline an implementation strategy based on your priorities:

## Implementation Strategy

### Phase 1: MVP (Minimum Viable Product) - Core Scanning Engine
**Priority: Essential Features Only**

**Core Functionality:**
1. **Basic Scans** (as you mentioned):
   - Stocks X% up in past month
   - 52-week highs/lows
   - Volume breakouts
   - Simple moving average crossovers

2. **Data Management:**
   - yfinance integration for NSE stocks
   - Local caching system
   - Daily EOD data only

3. **Basic GUI:**
   - Clean, modern interface (better than Spider Iris)
   - Scan selector dropdown
   - Results table
   - Simple chart popup

4. **Watchlist Management:**
   - Save scan results
   - Load watchlists
   - Basic add/remove functionality

### Phase 2: Performance Optimization
**Priority: Speed & Efficiency**

**Performance Enhancements:**
1. **Threading Strategy:**
   - Background data updates
   - Parallel scanning for faster results
   - Progress indicators

2. **Caching Optimization:**
   - Smart incremental updates
   - Memory management for large datasets
   - Database backend if needed (SQLite)

3. **Scan Engine Optimization:**
   - TA-Lib integration for fast indicators
   - Batch processing
   - Result caching

### Phase 3: Enhanced Features
**Priority: Nice-to-Have (Future)**

**Advanced Features:**
1. **More Technical Indicators**
2. **Custom Scan Builder**
3. **Advanced Charting**
4. **Export/Import Options**

## Technical Architecture Recommendations

### Data Strategy
- **Primary**: yfinance (free, reliable for EOD)
- **Fallback**: NSEpy for more robust NSE data
- **Caching**: Pickle files + SQLite for metadata
- **Update Strategy**: Incremental daily updates

### GUI Framework
- **PyQt6**: Professional look, good performance
- **Alternative**: CustomTkinter for modern aesthetics
- **Charting**: Plotly for interactive charts

### Performance Targets
- **Initial scan**: <30 seconds for 2000 stocks
- **Subsequent scans**: <10 seconds (cached data)
- **Data updates**: <5 minutes daily

## Development Approach

### Week 1: Foundation
- Set up project structure
- Implement data fetching and caching
- Create basic scan engine

### Week 2: Core Features
- Build GUI framework
- Implement basic scans
- Add watchlist functionality

### Week 3: Polish & Performance
- Optimize performance
- Add threading
- Improve UI/UX

### Week 4: Testing & Deployment
- Testing with real data
- Packaging as executable
- Documentation

## Questions for Final Strategy

1. **Development Pace**: Would you prefer a faster MVP (2-3 weeks) or more polished initial release (4-5 weeks)?

2. **Testing Approach**: Should we start with a small subset of stocks (e.g., top 100 NSE) for initial testing?

3. **User Interface**: Any specific design preferences (colors, layout style, etc.)?

4. **Error Handling**: How detailed should error messages and logging be for a personal use tool?

This strategy focuses on getting you a working tool quickly while maintaining the performance and modern interface you want. What aspects would you like to adjust or prioritize differently?Excellent! Your clarifications give me a clear direction. Let me outline an implementation strategy based on your priorities:

## Implementation Strategy

### Phase 1: MVP (Minimum Viable Product) - Core Scanning Engine
**Priority: Essential Features Only**

**Core Functionality:**
1. **Basic Scans** (as you mentioned):
   - Stocks X% up in past month
   - 52-week highs/lows
   - Volume breakouts
   - Simple moving average crossovers

2. **Data Management:**
   - yfinance integration for NSE stocks
   - Local caching system
   - Daily EOD data only

3. **Basic GUI:**
   - Clean, modern interface (better than Spider Iris)
   - Scan selector dropdown
   - Results table
   - Simple chart popup

4. **Watchlist Management:**
   - Save scan results
   - Load watchlists
   - Basic add/remove functionality

### Phase 2: Performance Optimization
**Priority: Speed & Efficiency**

**Performance Enhancements:**
1. **Threading Strategy:**
   - Background data updates
   - Parallel scanning for faster results
   - Progress indicators

2. **Caching Optimization:**
   - Smart incremental updates
   - Memory management for large datasets
   - Database backend if needed (SQLite)

3. **Scan Engine Optimization:**
   - TA-Lib integration for fast indicators
   - Batch processing
   - Result caching

### Phase 3: Enhanced Features
**Priority: Nice-to-Have (Future)**

**Advanced Features:**
1. **More Technical Indicators**
2. **Custom Scan Builder**
3. **Advanced Charting**
4. **Export/Import Options**

## Technical Architecture Recommendations

### Data Strategy
- **Primary**: yfinance (free, reliable for EOD)
- **Fallback**: NSEpy for more robust NSE data
- **Caching**: Pickle files + SQLite for metadata
- **Update Strategy**: Incremental daily updates

### GUI Framework
- **PyQt6**: Professional look, good performance
- **Alternative**: CustomTkinter for modern aesthetics
- **Charting**: Plotly for interactive charts

### Performance Targets
- **Initial scan**: <30 seconds for 2000 stocks
- **Subsequent scans**: <10 seconds (cached data)
- **Data updates**: <5 minutes daily

## Development Approach

### Week 1: Foundation
- Set up project structure
- Implement data fetching and caching
- Create basic scan engine

### Week 2: Core Features
- Build GUI framework
- Implement basic scans
- Add watchlist functionality

### Week 3: Polish & Performance
- Optimize performance
- Add threading
- Improve UI/UX

### Week 4: Testing & Deployment
- Testing with real data
- Packaging as executable
- Documentation

## Questions for Final Strategy

1. **Development Pace**: Would you prefer a faster MVP (2-3 weeks) or more polished initial release (4-5 weeks)?

2. **Testing Approach**: Should we start with a small subset of stocks (e.g., top 100 NSE) for initial testing?

3. **User Interface**: Any specific design preferences (colors, layout style, etc.)?

4. **Error Handling**: How detailed should error messages and logging be for a personal use tool?

This strategy focuses on getting you a working tool quickly while maintaining the performance and modern interface you want. What aspects would you like to adjust or prioritize differently?


---
---
---

Excellent point! The fast chart switching you're talking about is crucial for a smooth user experience. Here's how we can achieve that desktop-level performance with TradingView-like functionality:

## Chart Performance Strategy

### 1. **Pre-loading & Caching Strategy**
- **Pre-fetch charts**: When a watchlist loads, pre-load chart data for the first 10-20 stocks in memory
- **Lazy loading**: Load subsequent charts on-demand but cache them
- **Data caching**: Keep OHLCV data in memory for quick chart rendering

### 2. **Charting Library Selection**

**Option A: Plotly (Recommended)**
- **Performance**: Very fast rendering, optimized for desktop
- **TradingView-like**: Can replicate TV interface with custom styling
- **Interactivity**: Zoom, pan, hover, indicators
- **Integration**: Works well with PyQt6
- **MA Support**: Built-in moving averages, easy to add custom indicators

**Option B: Matplotlib + mplfinance**
- **Performance**: Good, but slightly slower than Plotly
- **Customization**: More control over appearance
- **Lightweight**: Smaller footprint

**Option C: PyQtGraph**
- **Performance**: Fastest for PyQt applications
- **Real-time**: Designed for fast updates
- **Custom**: More work to get TradingView look

### 3. **Fast Navigation Implementation**

```python
# Conceptual approach for down arrow navigation
def on_down_arrow_pressed():
    current_stock_index = self.watchlist_table.currentRow()
    next_stock = self.watchlist_stocks[current_stock_index + 1]
    
    # Check if chart data is cached
    if next_stock in self.chart_cache:
        self.update_chart(self.chart_cache[next_stock])
    else:
        # Load from disk/memory and cache
        chart_data = self.load_chart_data(next_stock)
        self.chart_cache[next_stock] = chart_data
        self.update_chart(chart_data)
```

### 4. **TradingView-like Features**

**Core Chart Elements:**
- **Candlestick charts**: OHLC representation
- **Moving Averages**: 20, 50, 200-day MAs
- **Volume bars**: At bottom
- **Zoom/Pan**: Mouse wheel zoom, drag to pan
- **Crosshair**: Hover for exact values
- **Time range**: 1M, 3M, 6M, 1Y, All

**Advanced Features:**
- **Multiple indicators**: RSI, MACD, Bollinger Bands
- **Drawing tools**: Trendlines, support/resistance
- **Alerts**: Price level notifications

### 5. **Performance Optimization**

**Memory Management:**
- **Chart cache limit**: Keep last 50 charts in memory
- **LRU eviction**: Remove oldest charts when cache full
- **Data compression**: Store only necessary OHLCV data

**Rendering Optimization:**
- **Canvas reuse**: Don't recreate charts, just update data
- **Incremental updates**: Only redraw when data changes
- **Threading**: Chart rendering in background threads

### 6. **Implementation Architecture**

```python
class ChartManager:
    def __init__(self):
        self.chart_cache = {}
        self.max_cache_size = 50
    
    def get_chart(self, symbol):
        if symbol in self.chart_cache:
            return self.chart_cache[symbol]
        else:
            return self.create_chart(symbol)
    
    def create_chart(self, symbol):
        # Load data, create Plotly figure
        # Add MAs, volume, etc.
        return chart_figure
    
    def update_chart_cache(self, symbol, chart):
        if len(self.chart_cache) >= self.max_cache_size:
            # Remove oldest
            oldest = next(iter(self.chart_cache))
            del self.chart_cache[oldest]
        self.chart_cache[symbol] = chart
```

### 7. **Keyboard Navigation**

```python
def keyPressEvent(self, event):
    if event.key() == Qt.Key_Down:
        self.navigate_chart(direction='next')
    elif event.key() == Qt.Key_Up:
        self.navigate_chart(direction='prev')
    elif event.key() == Qt.Key_Left:
        self.zoom_out()
    elif event.key() == Qt.Key_Right:
        self.zoom_in()
```

## Performance Targets

- **Chart switch time**: <200ms (instant feel)
- **Initial chart load**: <1 second
- **Memory usage**: ~50MB for 50 cached charts
- **CPU usage**: Minimal during navigation

## Questions for Implementation

1. **Chart Style**: Should we replicate TradingView's exact look, or create a custom modern style?

2. **Indicator Set**: Which specific indicators are must-haves for your analysis?

3. **Chart Size**: Full-screen popup vs. embedded in main window?

4. **Real-time Updates**: Should charts update during market hours, or EOD only?

5. **Customization**: Do you want users to be able to customize chart colors, themes, etc.?

This approach should give you that fast, responsive chart switching experience while maintaining TradingView-like functionality. What aspects would you like to prioritize or modify?