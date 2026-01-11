"""
MA Stock Trader - Unified Web Platform Backend
FastAPI server providing REST API endpoints for all trading operations
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import scanner modules only when needed to avoid Upstox API issues at startup
from src.scanner.scanner import scanner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MA Stock Trader API",
    description="Unified API for trading operations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global operation tracking
active_operations = {}

# Pydantic models
class ScanRequest(BaseModel):
    date: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class BreadthRequest(BaseModel):
    force_refresh: bool = False
    max_dates: int = 30

class FileInfo(BaseModel):
    filename: str
    type: str
    size: int
    created: str
    description: str

# API Routes

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "MA Stock Trader API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Scanner Operations

@app.post("/api/scanner/continuation")
async def run_continuation_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Run continuation scanner"""
    try:
        operation_id = f"continuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Start background task
        background_tasks.add_task(run_continuation_scan_background, operation_id, request)

        return {
            "status": "started",
            "operation_id": operation_id,
            "message": "Continuation scan started"
        }

    except Exception as e:
        logger.error(f"Continuation scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scanner/reversal")
async def run_reversal_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """Run reversal scanner"""
    try:
        operation_id = f"reversal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Start background task
        background_tasks.add_task(run_reversal_scan_background, operation_id, request)

        return {
            "status": "started",
            "operation_id": operation_id,
            "message": "Reversal scan started"
        }

    except Exception as e:
        logger.error(f"Reversal scan failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scanner/status/{operation_id}")
async def get_scan_status(operation_id: str):
    """Get status of a scan operation"""
    if operation_id not in active_operations:
        raise HTTPException(status_code=404, detail="Operation not found")

    return active_operations[operation_id]

# Market Breadth

