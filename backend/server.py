"""
TradeStack — FastAPI Backend
Entry point for the Python data microservice.
"""
import logging
import threading
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.cache_manager import cache_manager
from src.bhavcopy_updater import update_cache_for_date, fill_cache_gaps, find_cache_gaps, get_cache_dates

_MAX_LOG_ENTRIES = 500


def _log(op: dict, message: str):
    """Add a log entry to an operation, capping at MAX_LOG_ENTRIES to prevent unbounded memory growth."""
    if len(op.get("logs", [])) < _MAX_LOG_ENTRIES:
        op.setdefault("logs", []).append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
from src.nse_fetcher import get_latest_trading_date, get_nse_holidays
from src.db import (
    get_cache_stats,
    add_stock_to_list,
    remove_stock_from_list,
    get_stock_list,
    is_stock_in_list,
    clear_stock_list,
    upstox_set,
)
from src.upstox_config import get_status as token_status, validate_token as validate_token_svc, check_token, get_token as get_raw_token, get_api_key, get_api_secret
from src.upstox_fetcher import fetch_all_stocks, instrument_keys_loaded
from src.settings import get_all as settings_get_all, get as settings_get, set as settings_set, reset_category, reset_all
from src.scanner import ContinuationScanner, ReversalScanner, get_default_params, get_default_reversal_params
from src.market_breadth import calculate_breadth
from src.db import (add_trade_log, get_trade_logs, update_trade_log, delete_trade_log,
                    get_daily_pnl, get_yearly_pnl, update_get_trade_stats, get_capital_stats,
                    get_all_breadth, get_breadth_date_keys)
from src.iep_fetcher import iep_fetcher
from src.volume_profile import volume_profile_calculator
from src.volume_fetcher import volume_fetcher

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On server start, rebuild the cache index if it's empty."""
    stats = get_cache_stats()
    if stats["stock_count"] == 0:
        logger.info("Cache index is empty — rebuilding from .pkl files...")
        count = cache_manager.rebuild_index()
        logger.info(f"Cache index rebuilt: {count} entries")
    else:
        logger.info(f"Cache index has {stats['stock_count']} entries — no rebuild needed")
    yield


app = FastAPI(title="TradeStack", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory operation tracking ---
active_operations: dict = {}


class UpdateRequest(BaseModel):
    date: Optional[str] = None


# --- Health ---

@app.get("/")
def root():
    return {"status": "ok", "service": "TradeStack"}

@app.get("/health")
def health():
    return {"status": "healthy"}


# --- Data Pipeline API ---

@app.post("/api/data/update-bhavcopy")
def trigger_update(background_tasks: BackgroundTasks, request: Optional[UpdateRequest] = None):
    """Start a bhavcopy update in the background. Returns operation_id for progress polling.
    Matches working project behavior: if no date specified, fill all gaps from last cache to today."""
    operation_id = f"bhavcopy_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    if request and request.date:
        target = date.fromisoformat(request.date)
        active_operations[operation_id] = {
            "operation_id": operation_id,
            "type": "bhavcopy_update",
            "status": "starting",
            "progress": 0,
            "message": f"Initializing update for {target}",
            "target_date": target.isoformat(),
            "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Starting bhavcopy update for {target}..."],
        }
        background_tasks.add_task(_run_bhavcopy_update, operation_id, target)
        return {"status": "started", "operation_id": operation_id, "target_date": target.isoformat()}

    gaps = find_cache_gaps()
    if gaps:
        active_operations[operation_id] = {
            "operation_id": operation_id,
            "type": "fill_gaps",
            "status": "starting",
            "progress": 0,
            "message": f"Filling {len(gaps)} gap(s): {gaps[0]} to {gaps[-1]}",
            "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(gaps)} gap(s) - filling..."],
        }
        background_tasks.add_task(_run_fill_gaps, operation_id)
        return {"status": "started", "operation_id": operation_id, "mode": "fill_gaps"}

    # No gaps found — cache is up to date through yesterday.
    # If today is not a trading day or today's data is cached already, we're done.
    latest_cache = cache_manager.get_latest_cache_date()
    today = date.today()
    if latest_cache and latest_cache >= today:
        return {"status": "up_to_date", "message": "Cache is already up to date"}
    if today.weekday() >= 5 or today in get_nse_holidays():
        return {"status": "up_to_date", "message": "Today is not a trading day. Cache is up to date."}

    # Today is a trading day — try to download bhavcopy (may be available after ~7 PM)
    target = today
    # Make an upfront check so we can return instantly instead of starting a
    # background task that will fail a minute later.
    from src.nse_fetcher import download_bhavcopy
    bc = download_bhavcopy(target)
    if bc is None or bc.empty:
        return {"status": "up_to_date", "message": "Today's market data not yet available (typically after 7 PM). Cache is up to date."}

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "bhavcopy_update",
        "status": "starting",
        "progress": 0,
        "message": f"Initializing update for {target}",
        "target_date": target.isoformat(),
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Starting bhavcopy update for {target}..."],
    }
    background_tasks.add_task(_run_bhavcopy_update, operation_id, target)
    return {"status": "started", "operation_id": operation_id, "target_date": target.isoformat()}


