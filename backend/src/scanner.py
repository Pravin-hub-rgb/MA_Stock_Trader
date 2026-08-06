"""
Scanner for TradeStack
Continuation and reversal analysis with zig-zag pattern detection
"""

import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Optional, Callable
import pandas as pd

from src.cache_manager import cache_manager
from src.indicators import compute_all_indicators

logger = logging.getLogger(__name__)


def _detect_scan_date() -> Optional[date]:
    """Find the latest trading date from first available cached stock."""
    symbols = cache_manager.list_symbols()
    for symbol in symbols:
        try:
            data = cache_manager.load(symbol)
            if data is not None and not data.empty:
                d = data.index[-1]
                if hasattr(d, "date"):
                    d = d.date()
                return d
        except Exception:
            continue
    return None


def _stock_has_date(data: pd.DataFrame, target: date) -> bool:
    """Check if a stock's data contains a specific trading date (old: _get_all_cached_stocks_with_data check)."""
    ts = pd.Timestamp(target)
    if ts in data.index:
        return True
    for idx in data.index:
        if hasattr(idx, "date") and idx.date() == target:
            return True
    return False


def _run_chunk(symbols: list, params: dict, scan_date: Optional[date], mode: str) -> list[dict]:
    """Process a chunk of symbols in a worker process (module-level for pickling)."""
    from src.cache_manager import cache_manager
    from src.indicators import compute_all_indicators

    is_continuation = mode == "continuation"
    min_rows = params.get("cont_min_data_rows" if is_continuation else "rev_min_data_rows", 50)

    if is_continuation:
        scanner = ContinuationScanner(params)
    else:
        scanner = ReversalScanner(params)

    ind_params = {
        "sma_period": params.get("sma_period", 20),
        "adr_period": params.get("adr_period", 14),
        "high_low_period": params.get("high_low_period", 20),
        "ma_angle_points": params.get("ma_angle_points", 5),
        "price_change_periods": params.get("price_change_periods", [1, 5, 20]),
    }

    results = []
    for symbol in symbols:
        try:
            data = cache_manager.load(symbol)
            if data is None or len(data) < min_rows:
                continue
            if scan_date is not None and not _stock_has_date(data, scan_date):
                continue

            if scan_date is not None:
                data = data[data.index <= pd.Timestamp(scan_date)]
                if len(data) < min_rows:
                    continue

            data = compute_all_indicators(data, indicator_params=ind_params)
            latest = data.iloc[-1]

            if scanner._passes_filters(latest, data):
                if is_continuation:
                    hit = scanner._analyze_pattern(data)
                else:
                    hit = scanner._analyze_pattern(data, scan_date)
                if hit is not None:
                    results.append({
                        **hit,
                        "symbol": symbol,
                        "close": round(float(latest["close"]), 2),
                    })
        except Exception:
            pass
    return results


