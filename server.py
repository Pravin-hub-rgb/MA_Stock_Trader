"""
MA Stock Trader - Unified Web Platform Backend
FastAPI server providing REST API endpoints for all trading operations
"""

import sys
import os
import logging
import json
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

# Custom logging handler to capture bot logs for frontend display
class BotLogHandler(logging.Handler):
    """Custom logging handler that captures bot logs for frontend display"""

    def __init__(self):
        super().__init__()
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(levelname)s: %(name)s: %(message)s'))

    def emit(self, record):
        """Called when a log record is emitted - add to bot_logs for frontend"""
        global bot_logs

        # Format the log message
        message = self.format(record)

        # Add to bot_logs
        bot_logs.append({
            'timestamp': datetime.now().isoformat(),
            'message': message.strip()
        })

        # Keep only last 300 logs
        if len(bot_logs) > 300:
            bot_logs.pop(0)

# Create global bot log handler instance
bot_log_handler = BotLogHandler()

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
            # Launch the unified bot script with mode argument
            if mode == 'continuation':
                cmd = ['python', 'src/trading/live_trading/run_live_bot.py', 'c']
            else:
                cmd = ['python', 'src/trading/live_trading/run_live_bot.py', 'r']

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
                                # Keep only last 300 logs
                                if len(bot_logs) > 300:
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
        'logs': bot_logs,  # Return all logs
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