@app.get("/api/data/status/{operation_id}")
def get_operation_status(operation_id: str):
    """Poll the progress of a bhavcopy update operation."""
    op = active_operations.get(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


@app.get("/api/data/cache-info")
def get_cache_info():
    """Return high-level cache statistics."""
    stats = cache_manager.stats()
    stats["stock_count"] = len(cache_manager.list_symbols())
    stats["cache_dir"] = str(cache_manager.cache_dir)
    return stats


@app.get("/api/data/cache-dates")
def list_cache_dates():
    """Return all unique dates present across cached stocks."""
    return {"dates": get_cache_dates(), "count": len(get_cache_dates())}


@app.get("/api/data/cache-freshness")
def check_cache_freshness():
    """Compare latest cache date with latest NSE trading date.

    Returns isFresh, both dates, and a human-readable message.
    """
    latest_cache = cache_manager.get_latest_cache_date()
    latest_nse = get_latest_trading_date()

    is_fresh = (
        latest_cache is not None
        and latest_nse is not None
        and latest_cache >= latest_nse
    )

    if latest_nse is None:
        message = "Could not determine latest NSE trading date"
        days_behind = None
    elif latest_cache is None:
        message = "Cache is empty — no data available"
        days_behind = None
    elif is_fresh:
        message = f"Cache is fresh (latest: {latest_cache})"
        days_behind = 0
    else:
        diff = (latest_nse - latest_cache).days
        days_behind = diff
        message = f"Cache is stale — latest cache: {latest_cache}, NSE latest: {latest_nse} ({diff} day(s) behind)"

    return {
        "is_fresh": is_fresh,
        "latest_cache_date": latest_cache.isoformat() if latest_cache else None,
        "latest_nse_date": latest_nse.isoformat() if latest_nse else None,
        "days_behind": days_behind,
        "message": message,
    }


@app.get("/api/data/symbols")
def list_symbols():
    """Return all cached stock symbols."""
    return {"symbols": cache_manager.list_symbols(), "count": len(cache_manager.list_symbols())}


@app.post("/api/data/fill-gaps")
def trigger_fill_gaps(background_tasks: BackgroundTasks):
    """Fill all missing cache dates in the background."""
    operation_id = f"fillgaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "fill_gaps",
        "status": "starting",
        "progress": 0,
        "message": "Initializing gap fill",
    }

    background_tasks.add_task(_run_fill_gaps, operation_id)
    return {"status": "started", "operation_id": operation_id}


# --- Token Management API ---


class TokenRequest(BaseModel):
    token: str


@app.get("/api/token/status")
def get_token_status():
    """Return current token status (exists, masked, updated_at)."""
    return token_status()