class ContinuationScanner:
    def __init__(self, params: dict):
        self.params = params

    def run(self, progress_callback: Optional[Callable] = None, num_workers: Optional[int] = None, scan_date: Optional[date] = None) -> list[dict]:
        if scan_date is None:
            scan_date = _detect_scan_date()
        symbols = cache_manager.list_symbols()
        total = len(symbols)
        if total == 0:
            return []

        if num_workers is None:
            num_workers = min(os.cpu_count() or 4, total)

        chunk_size = max(1, total // num_workers)
        chunks = [symbols[i:i + chunk_size] for i in range(0, total, chunk_size)]

        results = []
        processed = 0

        with ProcessPoolExecutor(max_workers=num_workers) as pool:
            future_map = {pool.submit(_run_chunk, ch, self.params, scan_date, "continuation"): len(ch) for ch in chunks}
            for future in as_completed(future_map):
                chunk_len = future_map[future]
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    logger.error(f"Continuation chunk failed: {e}")
                processed += chunk_len
                if progress_callback:
                    pct = int((processed / total) * 100)
                    progress_callback(pct, f"Scanned {processed}/{total} stocks, found {len(results)} candidates")

        results.sort(key=lambda r: r["symbol"])
        return results

    def _passes_filters(self, latest: pd.Series, data: pd.DataFrame) -> bool:
        p = self.params
        close = float(latest["close"])
        if close < p["price_min"] or close > p["price_max"]:
            return False
        adr = float(latest.get("adr_percent", 0))
        if adr < p["min_adr"]:
            return False
        lookback = data.tail(p["lookback_days"])
        movement = abs(lookback["close"] - lookback["open"]) / lookback["open"]
        liquid_days = (lookback["volume"] >= p["volume_threshold"]) & (movement >= p["movement_threshold_pct"])
        if liquid_days.sum() < p["min_movement_days"]:
            return False
        return True

    def _analyze_pattern(self, data: pd.DataFrame) -> Optional[dict]:
        LOOKBACK = self.params.get("cont_lookback_days", 80)
        NEAR_TH = self.params["near_ma_threshold"] / 100
        BODY_TH = self.params["max_body_percentage"] / 100

        sma_period = self.params.get("sma_period", 20)
        rising_ma_window = self.params.get("rising_ma_prev_max_window", 5)
        adr_period = self.params.get("adr_period", 14)

        df = data.copy()
        if "sma_20" in df.columns:
            df["SMA20"] = df["sma_20"]
        else:
            df["SMA20"] = df["close"].rolling(sma_period).mean()
        direction = self.params.get("near_ma_direction", "above")
        df["Dist_to_MA_pct"] = abs(df["close"] - df["SMA20"]) / df["close"]
        if direction == "above":
            df["Near_MA"] = (df["close"] > df["SMA20"]) & (df["Dist_to_MA_pct"] <= NEAR_TH)
        elif direction == "below":
            df["Near_MA"] = (df["close"] < df["SMA20"]) & (df["Dist_to_MA_pct"] <= NEAR_TH)
        else:
            df["Near_MA"] = df["Dist_to_MA_pct"] <= NEAR_TH
        df["Above_MA"] = df["close"] > df["SMA20"]
        df["SMA20_prev_max"] = df["SMA20"].shift(1).rolling(rising_ma_window).max()
        rising_ma_tolerance = self.params.get("rising_ma_tolerance", 0.0) / 100
        df["Rising_MA"] = df["SMA20"] >= df["SMA20_prev_max"] * (1 - rising_ma_tolerance)

        latest = df.iloc[-1]

        if not (latest["Near_MA"] and latest["Rising_MA"]):
            return None

        body_pct = abs(latest["open"] - latest["close"]) / latest["close"]
        if body_pct >= BODY_TH:
            return None

        recent_adr = df.tail(adr_period)
        adr_abs = (recent_adr["high"] - recent_adr["low"]).mean()
        adr_pct = adr_abs / latest["close"]

        window = df.iloc[-LOOKBACK:]
        if len(window) < self.params.get("cont_min_data_rows", 50):
            return None

        below = window[~window["Above_MA"]]
        if below.empty:
            return None
        last_below = below.index[-1]

        # For below/both mode when latest candle is itself below MA,
        # skip the current below-MA run and find the previous Phase B dip
        if direction in ("below", "both") and not latest["Above_MA"]:
            above_idx = None
            for i in range(len(window) - 1, -1, -1):
                if window["Above_MA"].iloc[i]:
                    above_idx = i
                    break
            if above_idx is None or above_idx < 5:
                return None
            prev_below = window.iloc[:above_idx][~window.iloc[:above_idx]["Above_MA"]]
            if prev_below.empty:
                return None
            last_below = prev_below.index[-1]

        recovery = window.loc[last_below:]
        recovery_start = recovery[recovery["Above_MA"]]
        if recovery_start.empty:
            return None
        recovery_seg = window.loc[recovery_start.index[0]:]
        phase3_high = recovery_seg["high"].max()

        phase1 = window.loc[:last_below]
        phase1_above = phase1[phase1["Above_MA"]]
        if phase1_above.empty:
            return None
        phase1_high = phase1_above["high"].max()
        phase1_high_date = phase1_above["high"].idxmax()

        after_high = window.loc[phase1_high_date:].iloc[1:]
        if after_high.empty:
            return None
        below2 = after_high[after_high["close"] < after_high["SMA20"]]
        if below2.empty:
            return None
        phase2_low = below2["low"].min()

        depth_abs = phase1_high - phase2_low
        if depth_abs < adr_abs:
            return None
        if phase3_high >= phase1_high:
            return None

        return {
            "sma20": round(float(latest["SMA20"]), 2),
            "dist_to_ma_pct": round(float(latest["Dist_to_MA_pct"] * 100), 1),
            "phase1_high": round(float(phase1_high), 2),
            "phase2_low": round(float(phase2_low), 2),
            "phase3_high": round(float(phase3_high), 2),
            "depth_rs": round(float(depth_abs), 2),
            "depth_pct": round(float(depth_abs / phase1_high * 100), 1),
            "adr_pct": round(float(adr_pct * 100), 1),
        }


class ReversalScanner:
    def __init__(self, params: dict):
        self.params = params

    def run(self, progress_callback: Optional[Callable] = None, num_workers: Optional[int] = None, scan_date: Optional[date] = None) -> list[dict]:
        if scan_date is None:
            scan_date = _detect_scan_date()
        symbols = cache_manager.list_symbols()
        total = len(symbols)
        if total == 0:
            return []

        if num_workers is None:
            num_workers = min(os.cpu_count() or 4, total)

        chunk_size = max(1, total // num_workers)
        chunks = [symbols[i:i + chunk_size] for i in range(0, total, chunk_size)]

        results = []
        processed = 0

        with ProcessPoolExecutor(max_workers=num_workers) as pool:
            future_map = {pool.submit(_run_chunk, ch, self.params, scan_date, "reversal"): len(ch) for ch in chunks}
            for future in as_completed(future_map):
                chunk_len = future_map[future]
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    logger.error(f"Reversal chunk failed: {e}")
                processed += chunk_len
                if progress_callback:
                    pct = int((processed / total) * 100)
                    progress_callback(pct, f"Scanned {processed}/{total} stocks, found {len(results)} candidates")

        results.sort(key=lambda r: r["symbol"])
        return results

    def _passes_filters(self, latest: pd.Series, data: pd.DataFrame) -> bool:
        p = self.params
        close = float(latest["close"])
        if close < p["price_min"] or close > p["price_max"]:
            return False
        adr = float(latest.get("adr_percent", 0))
        if adr < p["min_adr"]:
            return False
        lookback = data.tail(p["lookback_days"])
        movement = abs(lookback["close"] - lookback["open"]) / lookback["open"]
        liquid_days = (lookback["volume"] >= p["volume_threshold"]) & (movement >= p["movement_threshold_pct"])
        if liquid_days.sum() < p["min_movement_days"]:
            return False
        return True

    def _analyze_pattern(self, data: pd.DataFrame, scan_date: Optional[date] = None) -> Optional[dict]:
        best = self._find_best_decline_period(data)
        if best is None:
            return None

        latest = data.iloc[-1]
        close = float(latest["close"])

        adr_pct = float(latest.get("adr_percent", 0))

        trend_window = data
        if scan_date is not None:
            start = scan_date - timedelta(days=self.params.get("rev_lookback_days", 15))
            trend_window = data[data.index >= pd.Timestamp(start)]
        sma = trend_window["close"].rolling(self.params.get("sma_period", 20)).mean()
        oldest_idx = len(trend_window) - best["period"]
        if oldest_idx < 0:
            trend_context = "downtrend"
        else:
            ma_at_oldest = sma.iloc[oldest_idx]
            ma_5_earlier = sma.iloc[oldest_idx - self.params.get("ma_angle_points", 5)] if oldest_idx >= self.params.get("ma_angle_points", 5) else pd.NA
            if pd.isna(ma_at_oldest) or pd.isna(ma_5_earlier):
                trend_context = "downtrend"
            else:
                trend_context = "uptrend" if ma_at_oldest > ma_5_earlier else "downtrend"

        return {
            "period": best["period"],
            "green_days": best["green_days"],
            "first_red_date": best["first_red_date"].strftime("%d %b %y").lstrip("0"),
            "decline_percent": round(best["decline_percent"], 4),
            "trend_context": trend_context,
            "adr_pct": round(adr_pct, 1),
        }

    def _find_best_decline_period(self, data: pd.DataFrame) -> Optional[dict]:
        min_period = self.params.get("rev_decline_days_min", 3)
        max_period = self.params.get("rev_decline_days_max", 15)
        min_decline = self.params.get("rev_min_decline_pct", 10.0) / 100

        best_setup = None
        max_decline = 0

        for period in range(min_period, max_period + 1):
            if len(data) < period:
                continue

            period_data = data.tail(period)

            red_count = int((period_data["close"] < period_data["open"]).sum())
            green_count = period - red_count

            if not self._check_pattern_logic(red_count, green_count, period, period_data):
                continue

            start_price = float(period_data.iloc[0]["open"])
            end_price = float(period_data.iloc[-1]["close"])
            decline = (start_price - end_price) / start_price

            if decline >= min_decline and (period_data["volume"] >= self.params["volume_threshold"]).any():
                if decline > max_decline:
                    max_decline = decline
                    best_setup = {
                        "period": period,
                        "green_days": green_count,
                        "first_red_date": period_data.index[0].date(),
                        "decline_percent": decline,
                    }

        return best_setup

    @staticmethod
    def _check_pattern_logic(red_days: int, green_days: int, period: int, period_data: pd.DataFrame) -> bool:
        if not (period_data.iloc[0]["close"] < period_data.iloc[0]["open"]):
            return False
        if period == 3:
            return red_days == 3 and green_days == 0
        if period in (4, 5):
            return red_days > green_days
        if period in (6, 7):
            return red_days + 1 > green_days
        if period >= 8:
            return green_days <= 3
        return False


def get_default_params() -> dict:
    """Return default scanner params pre-filled from settings."""
    from src.settings import get_all_as_dict
    s = get_all_as_dict()
    return {
        "price_min": int(s.get("price_min", 100)),
        "price_max": int(s.get("price_max", 2000)),
        "near_ma_threshold": float(s.get("cont_near_ma_threshold_pct", 5.0)),
        "near_ma_direction": s.get("cont_near_ma_direction", "above"),
        "max_body_percentage": float(s.get("cont_max_body_pct", 5.0)),
        "min_adr": float(s.get("min_adr_pct", 3.0)),
        "volume_threshold": int(s.get("volume_min", 1000000)),
        "lookback_days": int(s.get("lookback_days", 30)),
        "min_volume_days": int(s.get("min_volume_days", 2)),
        "movement_threshold_pct": float(s.get("movement_threshold_pct", 5.0)) / 100,
        "min_movement_days": int(s.get("min_movement_days", 2)),
        "cont_lookback_days": int(s.get("cont_lookback_days", 80)),
        "sma_period": int(s.get("sma_period", 20)),
        "rising_ma_prev_max_window": int(s.get("rising_ma_prev_max_window", 5)),
        "rising_ma_tolerance": float(s.get("cont_rising_ma_tolerance_pct", 0.0)),
        "adr_period": int(s.get("adr_period", 14)),
        "cont_min_data_rows": int(s.get("cont_min_data_rows", 50)),
        "ma_angle_points": int(s.get("ma_angle_points", 5)),
        "high_low_period": int(s.get("high_low_period", 20)),
        "price_change_periods": [int(x) for x in s.get("price_change_periods", "1,5,20").split(",")],
    }


def get_default_reversal_params() -> dict:
    """Return default reversal scanner params pre-filled from settings."""
    base = get_default_params()
    from src.settings import get_all_as_dict
    s = get_all_as_dict()
    base.update({
        "rev_decline_days_min": int(s.get("rev_decline_days_min", 3)),
        "rev_decline_days_max": int(s.get("rev_decline_days_max", 15)),
        "rev_min_decline_pct": float(s.get("rev_min_decline_pct", 10.0)),
        "rev_lookback_days": int(s.get("rev_lookback_days", 15)),
        "rev_min_data_rows": int(s.get("rev_min_data_rows", 30)),
    })
    return base
