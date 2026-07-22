"""
NSE Bhavcopy Fetcher for TradeStack
Downloads and processes NSE bhavcopy CSV files with fallback strategies.
"""

import io
import logging
import time
import zipfile
from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


# Module-level session for HTTP connection pooling (reuse TCP connections)
_shared_session: Optional[requests.Session] = None


def _get_session() -> requests.Session:
    """Return the shared HTTP session (connection pooling via keep-alive)."""
    global _shared_session
    if _shared_session is None:
        s = requests.Session()
        s.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/zip,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=4,
            pool_maxsize=8,
            max_retries=2,
        )
        s.mount("https://", adapter)
        _shared_session = s
    return _shared_session


def _standardize(df: pd.DataFrame, target_date: date, source: str) -> Optional[pd.DataFrame]:
    """Convert raw bhavcopy DataFrame into a standardized format."""
    col_map = {
        "TckrSymb": "symbol", "SYMBOL": "symbol",
        "SctySrs": "series",
        "OpnPric": "open", "OPEN": "open",
        "HghPric": "high", "HIGH": "high",
        "LwPric": "low", "LOW": "low",
        "ClsPric": "close", "CLOSE": "close",
        "TtlTradgVol": "volume", "TOTTRDQTY": "volume",
        "TradDt": "date",
    }
    df = df.rename(columns=col_map)

    if "series" in df.columns:
        df = df[df["series"] == "EQ"]

    if "date" not in df.columns:
        df["date"] = target_date
    else:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    cols = [c for c in ["symbol", "date", "open", "high", "low", "close", "volume"] if c in df.columns]
    if len(cols) < 7:
        logger.warning("Missing required columns in bhavcopy data")
        return None

    df = df[cols]
    df["volume"] = df["volume"].astype(int)
    df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)

    logger.info(f"Standardized {len(df)} stocks from {source}")
    return df


def _download_zip(url: str, session: requests.Session) -> Optional[pd.DataFrame]:
    """Download a ZIP, extract CSV, return DataFrame."""
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
        if not csv_files:
            return None
        with zf.open(csv_files[0]) as f:
            try:
                return pd.read_csv(f, encoding="utf-8")
            except UnicodeDecodeError:
                f.seek(0)
                return pd.read_csv(f, encoding="cp1252")


def download_bhavcopy(target_date: date) -> Optional[pd.DataFrame]:
    """
    Download bhavcopy for a given date using UDiFF URL.
    Returns standardized DataFrame or None.

    archives.nseindia.com (historical) removed 2026-07-20 - server returns 503 for all dates.
    """
    yyyymmdd = target_date.strftime("%Y%m%d")
    url = _url_udiff(yyyymmdd)
    session = _get_session()

    for attempt in range(3):
        try:
            logger.info(f"Trying direct-udiff for {target_date} (attempt {attempt + 1})")
            df = _download_zip(url, session)
            if df is not None and len(df) > 500:
                return _standardize(df, target_date, "direct-udiff")
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed for {target_date}: {e}")
            if attempt < 2:
                time.sleep(5)
            continue

    logger.error(f"Failed to download bhavcopy for {target_date}")
    return None


def _url_udiff(yyyymmdd: str) -> str:
    return (
        f"https://nsearchives.nseindia.com/content/cm/"
        f"BhavCopy_NSE_CM_0_0_0_{yyyymmdd}_F_0000.csv.zip"
    )




def get_stock_row(symbol: str, bhavcopy_df: pd.DataFrame) -> Optional[pd.Series]:
    """Extract a single stock's row from a bhavcopy DataFrame."""
    match = bhavcopy_df[bhavcopy_df["symbol"].str.upper() == symbol.upper()]
    if match.empty:
        return None
    return match.iloc[0]


# ---------------------------------------------------------------------------
# NSE Trading Calendar (holiday-master API)
# ---------------------------------------------------------------------------

_HOLIDAY_URL = "https://www.nseindia.com/api/holiday-master?type=trading"
_HOLIDAY_CACHE_TTL = 86400  # 24 hours
_holiday_cache: tuple[float, set[date]] | None = None


def _fetch_nse_holidays() -> set[date]:
    """Hit the NSE holiday-master API and return trading holidays as a set of dates."""
    try:
        session = _get_session()
        resp = session.get(_HOLIDAY_URL, timeout=15, headers={
            "Accept": "application/json, */*",
            "Referer": "https://www.nseindia.com/",
        })
        resp.raise_for_status()
        data = resp.json()
        holidays: set[date] = set()
        for h in data.get("CM", []):
            raw = h.get("tradingDate", "")
            if not raw:
                continue
            try:
                d = datetime.strptime(raw.strip(), "%d-%b-%Y").date()
                holidays.add(d)
            except ValueError:
                pass
        logger.info(f"Fetched {len(holidays)} NSE trading holidays from API")
        return holidays
    except Exception as e:
        logger.warning(f"Failed to fetch NSE holidays: {e}")
        return set()


def get_nse_holidays() -> set[date]:
    """Return NSE trading holidays, cached for 24 hours."""
    global _holiday_cache
    now = time.time()
    if _holiday_cache is None or now - _holiday_cache[0] > _HOLIDAY_CACHE_TTL:
        _holiday_cache = (now, _fetch_nse_holidays())
    return _holiday_cache[1]


def _cache_has_date(target: date, latest_cache_date: Optional[date]) -> bool:
    """Check if target date is already available in local cache (no HTTP needed)."""
    return latest_cache_date is not None and target <= latest_cache_date


def get_latest_trading_date(max_lookback: int = 10) -> Optional[date]:
    """Return the most recent NSE equity trading date.

    Two-pass strategy:
      1. Fast path — check local cache first (no HTTP).
      2. Slow path — probe NSE bhavcopy download for remaining candidates.

    Returns None if no trading date could be determined after max_lookback days.
    """
    today = date.today()
    holidays = get_nse_holidays()

    from .cache_manager import cache_manager
    latest_cache = cache_manager.get_latest_cache_date()

    for offset in range(1, max_lookback + 1):
        d = today - timedelta(days=offset)
        if d.weekday() >= 5:
            continue
        if d in holidays:
            continue
        # Fast path: already in cache, no HTTP needed
        if _cache_has_date(d, latest_cache):
            return d
        # Slow path: probe bhavcopy download
        try:
            bc = download_bhavcopy(d)
            if bc is not None and len(bc) > 500:
                return d
        except Exception:
            continue

    return None