@app.post("/api/token/validate")
def validate_upstox_token(request: TokenRequest):
    """Save and validate an Upstox access token."""
    result = validate_token_svc(request.token)
    return result


@app.get("/api/token/check")
def check_upstox_token():
    """Read-only validation of the stored token (no save)."""
    result = check_token()
    return result


@app.get("/api/token/raw")
def get_raw_upstox_token():
    """Return the raw access token (for streamer use)."""
    token = get_raw_token()
    if not token:
        return {"token": None, "exists": False}
    return {"token": token, "exists": True}


# --- Historical Data Download API ---


class BatchHistoryRequest(BaseModel):
    symbols: list[str]
    days: int = 200


@app.post("/api/data/batch-stock-history")
def batch_stock_history(body: BatchHistoryRequest):
    """Return OHLCV history for multiple symbols from cache (no DB).
    Each response includes candles array + SMA20 line data.
    """
    import pandas as pd
    result: dict = {}
    for sym in body.symbols:
        try:
            df = cache_manager.load(sym)
            if df is None or df.empty:
                result[sym] = {"candles": [], "sma": []}
                continue
            df = df.tail(body.days)
            close = df["close"].values
            sma20 = pd.Series(close).rolling(window=20).mean().values
            dates = [str(d.date()) if hasattr(d, "date") else str(d) for d in df.index]
            candles = [
                {"date": dates[i], "open": float(r["open"]), "high": float(r["high"]),
                 "low": float(r["low"]), "close": float(r["close"]), "volume": int(r["volume"])}
                for i, (_, r) in enumerate(df.iterrows())
            ]
            sma = [
                {"date": dates[i], "value": float(v)}
                for i, v in enumerate(sma20) if not pd.isna(v)
            ]
            result[sym] = {"candles": candles, "sma": sma}
        except Exception as e:
            result[sym] = {"candles": [], "sma": [], "error": str(e)}
    return {"data": result}


@app.post("/api/data/download-historical")
def trigger_historical_download(background_tasks: BackgroundTasks):
    """Start downloading 180 calendar days of historical data for all stocks."""
    operation_id = f"hist_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    if not instrument_keys_loaded():
        return {
            "status": "error",
            "message": "Instrument mapping file (complete.csv.gz) not found or empty. Please copy it to data/",
        }

    token = token_status()
    if not token["exists"]:
        return {"status": "error", "message": "No Upstox token configured. Please update your token first."}

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "historical_download",
        "status": "starting",
        "progress": 0,
        "message": "Initializing historical data download...",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Starting historical data download (180 calendar days)..."],
    }

    background_tasks.add_task(_run_historical_download, operation_id)
    return {"status": "started", "operation_id": operation_id}


# --- Instrument Key API ---


_INSTRUMENT_MAP: dict[str, str] | None = None


def _load_instrument_map():
    global _INSTRUMENT_MAP
    if _INSTRUMENT_MAP is not None:
        return
    from pathlib import Path
    import pandas as pd
    csv = Path(__file__).resolve().parent.parent / "data" / "complete.csv.gz"
    if not csv.exists():
        _INSTRUMENT_MAP = {}
        return
    df = pd.read_csv(csv, compression="gzip")
    eq = df[df["instrument_key"].str.startswith("NSE_EQ", na=False)]
    _INSTRUMENT_MAP = dict(zip(eq["tradingsymbol"], eq["instrument_key"]))


@app.post("/api/instrument-keys")
def resolve_instrument_keys(body: dict):
    """Resolve stock symbols to NSE_EQ instrument keys. Accepts {symbols: ["RELIANCE", ...]}."""
    _load_instrument_map()
    symbols: list[str] = body.get("symbols", [])
    result = {}
    for s in symbols:
        key = _INSTRUMENT_MAP.get(s.upper()) if _INSTRUMENT_MAP else None
        if key:
            result[s] = key
    return {"keys": result, "total": len(result), "missing": len(symbols) - len(result)}