@app.get("/api/live-trading/vah-results")
async def get_vah_results():
    """Get VAH calculation results for display in frontend"""
    try:
        vah_file = Path('vah_results.json')

        if vah_file.exists():
            with open(vah_file, 'r') as f:
                data = json.load(f)
                return data
        else:
            return {
                'message': 'VAH results not available yet. Start the bot to calculate VAH values.',
                'timestamp': datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to read VAH results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read VAH results: {str(e)}")

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
    """Get information about cached stock data"""
    try:
        from pathlib import Path
        from src.utils.cache_manager import cache_manager

        # Look at the data/cache directory where processed stock data is stored
        # (this is where the market breadth analyzer loads stocks from)
        cache_dir = Path('data/cache')
        cache_info = {
            'cache_exists': cache_dir.exists(),
            'total_files': 0,
            'total_size_mb': 0,
            'last_updated': None
        }

        if cache_dir.exists():
            total_size = 0

            # Count only .pkl files (processed stock data)
            for file_path in cache_dir.glob('*.pkl'):
                if file_path.is_file():
                    cache_info['total_files'] += 1
                    total_size += file_path.stat().st_size

            cache_info['total_size_mb'] = round(total_size / (1024 * 1024), 2)

            # Get the actual latest data date from cache (not file modification time)
            latest_data_date = cache_manager.get_latest_cache_date()
            if latest_data_date:
                # Convert to ISO format for frontend
                cache_info['last_updated'] = latest_data_date.isoformat()

        return cache_info

    except Exception as e:
        logger.error(f"Cache info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Stock List Management

@app.get("/api/stocks/continuation")
async def get_continuation_stocks():
    """Get all continuation stocks with metadata"""
    try:
        import os
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/continuation_list_metadata.json')

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                stocks = data.get('stocks', [])
                # Sort by added_at descending (newest first)
                stocks.sort(key=lambda x: x['added_at'], reverse=True)
                return {"stocks": stocks}
        else:
            return {"stocks": []}

    except Exception as e:
        logger.error(f"Failed to get continuation stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/continuation")
async def add_continuation_stock(stock_data: dict):
    """Add a stock to the continuation list"""
    try:
        import os
        import json
        from pathlib import Path
        from datetime import datetime

        symbol = stock_data.get('symbol', '').strip().upper()
        source = stock_data.get('source', 'manual')

        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        metadata_file = Path('src/trading/continuation_list_metadata.json')

        # Load existing data
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"stocks": []}

        # Check if stock already exists
        existing_stock = next((s for s in data['stocks'] if s['symbol'] == symbol), None)
        if existing_stock:
            raise HTTPException(status_code=409, detail=f"Stock {symbol} already exists in continuation list")

        # Add new stock
        new_stock = {
            "symbol": symbol,
            "added_at": datetime.now().isoformat(),
            "added_from": source
        }
        data['stocks'].append(new_stock)

        # Save updated data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": f"Added {symbol} to continuation list", "stock": new_stock}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add continuation stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/continuation/{symbol}")
async def remove_continuation_stock(symbol: str):
    """Remove a stock from the continuation list"""
    try:
        import json
        from pathlib import Path

        symbol = symbol.upper()
        metadata_file = Path('src/trading/continuation_list_metadata.json')

        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Continuation list not found")

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        # Find and remove the stock
        original_length = len(data['stocks'])
        data['stocks'] = [s for s in data['stocks'] if s['symbol'] != symbol]

        if len(data['stocks']) == original_length:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in continuation list")

        # Save updated data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": f"Removed {symbol} from continuation list"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove continuation stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/continuation")
async def clear_continuation_stocks():
    """Clear all stocks from the continuation list"""
    try:
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/continuation_list_metadata.json')

        # Create empty data structure
        data = {"stocks": []}

        # Save empty data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": "Cleared all stocks from continuation list"}

    except Exception as e:
        logger.error(f"Failed to clear continuation stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/continuation/finalize")
async def finalize_continuation_list():
    """Generate continuation_list.txt from metadata for live trading"""
    try:
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/continuation_list_metadata.json')
        csv_file = Path('src/trading/continuation_list.txt')

        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="No continuation stocks to finalize")

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        stocks = data.get('stocks', [])
        if not stocks:
            raise HTTPException(status_code=400, detail="No stocks in continuation list to finalize")

        # Extract symbols and create CSV format
        symbols = [stock['symbol'] for stock in stocks]
        csv_content = ','.join(symbols)

        # Write to continuation_list.txt
        with open(csv_file, 'w') as f:
            f.write(csv_content)

        return {
            "message": f"Finalized continuation list with {len(symbols)} stocks",
            "symbols": symbols,
            "file": str(csv_file)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to finalize continuation list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Reversal Stock Management

@app.get("/api/stocks/reversal")
async def get_reversal_stocks():
    """Get all reversal stocks with metadata"""
    try:
        import os
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/reversal_list_metadata.json')

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                stocks = data.get('stocks', [])
                # Sort by added_at descending (newest first)
                stocks.sort(key=lambda x: x['added_at'], reverse=True)
                return {"stocks": stocks}
        else:
            return {"stocks": []}

    except Exception as e:
        logger.error(f"Failed to get reversal stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/reversal")
async def add_reversal_stock(stock_data: dict):
    """Add a stock to the reversal list with period and trend"""
    try:
        import os
        import json
        from pathlib import Path
        from datetime import datetime

        symbol = stock_data.get('symbol', '').strip().upper()
        period = stock_data.get('period')
        trend = stock_data.get('trend', '').lower()  # 'uptrend' or 'downtrend'
        source = stock_data.get('source', 'manual')

        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        if period is None:
            raise HTTPException(status_code=400, detail="Period is required")
        if trend not in ['uptrend', 'downtrend']:
            raise HTTPException(status_code=400, detail="Trend must be 'uptrend' or 'downtrend'")

        metadata_file = Path('src/trading/reversal_list_metadata.json')

        # Load existing data
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"stocks": []}

        # Check if stock already exists
        existing_stock = next((s for s in data['stocks'] if s['symbol'] == symbol), None)
        if existing_stock:
            raise HTTPException(status_code=409, detail=f"Stock {symbol} already exists in reversal list")

        # Add new stock with period/trend
        new_stock = {
            "symbol": symbol,
            "period": period,
            "trend": trend,
            "added_at": datetime.now().isoformat(),
            "added_from": source
        }
        data['stocks'].append(new_stock)

        # Save updated data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": f"Added {symbol} to reversal list", "stock": new_stock}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add reversal stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/reversal/{symbol}")
async def remove_reversal_stock(symbol: str):
    """Remove a stock from the reversal list"""
    try:
        import json
        from pathlib import Path

        symbol = symbol.upper()
        metadata_file = Path('src/trading/reversal_list_metadata.json')

        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Reversal list not found")

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        # Find and remove the stock
        original_length = len(data['stocks'])
        data['stocks'] = [s for s in data['stocks'] if s['symbol'] != symbol]

        if len(data['stocks']) == original_length:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in reversal list")

        # Save updated data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": f"Removed {symbol} from reversal list"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove reversal stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/stocks/reversal")
async def clear_reversal_stocks():
    """Clear all stocks from the reversal list"""
    try:
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/reversal_list_metadata.json')

        # Create empty data structure
        data = {"stocks": []}

        # Save empty data
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

        return {"message": "Cleared all stocks from reversal list"}

    except Exception as e:
        logger.error(f"Failed to clear reversal stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stocks/reversal/finalize")
