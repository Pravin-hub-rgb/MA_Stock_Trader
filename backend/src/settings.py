"""
Settings Engine for TradeStack
Every parameter that previously required file-editing is now editable from the UI.
All settings stored in SQLite `settings` table.
"""

import logging
from datetime import datetime
from typing import Any

from . import db

logger = logging.getLogger(__name__)

SETTINGS_VERSION = "2"

SEED: list[dict] = [
    # ---- Trading Schedule ----
    {"key": "market_open", "value": "09:15", "type": "time", "category": "trading_schedule", "label": "Market Open", "description": "NSE market opening time"},
    {"key": "market_close", "value": "15:30", "type": "time", "category": "trading_schedule", "label": "Market Close", "description": "NSE market closing time"},
    {"key": "entry_window_minutes", "value": "5", "type": "number", "category": "trading_schedule", "label": "Entry Window (minutes)", "description": "Minutes after open for entry", "min": "1", "max": "60", "step": "1"},
    {"key": "prep_start_offset_seconds", "value": "30", "type": "number", "category": "trading_schedule", "label": "Prep Start Offset (seconds)", "description": "Seconds before market open to start preparing", "min": "0", "max": "300", "step": "5"},
    {"key": "confirmation_window_minutes", "value": "5", "type": "number", "category": "trading_schedule", "label": "Confirmation Window (minutes)", "description": "Window to confirm entry after open", "min": "1", "max": "30", "step": "1"},
    # ---- Risk Management ----
    {"key": "max_positions", "value": "2", "type": "number", "category": "risk_management", "label": "Max Positions", "description": "Maximum concurrent positions", "min": "1", "max": "10", "step": "1"},
    {"key": "entry_sl_pct", "value": "4.0", "type": "number", "category": "risk_management", "label": "Entry SL (%)", "description": "Stop loss as % of entry price", "min": "0.5", "max": "20.0", "step": "0.5"},
    {"key": "low_violation_pct", "value": "1.0", "type": "number", "category": "risk_management", "label": "Low Violation (%)", "description": "Allowed % below entry low before exit", "min": "0.1", "max": "10.0", "step": "0.1"},
    {"key": "flat_gap_threshold", "value": "0.3", "type": "number", "category": "risk_management", "label": "Flat Gap Threshold (%)", "description": "Gap % to consider flat", "min": "0.1", "max": "5.0", "step": "0.1"},
    {"key": "trailing_sl_threshold", "value": "5.0", "type": "number", "category": "risk_management", "label": "Trailing SL Trigger (%)", "description": "Profit % to trigger trailing SL", "min": "1.0", "max": "20.0", "step": "0.5"},
    {"key": "risk_per_trade_pct", "value": "0.5", "type": "number", "category": "risk_management", "label": "Risk Per Trade (%)", "description": "% of capital risked per trade", "min": "0.1", "max": "5.0", "step": "0.1"},
    {"key": "max_drawdown_pct", "value": "5.0", "type": "number", "category": "risk_management", "label": "Max Drawdown (%)", "description": "Max drawdown before circuit breaker", "min": "1.0", "max": "50.0", "step": "0.5"},
    {"key": "profit_target_pct", "value": "15.0", "type": "number", "category": "risk_management", "label": "Profit Target (%)", "description": "Target profit % per trade", "min": "2.0", "max": "50.0", "step": "0.5"},
    {"key": "time_exit_days", "value": "3", "type": "number", "category": "risk_management", "label": "Time Exit (days)", "description": "Max holding days before auto exit", "min": "1", "max": "30", "step": "1"},
    {"key": "max_stocks_to_select", "value": "2", "type": "number", "category": "risk_management", "label": "Max Stocks To Select", "description": "Max stocks for scan selection", "min": "1", "max": "20", "step": "1"},
    {"key": "max_stocks_to_trade", "value": "2", "type": "number", "category": "risk_management", "label": "Max Stocks To Trade", "description": "Max stocks actually traded", "min": "1", "max": "10", "step": "1"},
    {"key": "quality_score_threshold", "value": "15", "type": "number", "category": "risk_management", "label": "Quality Score Threshold", "description": "Minimum quality score for entry", "min": "0", "max": "100", "step": "1"},
    # ---- Gap / Entry Conditions ----
    {"key": "gap_up_min_pct", "value": "0.2", "type": "number", "category": "entry_conditions", "label": "Gap Up Min (%)", "description": "Minimum gap up % for entry", "min": "0.0", "max": "10.0", "step": "0.1"},
    {"key": "gap_up_max_pct", "value": "5.0", "type": "number", "category": "entry_conditions", "label": "Gap Up Max (%)", "description": "Maximum gap up % for entry", "min": "0.0", "max": "20.0", "step": "0.1"},
    {"key": "strong_start_gap_pct", "value": "2.0", "type": "number", "category": "entry_conditions", "label": "Strong Start Gap (%)", "description": "Gap % indicating strong start", "min": "0.0", "max": "10.0", "step": "0.1"},
    # ---- Scanner: Base Filters ----
    {"key": "price_min", "value": "100", "type": "number", "category": "scanner_base", "label": "Min Price", "description": "Minimum stock price for scan", "min": "10", "max": "10000", "step": "10"},
    {"key": "price_max", "value": "2000", "type": "number", "category": "scanner_base", "label": "Max Price", "description": "Maximum stock price for scan", "min": "10", "max": "50000", "step": "10"},
    {"key": "min_adr_pct", "value": "3.0", "type": "number", "category": "scanner_base", "label": "Min ADR (%)", "description": "Minimum average daily range", "min": "0.0", "max": "20.0", "step": "0.5"},
    {"key": "volume_min", "value": "1000000", "type": "number", "category": "scanner_base", "label": "Min Volume", "description": "Minimum daily volume (shares)", "min": "100000", "max": "100000000", "step": "100000"},
    {"key": "min_volume_days", "value": "2", "type": "number", "category": "scanner_base", "label": "Min Volume Days", "description": "Consecutive days volume must exceed threshold", "min": "1", "max": "10", "step": "1"},
    {"key": "movement_threshold_pct", "value": "5.0", "type": "number", "category": "scanner_base", "label": "Movement Threshold (%)", "description": "Min price movement % for scan", "min": "0.0", "max": "50.0", "step": "0.5"},
    {"key": "min_movement_days", "value": "2", "type": "number", "category": "scanner_base", "label": "Min Movement Days", "description": "Min days of movement for validity", "min": "1", "max": "10", "step": "1"},
    {"key": "lookback_days", "value": "30", "type": "number", "category": "scanner_base", "label": "Lookback Days", "description": "Days to look back for base filter checks", "min": "5", "max": "200", "step": "5"},
    {"key": "sma_period", "value": "20", "type": "number", "category": "scanner_base", "label": "SMA Period", "description": "Simple moving average period", "min": "5", "max": "200", "step": "1"},
    {"key": "adr_period", "value": "14", "type": "number", "category": "scanner_base", "label": "ADR Period", "description": "Average daily range calculation period", "min": "5", "max": "50", "step": "1"},
    {"key": "ma_angle_points", "value": "5", "type": "number", "category": "scanner_base", "label": "MA Angle Points", "description": "Points for MA angle linear regression", "min": "3", "max": "20", "step": "1"},
    # ---- Scanner: Continuation ----
    {"key": "cont_near_ma_threshold_pct", "value": "5.0", "type": "number", "category": "scanner_continuation", "label": "Near MA Threshold (%)", "description": "Max distance from SMA20 for near-MA filter", "min": "0.0", "max": "20.0", "step": "0.5"},
    {"key": "cont_near_ma_direction", "value": "above", "type": "select", "category": "scanner_continuation", "label": "Near MA Direction", "description": "Above SMA20, below SMA20, or both sides", "options": "above,below,both"},
    {"key": "cont_max_body_pct", "value": "5.0", "type": "number", "category": "scanner_continuation", "label": "Max Body (%)", "description": "Max candle body as % of range", "min": "0.0", "max": "20.0", "step": "0.5"},
    {"key": "cont_lookback_days", "value": "80", "type": "number", "category": "scanner_continuation", "label": "Continuation Lookback (days)", "description": "Lookback for continuation pattern", "min": "20", "max": "200", "step": "5"},
    {"key": "cont_consolidation_days_min", "value": "3", "type": "number", "category": "scanner_continuation", "label": "Consolidation Min (days)", "description": "Min consolidation days", "min": "1", "max": "20", "step": "1"},
    {"key": "cont_consolidation_days_max", "value": "7", "type": "number", "category": "scanner_continuation", "label": "Consolidation Max (days)", "description": "Max consolidation days", "min": "1", "max": "30", "step": "1"},
    {"key": "cont_max_distance_from_high_pct", "value": "5.0", "type": "number", "category": "scanner_continuation", "label": "Max Distance From High (%)", "description": "Max % below recent high", "min": "0.0", "max": "20.0", "step": "0.5"},
    {"key": "cont_min_ma_angle", "value": "0.0", "type": "number", "category": "scanner_continuation", "label": "Min MA Angle", "description": "Minimum SMA angle for continuation", "min": "-10.0", "max": "10.0", "step": "0.5"},
    {"key": "cont_min_data_rows", "value": "50", "type": "number", "category": "scanner_continuation", "label": "Cont Min Data Rows", "description": "Minimum data rows required for continuation scan", "min": "10", "max": "500", "step": "10"},
    {"key": "cont_rising_ma_tolerance_pct", "value": "0.0", "type": "number", "category": "scanner_continuation", "label": "Rising MA Tolerance (%)", "description": "Max % MA can decline from recent peak and still pass", "min": "0.0", "max": "5.0", "step": "0.1"},
    # ---- Scanner: Reversal ----
    {"key": "rev_decline_days_min", "value": "3", "type": "number", "category": "scanner_reversal", "label": "Decline Days Min", "description": "Min consecutive decline days", "min": "1", "max": "10", "step": "1"},
    {"key": "rev_decline_days_max", "value": "15", "type": "number", "category": "scanner_reversal", "label": "Decline Days Max", "description": "Max consecutive decline days", "min": "1", "max": "20", "step": "1"},
    {"key": "rev_min_decline_pct", "value": "10.0", "type": "number", "category": "scanner_reversal", "label": "Min Decline (%)", "description": "Min total decline % for reversal", "min": "0.0", "max": "50.0", "step": "0.5"},
    {"key": "rev_lookback_days", "value": "15", "type": "number", "category": "scanner_reversal", "label": "Reversal Lookback (days)", "description": "Lookback for reversal pattern", "min": "5", "max": "100", "step": "5"},
    {"key": "rev_oversold_distance_pct", "value": "5.0", "type": "number", "category": "scanner_reversal", "label": "Oversold Distance (%)", "description": "Distance below moving avg considered oversold", "min": "0.0", "max": "20.0", "step": "0.5"},
    {"key": "rev_min_data_rows", "value": "30", "type": "number", "category": "scanner_reversal", "label": "Rev Min Data Rows", "description": "Minimum data rows required for reversal scan", "min": "10", "max": "500", "step": "10"},
    # ---- Volume Validation (SVRO) ----
    {"key": "svro_min_volume_ratio", "value": "7.5", "type": "number", "category": "volume_validation", "label": "SVRO Min Volume Ratio (%)", "description": "Min volume ratio for SVRO signal", "min": "0.0", "max": "50.0", "step": "0.5"},
    {"key": "svro_baseline_days", "value": "10", "type": "number", "category": "volume_validation", "label": "SVRO Baseline Days", "description": "Days for SVRO baseline calculation", "min": "5", "max": "50", "step": "1"},
    {"key": "volume_surge_threshold", "value": "1.5", "type": "number", "category": "volume_validation", "label": "Volume Surge Threshold", "description": "Multiple of avg volume to qualify as surge", "min": "1.0", "max": "10.0", "step": "0.1"},
    {"key": "volume_ma_period", "value": "20", "type": "number", "category": "volume_validation", "label": "Volume MA Period", "description": "Period for volume moving average", "min": "5", "max": "50", "step": "1"},
    # ---- Volume Profile / VAH ----
    {"key": "vah_bin_size", "value": "0.05", "type": "number", "category": "volume_profile", "label": "VAH Bin Size", "description": "Price bin size for volume profile", "min": "0.01", "max": "1.0", "step": "0.01"},
    {"key": "vah_value_area_pct", "value": "70", "type": "number", "category": "volume_profile", "label": "VAH Value Area (%)", "description": "Value area % of total volume", "min": "50", "max": "90", "step": "5"},
    # ---- Technical Indicators ----
    {"key": "price_change_periods", "value": "1,5,20", "type": "string", "category": "indicators", "label": "Price Change Periods", "description": "Comma-separated periods for price change calculation"},
    {"key": "high_low_period", "value": "20", "type": "number", "category": "indicators", "label": "High/Low Distance Period", "description": "Period for high/low distance calculation", "min": "5", "max": "50", "step": "1"},
    {"key": "rising_ma_prev_max_window", "value": "5", "type": "number", "category": "indicators", "label": "Rising MA Prev Max Window", "description": "Days before current for rising MA max check", "min": "2", "max": "20", "step": "1"},
    # ---- Live Trading ----
    {"key": "trading_capital", "value": "100000", "type": "number", "category": "live_trading", "label": "Trading Capital", "description": "Total capital allocated for live trading", "min": "10000", "max": "10000000", "step": "10000"},
    {"key": "trading_quantity", "value": "100", "type": "number", "category": "live_trading", "label": "Trading Quantity", "description": "Number of shares per trade", "min": "1", "max": "10000", "step": "1"},
    {"key": "paper_trading", "value": "true", "type": "boolean", "category": "live_trading", "label": "Paper Trading", "description": "Run in paper trading mode (no real orders)"},
    # ---- Connection / WebSocket ----
    {"key": "api_poll_delay_seconds", "value": "5", "type": "number", "category": "connection", "label": "API Poll Delay (seconds)", "description": "Delay between API status polls", "min": "1", "max": "60", "step": "1"},
    {"key": "api_retry_delay_seconds", "value": "30", "type": "number", "category": "connection", "label": "API Retry Delay (seconds)", "description": "Delay before retrying failed API call", "min": "1", "max": "300", "step": "5"},
    {"key": "websocket_reconnect_delay", "value": "5", "type": "number", "category": "connection", "label": "WebSocket Reconnect Delay (s)", "description": "Delay between WebSocket reconnection attempts", "min": "1", "max": "60", "step": "1"},
    {"key": "max_websocket_retries", "value": "10", "type": "number", "category": "connection", "label": "Max WebSocket Retries", "description": "Max reconnection attempts before giving up", "min": "1", "max": "100", "step": "1"},
    # ---- Error Handling ----
    {"key": "max_retries", "value": "3", "type": "number", "category": "error_handling", "label": "Max Retries", "description": "Max retry attempts for failed operations", "min": "0", "max": "20", "step": "1"},
    {"key": "retry_delay_seconds", "value": "5", "type": "number", "category": "error_handling", "label": "Retry Delay (seconds)", "description": "Delay between retry attempts", "min": "1", "max": "120", "step": "1"},
    # ---- API Credentials ----
    {"key": "upstox_api_key", "value": "", "type": "password", "category": "credentials", "label": "Upstox API Key", "description": "Upstox API key from dashboard"},
    {"key": "upstox_api_secret", "value": "", "type": "password", "category": "credentials", "label": "Upstox API Secret", "description": "Upstox API secret key"},
    {"key": "upstox_access_token", "value": "", "type": "password", "category": "credentials", "label": "Upstox Access Token", "description": "Upstox JWT access token"},
    # ---- Paper Trading ----
    {"key": "paper_trading_enabled", "value": "true", "type": "boolean", "category": "paper_trading", "label": "Paper Trading Enabled", "description": "Enable paper trading mode"},
    {"key": "trade_log_dir", "value": "data/logs", "type": "string", "category": "paper_trading", "label": "Trade Log Directory", "description": "Directory for trade log files"},
    # ---- Data Management ----
    {"key": "cache_days", "value": "200", "type": "number", "category": "data_management", "label": "Cache Days", "description": "Days of data to keep in cache", "min": "30", "max": "500", "step": "10"},
    {"key": "bhavcopy_batch_size", "value": "100", "type": "number", "category": "data_management", "label": "Bhavcopy Batch Size", "description": "Stocks per batch during bhavcopy update", "min": "10", "max": "500", "step": "10"},
    {"key": "historical_download_days", "value": "180", "type": "number", "category": "data_management", "label": "Historical Download Days", "description": "Calendar days for Upstox historical download", "min": "30", "max": "500", "step": "10"},
    # ---- Logging ----
    {"key": "log_level", "value": "INFO", "type": "string", "category": "logging", "label": "Log Level", "description": "Application log level"},
    {"key": "log_to_file", "value": "true", "type": "boolean", "category": "logging", "label": "Log To File", "description": "Write logs to file"},
    {"key": "log_to_console", "value": "true", "type": "boolean", "category": "logging", "label": "Log To Console", "description": "Write logs to console"},
    {"key": "debug_mode", "value": "false", "type": "boolean", "category": "logging", "label": "Debug Mode", "description": "Enable verbose debug output"},
]