# --- Settings API ---


class SettingUpdate(BaseModel):
    value: str


@app.get("/api/settings")
def list_settings():
    """Return all settings with metadata, merging real credential values."""
    settings = settings_get_all()
    for s in settings:
        if s["key"] == "upstox_access_token":
            real_token = get_raw_token()
            if real_token:
                s["value"] = real_token
        elif s["key"] == "upstox_api_key":
            s["value"] = get_api_key()
        elif s["key"] == "upstox_api_secret":
            s["value"] = get_api_secret()
    return {"settings": settings}


@app.get("/api/settings/{key}")
def get_setting(key: str):
    """Get a single setting."""
    val = settings_get(key)
    if val is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": key, "value": val}


@app.put("/api/settings/{key}")
def update_setting(key: str, body: SettingUpdate):
    """Update a single setting value, syncing credentials to their real storage."""
    existing = settings_get(key)
    if existing is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    settings_set(key, body.value)
    if key == "upstox_access_token":
        upstox_set("access_token", body.value)
    return {"status": "saved", "key": key, "value": body.value}


@app.post("/api/settings/reset/{category}")
def reset_settings_category(category: str):
    """Reset a settings category to defaults."""
    reset_category(category)
    return {"status": "reset", "category": category}


@app.post("/api/settings/reset")
def reset_all_settings():
    """Reset ALL settings to defaults."""
    reset_all()
    return {"status": "reset", "count": len(settings_get_all())}


# --- Scanner API ---


class ScanFilters(BaseModel):
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    near_ma_threshold: Optional[float] = None
    near_ma_direction: Optional[str] = None
    max_body_percentage: Optional[float] = None
    rev_decline_days_min: Optional[int] = None
    rev_decline_days_max: Optional[int] = None
    rev_min_decline_pct: Optional[float] = None


class ScanRequest(BaseModel):
    date: Optional[str] = None
    filters: Optional[ScanFilters] = None


@app.post("/api/scanner/continuation")
def trigger_continuation_scan(request: Optional[ScanRequest] = None):
    """Run continuation scan in background thread."""
    operation_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    params = get_default_params()
    if request and request.filters:
        f = request.filters
        if f.min_price is not None:
            params["price_min"] = f.min_price
        if f.max_price is not None:
            params["price_max"] = f.max_price
        if f.near_ma_threshold is not None:
            params["near_ma_threshold"] = f.near_ma_threshold
        if f.near_ma_direction is not None:
            params["near_ma_direction"] = f.near_ma_direction
        if f.max_body_percentage is not None:
            params["max_body_percentage"] = f.max_body_percentage

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "continuation_scan",
        "status": "starting",
        "progress": 0,
        "message": "Scanning...",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Starting continuation scan..."],
    }

    t = threading.Thread(target=_run_continuation_scan, args=(operation_id, params), daemon=True)
    t.start()
    return {"status": "started", "operation_id": operation_id}


@app.post("/api/scanner/reversal")
def trigger_reversal_scan(request: Optional[ScanRequest] = None):
    """Run reversal scan in background thread."""
    operation_id = f"rev_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    params = get_default_reversal_params()
    if request and request.filters:
        f = request.filters
        if f.min_price is not None:
            params["price_min"] = f.min_price
        if f.max_price is not None:
            params["price_max"] = f.max_price
        if f.rev_decline_days_min is not None:
            params["rev_decline_days_min"] = f.rev_decline_days_min
        if f.rev_decline_days_max is not None:
            params["rev_decline_days_max"] = f.rev_decline_days_max
        if f.rev_min_decline_pct is not None:
            params["rev_min_decline_pct"] = f.rev_min_decline_pct

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "reversal_scan",
        "status": "starting",
        "progress": 0,
        "message": "Scanning...",
        "logs": [f"[{datetime.now().strftime('%H:%M:%S')}] Starting reversal scan..."],
    }

    t = threading.Thread(target=_run_reversal_scan, args=(operation_id, params), daemon=True)
    t.start()
    return {"status": "started", "operation_id": operation_id}