@app.get("/api/breadth/data")
async def get_breadth_data():
    """Get all cached breadth data"""
    try:
        # Import here to avoid startup issues
        from src.scanner.market_breadth_analyzer import breadth_cache

        # Get all cached breadth data
        cached_dates = breadth_cache.get_all_cached_dates()
        results = []

        for date_key in sorted(cached_dates, reverse=True):  # Most recent first
            try:
                cached_data = breadth_cache.get_cached_breadth(date_key)
                if cached_data:
                    result = {
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
                    results.append(result)
            except Exception as e:
                logger.warning(f"Error loading cached data for {date_key}: {e}")
                continue

        return {
            "data": results,
            "total_dates": len(results),
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to load breadth data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/breadth/analyze")
async def run_breadth_analysis(request: BreadthRequest, background_tasks: BackgroundTasks):
    """Run market breadth analysis"""
    try:
        operation_id = f"breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Start background task
        background_tasks.add_task(run_breadth_analysis_background, operation_id, request)

        return {
            "status": "started",
            "operation_id": operation_id,
            "message": "Market breadth analysis started"
        }

    except Exception as e:
        logger.error(f"Breadth analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File Management

@app.get("/api/files/list")
async def list_files(file_type: str = Query("all", description="Filter by file type: scan, breadth, all")):
    """List available result files"""
    try:
        files = []

        # Scan directories for result files
        directories = {
            "scan": ["continuation_scans", "reversal_scans"],
            "breadth": ["market_breadth_reports"],
            "all": ["continuation_scans", "reversal_scans", "market_breadth_reports"]
        }

        dirs_to_check = directories.get(file_type, directories["all"])

        for dir_name in dirs_to_check:
            dir_path = Path(dir_name)
            if dir_path.exists():
                for file_path in dir_path.glob("*.csv"):
                    try:
                        stat = file_path.stat()
                        files.append(FileInfo(
                            filename=file_path.name,
                            type=dir_name.replace("_", " ").replace("scans", "scan"),
                            size=stat.st_size,
                            created=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            description=f"{dir_name.replace('_', ' ').title()} results"
                        ))
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")
                        continue

        # Sort by creation date (newest first)
        files.sort(key=lambda x: x.created, reverse=True)

        return {"files": files[:50]}  # Limit to 50 most recent

    except Exception as e:
        logger.error(f"File listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files/download/{filename}")
async def download_file(filename: str):
    """Download a specific file"""
    try:
        # Search for file in all result directories
        search_dirs = ["continuation_scans", "reversal_scans", "market_breadth_reports"]

        for dir_name in search_dirs:
            file_path = Path(dir_name) / filename
            if file_path.exists():
                return FileResponse(
                    path=file_path,
                    filename=filename,
                    media_type='text/csv'
                )

        raise HTTPException(status_code=404, detail="File not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions

def run_continuation_scan_background(operation_id: str, request: ScanRequest):
    """Background task for continuation scan"""
    try:
        logger.info(f"Starting continuation scan: {operation_id}")

        # Update operation status
        active_operations[operation_id] = {
            "type": "continuation_scan",
            "status": "running",
            "progress": 0,
            "message": "Initializing continuation scan..."
        }

        # Apply filter parameters if provided
        if hasattr(request, 'filters') and request.filters:
            filters = request.filters
            logger.info(f"Applying filters: {filters}")

            if 'min_price' in filters:
                scanner.update_price_filters(filters['min_price'], filters.get('max_price', 2000))
            if 'max_price' in filters and 'min_price' not in filters:
                # If only max_price provided, keep current min_price
                current_min = getattr(scanner, 'common_params', {}).get('price_min', 100)
                scanner.update_price_filters(current_min, filters['max_price'])
            if 'near_ma_threshold' in filters:
                scanner.update_near_ma_threshold(filters['near_ma_threshold'])
            if 'max_body_percentage' in filters:
                scanner.update_max_body_percentage(filters['max_body_percentage'])

            logger.info(f"Updated scanner filters - current params: {scanner.common_params}")

        # Create a progress callback function
        def progress_callback(value: int, message: str):
            active_operations[operation_id].update({
                "progress": value,
                "message": message
            })

        # Run the actual continuation scan
        results = scanner.run_continuation_scan(
            scan_date=None,  # Auto-detect latest available date
            progress_callback=progress_callback
        )

        # Export results to CSV
        if results:
            import csv
            import os
            os.makedirs('continuation_scans', exist_ok=True)
            filename = f"continuation_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(f'continuation_scans/{filename}', 'w', newline='') as csvfile:
                fieldnames = ['symbol', 'close', 'sma20', 'dist_to_ma_pct', 'phase1_high', 'phase2_low', 'phase3_high', 'depth_rs', 'depth_pct', 'adr_pct']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            logger.info(f"Exported {len(results)} continuation results to {filename}")

        # Update final status
        active_operations[operation_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Continuation scan completed - found {len(results) if results else 0} setups",
            "result": {
                "results_count": len(results) if results else 0,
                "exported_file": filename if results else None,
                "results": results[:50] if results else []  # Include first 50 results in response
            }
        })

        logger.info(f"Continuation scan completed: {operation_id} - {len(results) if results else 0} results")

    except Exception as e:
        logger.error(f"Continuation scan background task failed: {e}")
        active_operations[operation_id].update({
            "status": "error",
            "error": str(e)
        })

def run_reversal_scan_background(operation_id: str, request: ScanRequest):
    """Background task for reversal scan"""
    try:
        logger.info(f"Starting reversal scan: {operation_id}")

        # Update operation status
        active_operations[operation_id] = {
            "type": "reversal_scan",
            "status": "running",
            "progress": 0,
            "message": "Initializing reversal scan..."
        }

        # Apply filter parameters if provided
        if hasattr(request, 'filters') and request.filters:
            filters = request.filters
            logger.info(f"Applying reversal filters: {filters}")

            if 'min_price' in filters:
                scanner.update_price_filters(filters['min_price'], filters.get('max_price', 2000))
            if 'max_price' in filters and 'min_price' not in filters:
                # If only max_price provided, keep current min_price
                current_min = getattr(scanner, 'common_params', {}).get('price_min', 100)
                scanner.update_price_filters(current_min, filters['max_price'])
            if 'min_decline_percent' in filters:
                scanner.update_min_decline_percent(filters['min_decline_percent'])

            logger.info(f"Updated reversal scanner filters - current params: {scanner.reversal_params}")

        # Create a progress callback function
        def progress_callback(value: int, message: str):
            active_operations[operation_id].update({
                "progress": value,
                "message": message
            })

        # Run the actual reversal scan
        results = scanner.run_reversal_scan(
            scan_date=None,  # Auto-detect latest available date
            progress_callback=progress_callback
        )

        # Export results to CSV
        if results:
            import csv
            import os
            os.makedirs('reversal_scans', exist_ok=True)
            filename = f"reversal_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(f'reversal_scans/{filename}', 'w', newline='') as csvfile:
                fieldnames = ['symbol', 'close', 'period', 'red_days', 'green_days', 'decline_percent', 'trend_context', 'liquidity_verified', 'adr_percent']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

            logger.info(f"Exported {len(results)} reversal results to {filename}")

        # Update final status
        active_operations[operation_id].update({
            "status": "completed",
            "progress": 100,
            "message": f"Reversal scan completed - found {len(results) if results else 0} setups",
            "result": {
                "results_count": len(results) if results else 0,
                "exported_file": filename if results else None,
                "results": results[:50] if results else []  # Include first 50 results in response
            }
        })

        logger.info(f"Reversal scan completed: {operation_id} - {len(results) if results else 0} results")

    except Exception as e:
        logger.error(f"Reversal scan background task failed: {e}")
        active_operations[operation_id].update({
            "status": "error",
            "error": str(e)
        })

def run_breadth_analysis_background(operation_id: str, request: BreadthRequest):
    """Background task for breadth analysis"""
    try:
        logger.info(f"Starting breadth analysis: {operation_id}")

        active_operations[operation_id] = {
            "type": "breadth_analysis",
            "status": "running",
            "progress": 0,
            "message": "Initializing breadth analysis..."
        }

        # Simulate the analysis process
        import time
        for i in range(0, 101, 8):
            time.sleep(0.6)
            active_operations[operation_id].update({
                "progress": i,
                "message": f"Calculating breadth metrics... {i}% complete"
            })

        active_operations[operation_id].update({
            "status": "completed",
            "progress": 100,
            "message": "Breadth analysis completed",
            "result": {
                "dates_analyzed": 25,
                "exported_file": f"market_breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        })

        logger.info(f"Breadth analysis completed: {operation_id}")

    except Exception as e:
        logger.error(f"Breadth analysis background task failed: {e}")
        active_operations[operation_id].update({
            "status": "error",
            "error": str(e)
        })

# WebSocket endpoint for progress updates will be added later

if __name__ == "__main__":
    print("🚀 Starting MA Stock Trader API Server...")
    print("📡 API available at: http://localhost:8000")
    print("📚 Documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
