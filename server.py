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
    """Get cached breadth data from existing breadth_data.pkl file"""
    try:
        # Use the existing BreadthCacheManager from the working GUI
        from src.scanner.market_breadth_analyzer import breadth_cache

        # Get all cached dates
        all_dates = breadth_cache.get_all_cached_dates()

        if not all_dates:
            return {
                "data": [],
                "total_dates": 0,
                "last_updated": None,
                "message": "No breadth data available. Click 'Update' to calculate."
            }

        # Convert cached data to frontend format
        results = []
        for date_key in sorted(all_dates, reverse=True):  # Most recent first
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

        # Get last updated time from file modification
        import os
        cache_file = Path('data/breadth_cache/breadth_data.pkl')
        last_updated = None
        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            last_updated = datetime.fromtimestamp(mtime).isoformat()

        return {
            "data": results,
            "total_dates": len(results),
            "last_updated": last_updated
        }

    except Exception as e:
        logger.error(f"Failed to load breadth data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/breadth/update")
async def update_breadth_data():
    """Update breadth data using existing BreadthCalculator - saves to breadth_data.pkl"""
    try:
        # Use the same BreadthCalculator as the GUI - it automatically uses breadth_cache
        from src.scanner.market_breadth_analyzer import BreadthCalculator

        # Create calculator and run the calculation
        # This automatically saves results to breadth_data.pkl via BreadthCacheManager
        calculator = BreadthCalculator()
        results = calculator._calculate_breadth()

        return {
            "status": "success",
            "data": results,
            "total_dates": len(results),
            "last_updated": datetime.now().isoformat(),
            "message": f"Breadth analysis completed: {len(results)} dates"
        }

    except Exception as e:
        logger.error(f"Breadth update failed: {e}")
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

# Live Trading Operations