def get_all() -> list[dict]:
    """Return all settings from DB."""
    return db.settings_get_all()


def get_all_as_dict() -> dict[str, str]:
    """Return settings as flat key→value dict (with type casting for booleans/numbers)."""
    rows = db.settings_get_all()
    result = {}
    for r in rows:
        result[r["key"]] = _cast_value(r["value"], r["type"])
    return result


def get(key: str) -> Any:
    """Get a single setting value (type-casted)."""
    row = db.settings_get(key)
    if not row:
        return None
    return _cast_value(row["value"], row["type"])


def set(key: str, value: str):
    """Set a single setting value."""
    db.settings_set_value(key, str(value))


def reset_category(category: str):
    """Reset a category to seed defaults."""
    db.settings_reset_category(category)
    _seed_category(category)


def reset_all():
    """Reset ALL settings to seed defaults."""
    for r in SEED:
        db.settings_upsert(**r)


def _cast_value(value: str, type_: str) -> Any:
    if type_ == "boolean":
        return str(value).lower() in ("true", "1", "yes")
    if type_ == "number":
        try:
            if "." in str(value):
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return value
    return str(value)


def _seed_category(category: str):
    """Insert seed defaults for one category."""
    for r in SEED:
        if r["category"] == category:
            db.settings_upsert(**r)


def ensure_settings():
    """Seed the settings table if empty or version mismatch."""
    version = db.settings_get_meta("settings_version")
    if version == SETTINGS_VERSION and db.settings_get_all():
        return

    logger.info(f"Settings: seeding (version={SETTINGS_VERSION}, previous={version})")
    for r in SEED:
        db.settings_upsert(**r)
    db.settings_set_meta("settings_version", SETTINGS_VERSION)
    logger.info(f"Settings: seeded {len(SEED)} defaults")


# Auto-seed on import
ensure_settings()