@app.get("/api/scanner/status/{operation_id}")
def get_scan_status(operation_id: str):
    """Poll scan progress."""
    op = active_operations.get(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return op


# --- Stock List API ---


class StockListAddRequest(BaseModel):
    symbol: str
    close: Optional[float] = None
    trend_context: Optional[str] = None
    period: Optional[int] = None
    depth_pct: Optional[float] = None


@app.get("/api/stock-list/{list_type}")
def list_stock_list(list_type: str):
    """Return all stocks in a trading list."""
    stocks = get_stock_list(list_type)
    return {"stocks": stocks, "count": len(stocks)}


@app.get("/api/stock-list/{list_type}/resolved")
def list_stock_list_resolved(list_type: str):
    """Return stock list with close values resolved from live cache.

    Unlike the plain endpoint (which returns the frozen snapshot),
    this reads the latest close from each stock's .pkl file at call time.
    Falls back to stored close if cache is unavailable.
    """
    stocks = get_stock_list(list_type)
    resolved = []
    for s in stocks:
        latest_close = cache_manager.get_last_close(s["symbol"])
        resolved.append({
            **s,
            "close": latest_close if latest_close is not None else s.get("close"),
        })
    return {"stocks": resolved, "count": len(resolved)}


@app.post("/api/stock-list/{list_type}")
def add_to_stock_list(list_type: str, body: StockListAddRequest):
    """Add a stock to a trading list."""
    is_new = add_stock_to_list(
        list_type, body.symbol,
        close=body.close,
        trend_context=body.trend_context,
        period=body.period,
        depth_pct=body.depth_pct,
    )
    return {"status": "added" if is_new else "updated", "symbol": body.symbol.upper()}


@app.delete("/api/stock-list/{list_type}/{symbol}")
def remove_from_stock_list(list_type: str, symbol: str):
    """Remove a stock from a trading list."""
    existed = remove_stock_from_list(list_type, symbol)
    if not existed:
        raise HTTPException(status_code=404, detail="Stock not found in list")
    return {"status": "removed", "symbol": symbol.upper()}


@app.get("/api/stock-list/{list_type}/check/{symbol}")
def check_stock_in_list(list_type: str, symbol: str):
    """Check if a stock is in a trading list."""
    return {"in_list": is_stock_in_list(list_type, symbol)}


@app.delete("/api/stock-list/{list_type}")
def clear_stock_list_endpoint(list_type: str):
    """Remove all stocks from a trading list."""
    count = clear_stock_list(list_type)
    return {"status": "cleared", "list_type": list_type, "count": count}


# --- Market Breadth API ---


@app.get("/api/breadth/data")
def get_breadth_data():
    """Get cached breadth data from SQLite."""
    try:
        rows = get_all_breadth()
        if not rows:
            return {"data": [], "total_dates": 0, "last_updated": None, "message": "No breadth data available. Click 'Update' to calculate."}

        results = []
        for row in rows:
            results.append({
                "date": row["date_key"],
                "up_4_5_pct": row["up_4_5"],
                "down_4_5_pct": row["down_4_5"],
                "up_20_pct_5d": row["up_20_5d"],
                "down_20_pct_5d": row["down_20_5d"],
                "above_20ma": row["above_20ma"],
                "below_20ma": row["below_20ma"],
                "above_50ma": row["above_50ma"],
                "below_50ma": row["below_50ma"],
            })

        return {"data": results, "total_dates": len(results), "last_updated": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Failed to load breadth data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/breadth/update")
def trigger_breadth_update():
    """Run breadth calculation in background thread."""
    operation_id = f"breadth_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

    active_operations[operation_id] = {
        "operation_id": operation_id,
        "type": "breadth_update",
        "status": "starting",
        "progress": 0,
        "message": "Starting breadth analysis...",
    }

    t = threading.Thread(target=_run_breadth_update, args=(operation_id,), daemon=True)
    t.start()
    return {"status": "started", "operation_id": operation_id}


# --- Pre-market Preparation API (IEP + VAH) ---


class PrepIEPRequest(BaseModel):
    symbols: list[str]


class PrepVolumeProfileRequest(BaseModel):
    symbols: list[str]


@app.post("/api/prep/iep")
def fetch_prep_iep(request: PrepIEPRequest):
    """Batch fetch IEP (Indicative Equilibrium Price) for pre-market opening prices."""
    token = get_raw_token()
    if not token:
        raise HTTPException(status_code=401, detail="No Upstox token configured")
    prices = iep_fetcher.fetch_iep_batch(request.symbols, token)
    return {"prices": prices, "count": len(prices), "total_requested": len(request.symbols)}


@app.post("/api/prep/volume-profile")
def calculate_prep_volume_profile(request: PrepVolumeProfileRequest):
    """Calculate VAH for symbols using previous trading day's intraday data."""
    token = get_raw_token()
    if not token:
        raise HTTPException(status_code=401, detail="No Upstox token configured")

    # Load VAH settings from DB
    from src.settings import get as settings_get
    bin_size = float(settings_get("vah_bin_size") or 0.05)
    value_area_pct = float(settings_get("vah_value_area_pct") or 70) / 100
    volume_profile_calculator.bin_size = bin_size
    volume_profile_calculator.value_area_pct = value_area_pct

    vah = volume_profile_calculator.calculate_vah_for_stocks(request.symbols, token)
    return {"vah": vah, "count": len(vah), "total_requested": len(request.symbols)}


@app.get("/api/prep/previous-trading-day")
def get_previous_trading_day():
    """Return the last trading day with available intraday data."""
    token = get_raw_token()
    if not token:
        raise HTTPException(status_code=401, detail="No Upstox token configured")
    prev_day = volume_profile_calculator.get_previous_trading_day(token)
    if prev_day is None:
        raise HTTPException(status_code=404, detail="No previous trading day found")
    return {"date": prev_day.isoformat()}


class VolumeBaselinesRequest(BaseModel):
    symbols: list[str]


@app.post("/api/prep/volume-baselines")
def get_volume_baselines(request: VolumeBaselinesRequest):
    """Get 10-day mean volume baselines from cache for each symbol."""
    baselines: dict[str, float] = {}
    svro_days = int(settings_get("svro_baseline_days") or 10)
    vol_fallback = float(settings_get("volume_min") or 1000000)
    for sym in request.symbols:
        try:
            df = cache_manager.load(sym)
            if df is not None and not df.empty and "volume" in df.columns and len(df) >= svro_days:
                baselines[sym] = float(df["volume"].tail(svro_days).mean())
            else:
                baselines[sym] = vol_fallback
        except Exception:
            baselines[sym] = vol_fallback
    return {"baselines": baselines, "count": len(baselines)}


@app.post("/api/prep/current-volume")
def get_current_volume(request: VolumeBaselinesRequest):
    """Get today's cumulative live volume from Upstox for each symbol."""
    token = get_raw_token()
    if not token:
        return {"volumes": {}, "error": "No token configured"}
    volumes: dict[str, float] = {}
    for sym in request.symbols:
        vol = volume_fetcher.fetch_current_volume(sym, token)
        volumes[sym] = vol if vol > 0 else 0
    return {"volumes": volumes, "count": len(volumes)}


# --- Trade Log API ---


class TradeLogEntry(BaseModel):
    symbol: str
    instrument_key: str = ""
    entry_price: float
    entry_sl: float | None = None
    entry_time: str
    entry_date: str
    session_id: str
    trade_type: str = "continuation"
    quantity: int = 100


@app.post("/api/trades/log-entry")
def log_trade_entry(body: TradeLogEntry):
    """Record a paper trade entry from the live trader."""
    tid = add_trade_log(
        symbol=body.symbol,
        instrument_key=body.instrument_key,
        entry_price=body.entry_price,
        entry_sl=body.entry_sl,
        entry_time=body.entry_time,
        entry_date=body.entry_date,
        session_id=body.session_id,
        trade_type=body.trade_type,
        quantity=body.quantity,
    )
    return {"status": "logged", "id": tid}


@app.get("/api/trades/list")
def list_trades(start_date: str | None = None, end_date: str | None = None):
    """Return all trade log entries, optional date filtering."""
    trades = get_trade_logs(start_date=start_date, end_date=end_date)
    return {"trades": trades, "count": len(trades)}


@app.get("/api/trades/daily-pnl")
def daily_pnl(year: int, month: int):
    """Return per-day net P&L and trade count for heatmap."""
    return {"days": get_daily_pnl(year, month)}


@app.get("/api/trades/yearly-pnl")
def yearly_pnl(year: int):
    """Return per-day net P&L and trade count for the full year."""
    return {"days": get_yearly_pnl(year)}


@app.get("/api/trades/stats")
def trade_stats():
    """Return cumulative trade statistics."""
    return update_get_trade_stats()


@app.get("/api/trades/capital-stats")
def capital_stats():
    """Return capital statistics (initial_capital, realized_pnl, available_capital, open_position_value)."""
    return get_capital_stats()


class TradeUpdateBody(BaseModel):
    exit_date: str | None = None
    exit_price: float | None = None


@app.put("/api/trades/{trade_id}")
def edit_trade(trade_id: int, body: TradeUpdateBody):
    """Update a trade log entry with exit price (auto-calculates P&L) and exit date."""
    update_trade_log(trade_id, exit_date=body.exit_date, exit_price=body.exit_price)
    return {"status": "updated"}


@app.delete("/api/trades/{trade_id}")
def remove_trade(trade_id: int):
    """Delete a trade log entry."""
    delete_trade_log(trade_id)
    return {"status": "deleted"}


# --- Background tasks ---

def _run_bhavcopy_update(operation_id: str, target_date: date):
    try:
        op = active_operations[operation_id]
        op["status"] = "running"
        op["message"] = f"Downloading bhavcopy for {target_date}..."

        def progress(pct: Optional[float] = None, msg: Optional[str] = None, log_entry: Optional[str] = None):
            if log_entry:
                _log(op, log_entry)
            if pct is not None:
                op["progress"] = pct
            if msg is not None:
                op["message"] = msg

        batch_size = int(settings_get("bhavcopy_batch_size") or 100)
        result = update_cache_for_date(target_date, batch_size=batch_size, progress_callback=progress)

        error = result.get("error")
        if error:
            _log(op, f"Failed — {error}")
            op.update(status="error", progress=100, message=error, error=error, result=result)
        else:
            _log(op, f"Done — {result['updated']} updated, {result['skipped']} skipped")
            op.update(
                status="completed",
                progress=100,
                message=f"Done — {result['updated']} updated, {result['skipped']} skipped",
                result=result,
            )
    except Exception as e:
        logger.error(f"Bhavcopy update failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


def _run_fill_gaps(operation_id: str):
    try:
        op = active_operations[operation_id]
        op["status"] = "running"
        gaps = find_cache_gaps()
        op["message"] = f"Filling {len(gaps)} gap(s)..."

        def progress(pct=None, msg=None, log_entry=None):
            if log_entry:
                _log(op, log_entry)
            if pct is not None:
                op["progress"] = pct
            if msg is not None:
                op["message"] = msg

        batch_size = int(settings_get("bhavcopy_batch_size") or 100)
        results = fill_cache_gaps(batch_size=batch_size, progress_callback=progress)

        total_updated = sum(r.get("updated", 0) for r in results)
        total_failed_stocks = sum(r.get("failed", 0) for r in results)
        total_skipped = sum(r.get("skipped", 0) for r in results)
        failed_dates = [r for r in results if r.get("error")]
        skipped_dates = [r for r in results if r.get("error")]

        if total_failed_stocks:
            _log(op, f"Done — {total_updated} updated, {total_skipped} skipped, {total_failed_stocks} stock(s) failed")
            for r in results:
                if r.get("failed", 0):
                    _log(op, f"  {r['date']}: {r['failed']} stock(s) failed")
        elif failed_dates:
            for fd in failed_dates:
                _log(op, f"  Skipped {fd['date']}: {fd['error']}")
            _log(op, f"Filled {len(results) - len(failed_dates)} date(s), {total_updated} stocks updated")
        else:
            _log(op, f"Filled {len(results)} date(s), {total_updated} stocks updated")

        op.update(
            status="completed",
            progress=100,
            result={
                "dates_filled": len(results),
                "total_updated": total_updated,
                "total_failed_stocks": total_failed_stocks,
                "total_skipped": total_skipped,
                "details": results,
            },
        )
    except Exception as e:
        logger.error(f"Gap fill failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


def _run_historical_download(operation_id: str):
    try:
        from src.upstox_config import get_token

        token = get_token()
        if not token:
            active_operations[operation_id].update(status="error", message="No token available")
            return

        op = active_operations[operation_id]
        op["status"] = "running"

        def progress(pct: Optional[float] = None, msg: Optional[str] = None, log_entry: Optional[str] = None):
            if log_entry:
                _log(op, log_entry)
            if pct is not None:
                op["progress"] = pct
            if msg is not None:
                op["message"] = msg

        download_days = int(settings_get("historical_download_days") or 180)
        result = fetch_all_stocks(token, days=download_days, progress_callback=progress)

        _log(op, "Rebuilding SQLite cache index from .pkl files...")
        op["message"] = "Rebuilding cache index..."
        idx_count = cache_manager.rebuild_index()
        _log(op, f"Cache index rebuilt: {idx_count} entries")

        op.update(
            status="completed",
            progress=100,
            message=f"Done — {result['updated']} updated, {result['failed']} failed out of {result['total']}",
            result=result,
            index_rebuilt=idx_count,
        )
    except Exception as e:
        logger.error(f"Historical download failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


def _run_continuation_scan(operation_id: str, params: dict):
    try:
        op = active_operations[operation_id]
        op["status"] = "running"

        def progress(pct: int, msg: str):
            op["progress"] = pct
            op["message"] = msg

        scanner = ContinuationScanner(params)
        results = scanner.run(progress_callback=progress)

        op.update(
            status="completed",
            progress=100,
            message=f"Scan complete — {len(results)} results",
            result={"count": len(results), "results": results},
        )
    except Exception as e:
        logger.error(f"Continuation scan failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


def _run_reversal_scan(operation_id: str, params: dict):
    try:
        op = active_operations[operation_id]
        op["status"] = "running"

        def progress(pct: int, msg: str):
            op["progress"] = pct
            op["message"] = msg

        scanner = ReversalScanner(params)
        results = scanner.run(progress_callback=progress)

        op.update(
            status="completed",
            progress=100,
            message=f"Scan complete — {len(results)} results",
            result={"count": len(results), "results": results},
        )
    except Exception as e:
        logger.error(f"Reversal scan failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


def _run_breadth_update(operation_id: str):
    try:
        op = active_operations[operation_id]
        op["status"] = "running"

        def progress(pct: int, msg: str):
            op["progress"] = pct
            op["message"] = msg

        results = calculate_breadth(progress_callback=progress)

        op.update(
            status="completed",
            progress=100,
            message=f"Breadth analysis completed: {len(results)} dates",
            result={"data": results, "total_dates": len(results), "last_updated": datetime.now().isoformat()},
        )
    except Exception as e:
        logger.error(f"Breadth update failed: {e}")
        active_operations[operation_id].update(status="error", message=str(e), error=str(e))


# --- Entry point ---

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("server:app", host="127.0.0.1", port=8001, reload=False)
