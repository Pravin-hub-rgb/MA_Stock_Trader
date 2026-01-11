# MA Stock Trader - Unified Web Platform

## Overview

This document outlines the architecture and implementation plan for a unified web-based trading platform that consolidates all MA Stock Trader tools into a single, modern web interface.

## Architecture

### Backend: Python FastAPI Server
- **Framework**: FastAPI with Uvicorn ASGI server
- **Purpose**: Expose all trading operations as REST API endpoints
- **Real-time**: WebSocket support for progress updates
- **File Handling**: CSV export/import capabilities

### Frontend: React Web Application
- **Framework**: React with TypeScript
- **UI Library**: Material-UI (MUI) for professional components
- **Styling**: Tailwind CSS for responsive design
- **Features**: Tabbed interface, color-coded tables, real-time updates

### Development Setup

#### Backend Setup
```bash
# Install dependencies
pip install fastapi uvicorn python-multipart

# Start development server
python server.py
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## API Endpoints

### Scanner Operations

#### Continuation Scanner
```http
POST /api/scanner/continuation
```
**Purpose**: Run continuation scanner and return results
**Request Body**:
```json
{
  "date": "2026-01-10",
  "filters": {
    "min_volume": 100000,
    "max_stocks": 50
  }
}
```
**Response**:
```json
{
  "status": "success",
  "results_count": 25,
  "exported_file": "continuation_scan_20260110_120000.csv"
}
```

#### Reversal Scanner
```http
POST /api/scanner/reversal
```
**Purpose**: Run reversal scanner and return results
**Request Body**:
```json
{
  "date": "2026-01-10",
  "filters": {
    "min_volume": 50000,
    "max_stocks": 30
  }
}
```
**Response**:
```json
{
  "status": "success",
  "results_count": 18,
  "exported_file": "reversal_scan_20260110_120000.csv"
}
```

### Market Breadth Analysis

#### Run Breadth Analysis
```http
POST /api/breadth/analyze
```
**Purpose**: Calculate market breadth metrics for available dates
**Request Body**:
```json
{
  "force_refresh": false,
  "max_dates": 30
}
```
**Response**:
```json
{
  "status": "success",
  "dates_analyzed": 25,
  "exported_file": "market_breadth_20260110_120000.csv",
  "summary": {
    "total_dates": 25,
    "cached_dates": 20,
    "calculated_dates": 5
  }
}
```

### File Management

#### List Available Files
```http
GET /api/files/list
```
**Purpose**: Get list of all exported result files
**Query Parameters**:
- `type`: Filter by file type (`scan`, `breadth`, `all`)
- `limit`: Maximum number of files to return (default: 50)

**Response**:
```json
{
  "files": [
    {
      "filename": "continuation_scan_20260110_120000.csv",
      "type": "scan",
      "size": 24560,
      "created": "2026-01-10T12:00:00Z",
      "description": "Continuation scan results"
    },
    {
      "filename": "market_breadth_20260110_115959.csv",
      "type": "breadth",
      "size": 18943,
      "created": "2026-01-10T11:59:59Z",
      "description": "Market breadth analysis"
    }
  ]
}
```

#### Download File
```http
GET /api/files/download/{filename}
```
**Purpose**: Download a specific result file
**Response**: CSV file as attachment

### Real-time Communication

#### WebSocket Progress Updates
```websocket
WS /ws/progress
```
**Purpose**: Receive real-time progress updates for long-running operations

**Message Types**:

**Operation Started**:
```json
{
  "type": "operation_started",
  "operation_id": "scan_continuation_20260110_120000",
  "operation_type": "continuation_scan",
  "message": "Starting continuation scan..."
}
```

**Progress Update**:
```json
{
  "type": "progress_update",
  "operation_id": "scan_continuation_20260110_120000",
  "progress": 65,
  "message": "Processing 650/1000 stocks..."
}
```

**Operation Completed**:
```json
{
  "type": "operation_completed",
  "operation_id": "scan_continuation_20260110_120000",
  "status": "success",
  "result": {
    "results_count": 25,
    "exported_file": "continuation_scan_20260110_120000.csv"
  }
}
```

**Error**:
```json
{
  "type": "error",
  "operation_id": "scan_continuation_20260110_120000",
  "error": "Failed to load stock data",
  "details": "Cache directory not found"
}
```

## Frontend Structure

### Navigation Tabs
1. **Dashboard**: Overview and quick actions
2. **Continuation Scanner**: Run and view continuation scans
3. **Reversal Scanner**: Run and view reversal scans
4. **Market Breadth**: Run breadth analysis and view color-coded results
5. **Results**: Browse and download all exported files

### Key Components

#### Color-Coded Data Tables
- **Market Breadth**: Full color gradient for momentum visualization
- **Scanner Results**: Conditional formatting based on signal strength
- **Interactive**: Sortable, filterable, exportable

#### Real-time Progress
- **Progress Bars**: Visual progress for long operations
- **Live Updates**: WebSocket-powered status updates
- **Cancel Operations**: Ability to stop running processes

#### File Management
- **File Browser**: List all generated reports
- **Quick Download**: One-click CSV downloads
- **Auto-refresh**: New files appear automatically

## Development Workflow

### Backend Development
1. Add new endpoints in `server.py`
2. Implement business logic using existing scanner modules
3. Add WebSocket handlers for progress updates
4. Test API endpoints with tools like Postman or curl

### Frontend Development
1. Create new components in `frontend/src/components/`
2. Add API integration in `frontend/src/services/`
3. Implement WebSocket connections for real-time updates
4. Style components with Tailwind CSS classes

### Deployment
```bash
# Backend
python server.py

# Frontend (separate terminal)
cd frontend && npm run dev

# Production build
cd frontend && npm run build
```

## File Structure

```
MA_Stock_Trader/
├── server.py                    # FastAPI backend server
├── frontend/                    # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── services/          # API integration
│   │   └── pages/             # Page components
│   ├── public/
│   └── package.json
├── src/                        # Existing Python modules
├── docs/
│   └── unified_platform.md     # This document
└── requirements.txt
```

## Future Enhancements

### Phase 2: Data Management
- Bhavcopy updates via web interface
- Cache management and health monitoring
- Historical data import/export

### Phase 3: Live Trading Integration
- Real-time trading controls
- Position monitoring dashboard
- Risk management interface

### Phase 4: Advanced Features
- Portfolio analytics
- Performance reporting
- Alert system

## Benefits

- **Unified Interface**: Single entry point for all trading tools
- **Modern UX**: Professional web interface with color coding
- **Real-time Feedback**: Live progress updates and status monitoring
- **Cross-platform**: Works on any device with a browser
- **Maintainable**: Clean separation of frontend and backend concerns
- **Scalable**: Easy to add new features and tools

This unified platform will transform your collection of command-line tools into a professional, web-based trading application.