@app.get("/api/live-trading/validate-lists")
async def validate_trading_lists():
    """Validate continuation and reversal lists for live trading readiness"""
    try:
        from validate_trading_lists import TradingListValidator

        validator = TradingListValidator()

        # Capture output using redirect
        import io
        import sys
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            validator.print_results()

        output = f.getvalue()

        return {
            'validation_output': output,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"List validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Global bot process management
bot_process = None
bot_logs = []

@app.post("/api/live-trading/start")
async def start_live_trading(data: dict, background_tasks: BackgroundTasks):
    """Start the live trading bot as a subprocess"""
    global bot_process, bot_logs

    try:
        mode = data.get('mode', 'continuation')

        if mode not in ['continuation', 'reversal']:
            raise HTTPException(status_code=400, detail="Invalid mode. Must be 'continuation' or 'reversal'")

        # Check if bot is already running
        if bot_process and bot_process.poll() is None:
            return {
                'status': 'already_running',
                'message': 'Bot is already running',
                'timestamp': datetime.now().isoformat()
            }

        # Clear previous logs
        bot_logs.clear()

        # Start the bot as a subprocess
        import subprocess
        import threading

        try:
            # Launch the actual run_live_bot.py script
            # Convert mode to expected format: continuation -> c, reversal -> r
            mode_arg = 'c' if mode == 'continuation' else 'r'
            cmd = ['python', 'run_live_bot.py', mode_arg]

            logger.info(f"Starting bot with command: {' '.join(cmd)}")
            logger.info(f"Working directory: {os.getcwd()}")
            logger.info(f"Python executable: {sys.executable}")

            bot_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr separately
                text=True,
                bufsize=1,
                cwd=os.getcwd(),
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}  # Disable output buffering
            )

            logger.info(f"Bot process started with PID: {bot_process.pid}")

            # Start log streaming thread
            def stream_logs():
                global bot_logs
                try:
                    # Read stdout
                    if bot_process.stdout:
                        for line in iter(bot_process.stdout.readline, ''):
                            if line.strip():
                                bot_logs.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'message': line.strip()
                                })
                                # Keep only last 100 logs
                                if len(bot_logs) > 100:
                                    bot_logs.pop(0)

                    # Read stderr
                    if bot_process.stderr:
                        for line in iter(bot_process.stderr.readline, ''):
                            if line.strip():
                                bot_logs.append({
                                    'timestamp': datetime.now().isoformat(),
                                    'message': f"ERROR: {line.strip()}"
                                })

                except Exception as e:
                    logger.error(f"Exception in log streaming thread: {e}")

                # Check final process status
                final_poll = bot_process.poll()
                logger.info(f"Bot process finished with exit code: {final_poll}")

            threading.Thread(target=stream_logs, daemon=True).start()

            logger.info(f"Live trading bot started with mode: {mode}")

            return {
                'status': 'started',
                'mode': mode,
                'message': f'Bot started in {mode} mode',
                'process_id': bot_process.pid,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to launch bot process: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to start bot: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start live trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/live-trading/stop")
async def stop_live_trading():
    """Stop the live trading bot"""
    global bot_process

    try:
        if not bot_process:
            return {
                'status': 'not_running',
                'message': 'Bot is not running',
                'timestamp': datetime.now().isoformat()
            }

        # Terminate the bot process
        try:
            bot_process.terminate()
            # Wait up to 5 seconds for graceful shutdown
            try:
                bot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't respond
                bot_process.kill()
                bot_process.wait()

            logger.info("Live trading bot stopped successfully")
            bot_process = None

            return {
                'status': 'stopped',
                'message': 'Bot stopped successfully',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error stopping bot process: {e}")
            # Try force kill
            try:
                if bot_process and bot_process.poll() is None:
                    bot_process.kill()
                    bot_process = None
            except:
                pass

            raise HTTPException(status_code=500, detail=f"Failed to stop bot: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop live trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live-trading/logs")
async def get_live_trading_logs():
    """Get current live trading logs"""
    global bot_logs

    return {
        'logs': bot_logs[-50:],  # Return last 50 logs
        'is_running': bot_process is not None and bot_process.poll() is None,
        'total_logs': len(bot_logs),
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/live-trading/status")
async def get_live_trading_status():
    """Get live trading bot status"""
    global bot_process

    is_running = bot_process is not None and bot_process.poll() is None

    return {
        'is_running': is_running,
        'process_id': bot_process.pid if bot_process else None,
        'exit_code': bot_process.poll() if bot_process else None,
        'total_logs': len(bot_logs),
        'timestamp': datetime.now().isoformat()
    }

# Data Management

@app.post("/api/data/update-bhavcopy")
async def update_bhavcopy_data(background_tasks: BackgroundTasks):
    """Update latest bhavcopy data from NSE"""
    try:
        operation_id = f"bhavcopy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Start background task
        background_tasks.add_task(run_bhavcopy_update_background, operation_id)

        return {
            "status": "started",
            "operation_id": operation_id,
            "message": "Bhavcopy data update started"
        }

    except Exception as e:
        logger.error(f"Bhavcopy update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/status/{operation_id}")
async def get_data_update_status(operation_id: str):
    """Get status of data update operation"""
    if operation_id not in active_operations:
        raise HTTPException(status_code=404, detail="Operation not found")

    return active_operations[operation_id]

@app.get("/api/data/cache-info")
async def get_cache_info():
    """Get information about cached data"""
    try:
        import os
        from pathlib import Path

        cache_dir = Path('bhavcopy_cache')
        cache_info = {
            'cache_exists': cache_dir.exists(),
            'total_files': 0,
            'total_size_mb': 0,
            'last_updated': None
        }

        if cache_dir.exists():
            total_size = 0
            latest_mtime = 0

            for file_path in cache_dir.rglob('*'):
                if file_path.is_file():
                    cache_info['total_files'] += 1
                    total_size += file_path.stat().st_size
                    latest_mtime = max(latest_mtime, file_path.stat().st_mtime)

            cache_info['total_size_mb'] = round(total_size / (1024 * 1024), 2)
            if latest_mtime > 0:
                cache_info['last_updated'] = datetime.fromtimestamp(latest_mtime).isoformat()

        return cache_info

    except Exception as e:
        logger.error(f"Cache info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Token Management

@app.post("/api/token/validate")
async def validate_access_token(token_data: dict):
    """Validate Upstox access token by testing with actual trading list stocks"""
    try:
        token = token_data.get('token', '').strip()

        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        # Use hardcoded top 10 stocks that are unlikely to ever be delisted
        # If any one returns LTP data, token is valid
        test_symbols = [
            'RELIANCE',    # Reliance Industries Limited
            'TCS',         # Tata Consultancy Services
            'HDFCBANK',    # HDFC Bank Limited
            'INFY',        # Infosys Limited
            'ICICIBANK',   # ICICI Bank Limited
            'HINDUNILVR',  # Hindustan Unilever Limited
            'ITC',         # ITC Limited
            'SBIN',        # State Bank of India
            'BHARTIARTL',  # Bharti Airtel Limited
            'BAJFINANCE'   # Bajaj Finance Limited
        ]

        from src.utils.upstox_fetcher import UpstoxFetcher

        # Create fetcher and temporarily set token
        fetcher = UpstoxFetcher()
        original_token = getattr(fetcher, 'access_token', None)
        fetcher.access_token = token

        successful_tests = 0
        test_results = []

        try:
            # Test token by getting LTP for sample stocks (same as list validation)
            for symbol in test_symbols[:3]:  # Test up to 3 stocks
                try:
                    data = fetcher.get_latest_data(symbol)
                    if data and 'close' in data:
                        successful_tests += 1
                        test_results.append(f"OK {symbol}: Rs{data['close']:.2f}")
                    else:
                        test_results.append(f"FAIL {symbol}: No data received")
                except Exception as e:
                    test_results.append(f"FAIL {symbol}: {str(e)}")

            # Token is valid if we can get data for at least 1 stock
            if successful_tests > 0:
                # Update config with valid token
                await update_token_in_config(token)

                return {
                    'valid': True,
                    'successful_tests': successful_tests,
                    'total_tests': len(test_symbols[:3]),
                    'test_results': test_results,
                    'message': f'Token validated successfully ({successful_tests}/{len(test_symbols[:3])} stocks)',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'valid': False,
                    'error': 'Could not retrieve data for any test stocks',
                    'test_results': test_results
                }

        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return {
                'valid': False,
                'error': f'Token validation failed: {str(e)}'
            }
        finally:
            # Restore original token if it existed
            if original_token:
                fetcher.access_token = original_token

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def update_token_in_config(token: str):
    """Update access token in config file"""
    try:
        import json
        config_path = Path('config/config.json')

        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Update token
        config['upstox_access_token'] = token

        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info("Access token updated in config file")

    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save token: {str(e)}")

@app.get("/api/token/current")
async def get_current_token():
    """Get current access token from config file"""
    try:
        import json
        config_path = Path('config/config.json')
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            token = config.get('upstox_access_token')
            return {
                'token': token,
                'exists': bool(token),
                'masked': f"{'*' * 10}...{token[-4:]}" if token else None
            }
        return {'token': None, 'exists': False, 'masked': None}
    except Exception as e:
        logger.error(f"Failed to read current token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read token: {str(e)}")

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
    """Background task for breadth analysis using the real BreadthCalculator"""
    try:
        logger.info(f"Starting breadth analysis: {operation_id}")

        active_operations[operation_id] = {
            "type": "breadth_analysis",
            "status": "running",
            "progress": 0,
            "message": "Initializing breadth analysis..."
        }

        # Use the real BreadthCalculator from the working GUI
        from src.scanner.market_breadth_analyzer import BreadthCalculator

        # Create calculator and override progress callback
        calculator = BreadthCalculator()

        # Override the progress signal to update our operation status
        def progress_callback(message: str):
            # Map progress messages to percentages
            if "Found" in message and "cached stocks" in message:
                progress = 10
            elif "Loaded" in message and "stocks with data" in message:
                progress = 30
            elif "Found" in message and "cached dates" in message:
                progress = 50
            elif "Using" in message and "cached results" in message:
                progress = 70
            elif "Calculating date" in message:
                progress = 90
            elif "Completed breadth analysis" in message:
                progress = 100
            else:
                progress = active_operations[operation_id].get("progress", 0)

            active_operations[operation_id].update({
                "progress": progress,
                "message": message
            })

        # Monkey patch the progress signal
        original_progress = calculator.progress
        calculator.progress = progress_callback

        try:
            # Run the actual breadth calculation
            results = calculator._calculate_breadth()

            active_operations[operation_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"Breadth analysis completed: {len(results)} dates analyzed",
                "result": {
                    "dates_analyzed": len(results),
                    "data": results,
                    "exported_file": f"market_breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            })

            logger.info(f"Breadth analysis completed: {operation_id} - {len(results)} results")

        finally:
            # Restore original progress callback
            calculator.progress = original_progress

    except Exception as e:
        logger.error(f"Breadth analysis background task failed: {e}")
        active_operations[operation_id].update({
            "status": "error",
            "error": str(e)
        })

def run_bhavcopy_update_background(operation_id: str):
    """Background task for bhavcopy data update"""
    try:
        logger.info(f"Starting bhavcopy update: {operation_id}")

        active_operations[operation_id] = {
            "type": "bhavcopy_update",
            "status": "running",
            "progress": 0,
            "message": "Initializing bhavcopy update..."
        }

        # Import and run the bhavcopy update
        from src.utils.bhavcopy_integrator import update_latest_bhavcopy

        # Update progress
        active_operations[operation_id].update({
            "progress": 25,
            "message": "Downloading latest bhavcopy from NSE..."
        })

        # Run the update
        result = update_latest_bhavcopy()

        if result['status'] == 'SUCCESS':
            active_operations[operation_id].update({
                "status": "completed",
                "progress": 100,
                "message": f"Successfully updated cache with {result['date']} data",
                "result": {
                    "date": result['date'],
                    "status": "success"
                }
            })
            logger.info(f"Bhavcopy update completed: {operation_id} - {result['date']}")
        else:
            active_operations[operation_id].update({
                "status": "error",
                "progress": 100,
                "error": result.get('error', 'Unknown error occurred'),
                "message": f"Failed to update bhavcopy: {result.get('error', 'Unknown error')}"
            })
            logger.error(f"Bhavcopy update failed: {operation_id} - {result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Bhavcopy update background task failed: {e}")
        active_operations[operation_id].update({
            "status": "error",
            "error": str(e)
        })

# WebSocket endpoint for progress updates will be added later

if __name__ == "__main__":
    print("Starting MA Stock Trader API Server...")
    print("API available at: http://localhost:8000")
    print("Documentation at: http://localhost:8000/docs")

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