async def finalize_reversal_list():
    """Generate reversal_list.txt from metadata with SYMBOL-TREND_PERIOD format"""
    try:
        import json
        from pathlib import Path

        metadata_file = Path('src/trading/reversal_list_metadata.json')
        txt_file = Path('src/trading/reversal_list.txt')

        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="No reversal stocks to finalize")

        with open(metadata_file, 'r') as f:
            data = json.load(f)

        stocks = data.get('stocks', [])
        if not stocks:
            raise HTTPException(status_code=400, detail="No stocks in reversal list to finalize")

        # Format as SYMBOL-TREND_PERIOD (e.g., "ABDL-d7", "HDFC-u5")
        def format_stock(stock):
            trend_char = 'u' if stock['trend'] == 'uptrend' else 'd'
            return f"{stock['symbol']}-{trend_char}{stock['period']}"

        formatted_stocks = [format_stock(stock) for stock in stocks]
        csv_content = ','.join(formatted_stocks)

        # Write to reversal_list.txt
        with open(txt_file, 'w') as f:
            f.write(csv_content)

        return {
            "message": f"Finalized reversal list with {len(formatted_stocks)} stocks",
            "formatted_stocks": formatted_stocks,
            "file": str(txt_file)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to finalize reversal list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trading Files Management

@app.get("/api/stocks/trading-files/{list_type}")
async def get_trading_file_contents(list_type: str):
    """Get contents of trading list files (.txt files that bot reads)"""
    try:
        from pathlib import Path

        if list_type not in ['continuation', 'reversal']:
            raise HTTPException(status_code=400, detail="Invalid list type. Must be 'continuation' or 'reversal'")

        # Use server script directory as base (not current working directory)
        server_dir = Path(__file__).parent

        # Determine file path relative to server location
        if list_type == 'continuation':
            file_path = server_dir / 'src/trading/continuation_list.txt'
        else:
            file_path = server_dir / 'src/trading/reversal_list.txt'

        # Read file contents
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = f.read().strip()

            # Parse content for display
            if content:
                symbols = [s.strip() for s in content.split(',') if s.strip()]
            else:
                symbols = []

            # Get file modification time
            import os
            mtime = os.path.getmtime(file_path)
            from datetime import datetime
            last_modified = datetime.fromtimestamp(mtime).isoformat()

            return {
                'file_path': str(file_path),
                'content': content,
                'symbols': symbols,
                'symbol_count': len(symbols),
                'last_modified': last_modified,
                'exists': True
            }
        else:
            return {
                'file_path': str(file_path),
                'content': '',
                'symbols': [],
                'symbol_count': 0,
                'last_modified': None,
                'exists': False
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read trading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read trading file: {str(e)}")

@app.delete("/api/stocks/trading-files/{list_type}")
async def clear_trading_file(list_type: str):
    """Clear trading list file (.txt file that bot reads)"""
    try:
        from pathlib import Path

        if list_type not in ['continuation', 'reversal']:
            raise HTTPException(status_code=400, detail="Invalid list type. Must be 'continuation' or 'reversal'")

        # Use server script directory as base (not current working directory)
        server_dir = Path(__file__).parent

        # Determine file path relative to server location
        if list_type == 'continuation':
            file_path = server_dir / 'src/trading/continuation_list.txt'
        else:
            file_path = server_dir / 'src/trading/reversal_list.txt'

        # Clear the file by writing empty content
        with open(file_path, 'w') as f:
            f.write('')

        return {
            'message': f'Cleared {list_type} trading file',
            'file_path': str(file_path),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to clear trading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear trading file: {str(e)}")

# Token Management - New Modular System

@app.post("/api/token/validate")
async def validate_access_token(token_data: dict):
    """Validate Upstox access token using UpstoxFetcher (same as live trading)"""
    try:
        from src.utils.token_config_manager import token_config_manager
        from src.utils.upstox_fetcher import upstox_fetcher

        token = token_data.get('token', '').strip()

        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        # 1. Update token in config file
        success = token_config_manager.update_token(token)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update token")

        # 2. Force UpstoxFetcher to reload the token immediately
        upstox_fetcher._load_config()

        # 3. Test the token using UpstoxFetcher (same as live trading)
        # Try to get LTP data for RELIANCE
        ltp_data = upstox_fetcher.get_ltp_data('RELIANCE')

        # 4. If UpstoxFetcher can get data, the token is valid
        if ltp_data and 'ltp' in ltp_data:
            return {
                'valid': True,
                'message': 'Token validated successfully',
                'test_result': f'RELIANCE LTP: ₹{ltp_data["ltp"]}',
                'timestamp': datetime.now().isoformat()
            }
        else:
            # If we can't get LTP data, check if it's due to invalid token
            # by trying to initialize the Upstox client
            try:
                upstox_fetcher._ensure_initialized()
                # If initialization succeeds, the token might be valid but API is down
                # If initialization fails with 401, the token is definitely invalid
                return {
                    'valid': False,
                    'error': 'Token validation failed - could not fetch market data',
                    'test_result': 'No LTP data received (token may be invalid or API unavailable)',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as init_error:
                if '401' in str(init_error) or 'Invalid token' in str(init_error):
                    return {
                        'valid': False,
                        'error': 'Token validation failed - invalid token',
                        'test_result': 'Invalid token detected',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'Token validation failed - {str(init_error)}',
                        'test_result': 'Client initialization failed',
                        'timestamp': datetime.now().isoformat()
                    }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/token/current")
async def get_current_token():
    """Get current access token status using the new modular system"""
    try:
        from src.utils.token_validator_module import token_validator_module
        return token_validator_module.get_current_token_status()
    except Exception as e:
        logger.error(f"Failed to read current token: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read token: {str(e)}")

@app.get("/api/token/check")
async def check_token_status():
    """Simple token status check - reads token from config and tests validity without writing back"""
    try:
        from src.utils.token_validator_module import token_validator_module
        from src.utils.upstox_fetcher import upstox_fetcher

        # Get current token status
        status = token_validator_module.get_current_token_status()
        
        if not status.get('token'):
            return {
                'valid': False,
                'message': 'No token found in config file',
                'timestamp': datetime.now().isoformat()
            }

        # Test the token using UpstoxFetcher (same as live trading)
        # Try to get LTP data for RELIANCE
        ltp_data = upstox_fetcher.get_ltp_data('RELIANCE')

        # If UpstoxFetcher can get data, the token is valid
        if ltp_data and 'ltp' in ltp_data:
            return {
                'valid': True,
                'message': 'Token is valid',
                'test_result': f'RELIANCE LTP: ₹{ltp_data["ltp"]}',
                'timestamp': datetime.now().isoformat()
            }
        else:
            # If we can't get LTP data, check if it's due to invalid token
            # by trying to initialize the Upstox client
            try:
                upstox_fetcher._ensure_initialized()
                # If initialization succeeds, the token might be valid but API is down
                # If initialization fails with 401, the token is definitely invalid
                return {
                    'valid': False,
                    'message': 'Token validation failed - could not fetch market data',
                    'test_result': 'No LTP data received (token may be invalid or API unavailable)',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as init_error:
                if '401' in str(init_error) or 'Invalid token' in str(init_error):
                    return {
                        'valid': False,
                        'message': 'Token validation failed - invalid token',
                        'test_result': 'Invalid token detected',
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'valid': False,
                        'message': f'Token validation failed - {str(init_error)}',
                        'test_result': 'Client initialization failed',
                        'timestamp': datetime.now().isoformat()
                    }

    except Exception as e:
        logger.error(f"Token check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Token check failed: {str(e)}")


@app.post("/api/token/update")
async def update_token_config(token_data: dict):
    """Update token in config file using the new modular system"""
    try:
        from src.utils.token_validator_module import token_validator_module
        
        token = token_data.get('token', '').strip()
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")

        result = token_validator_module.update_token_in_config(token)
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token update failed: {e}")
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
                fieldnames = ['symbol', 'close', 'period', 'green_days', 'first_red_date', 'decline_percent', 'trend_context', 'liquidity_verified', 'adr_percent']
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
            # Handle both single date (manual update) and date range (smart update) responses
            if 'date' in result:
                # Manual update for specific date
                date_info = result['date']
                message = f"Successfully updated cache with {date_info} data"
            else:
                # Smart update with date range
                date_info = result.get('date_range', 'unknown range')
                message = f"Successfully updated cache for date range: {date_info}"

            active_operations[operation_id].update({
                "status": "completed",
                "progress": 100,
                "message": message,
                "result": {
                    "date_info": date_info,
                    "status": "success",
                    "stocks_updated": result.get('total_stocks_updated', result.get('stocks_updated', 0))
                }
            })
            logger.info(f"Bhavcopy update completed: {operation_id} - {date_info}")
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
    print("API available at: http://localhost:8001")
    print("Documentation at: http://localhost:8001/docs")

    uvicorn.run(
        "server:app",
        host="127.0.0.1",  # Use localhost instead of 0.0.0.0 for frontend proxy
        port=8001,  # Use port 8001 to avoid conflicts
        reload=False,  # Disable reload to prevent import crashes
        log_level="info"
    )
