"""
Continuation setup analyzer for MA Stock Trader
Implements the guider's zig-zag continuation pullback pattern
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, Dict
import pandas as pd

from src.utils.data_fetcher import data_fetcher
from src.utils.cache_manager import cache_manager
from .filters import FilterEngine

logger = logging.getLogger(__name__)


class ContinuationAnalyzer:
    """Handles continuation setup analysis using zig-zag pattern"""

    def __init__(self, filter_engine: FilterEngine):
        self.filter_engine = filter_engine

    def analyze_continuation_setup(self, symbol: str, scan_date: date, data: pd.DataFrame) -> Optional[Dict]:
        """Analyze stock for continuation pullback zig-zag pattern (assumes data is pre-fetched and base filters passed)"""
        try:
            # Data is already provided and filtered
            latest = data.iloc[-1]

            # Now check the zig-zag pattern
            hit, details = self._check_continuation_pattern(data, self.filter_engine.continuation_params)
            if not hit:
                logger.info(f"{symbol}: {details}")
                return None

            # Pattern matched - return enriched results
            return {
                'symbol': symbol,
                'close': latest['close'],
                'sma20': round(latest['ma_20'], 2),
                'dist_to_ma_pct': round(details['Dist_to_MA_%'], 1),
                'phase1_high': details['Phase1_High'],
                'phase2_low': details['Phase2_Low'],
                'phase3_high': details['Phase3_High'],
                'depth_rs': details['Depth_Rs'],
                'depth_pct': details['Depth_%'],
                'adr_pct': details['ADR_%']
            }

        except Exception as e:
            logger.error(f"Error analyzing continuation setup for {symbol}: {e}")
            return None

    def _check_continuation_pattern(self, data: pd.DataFrame, params: Dict) -> tuple[bool, str | Dict]:
        """
        Check for continuation pullback zig-zag pattern (guider's implementation)
        Returns: (is_hit: bool, details: dict or failure_reason: str)
        """
        # Parameters from spec
        LOOKBACK_DAYS = 80
        NEAR_THRESHOLD = params.get('near_ma_threshold', 0.05)  # Default 5% if not set
        MAX_BODY_THRESHOLD = params.get('max_body_percentage', 0.03)  # Default 3% if not set
        ADR_PERIOD = 14
        ADR_MULT = 1.0

        # Need enough data (50 trading days for 3-phase continuation analysis with 80-day lookback)
        if len(data) < 50:
            return False, f"Insufficient data ({len(data)} < 50 trading days)"

        # Prepare data with proper column names (capitalize for guider's code)
        df = data.copy()

        # Ensure date is a column, not index
        if isinstance(df.index, pd.DatetimeIndex):
            df = df.reset_index()
            df = df.rename(columns={'index': 'date'})

        df = df.rename(columns={
            'open': 'Open', 'high': 'High', 'low': 'Low',
            'close': 'Close', 'volume': 'Volume', 'ma_20': 'SMA20'
        })
        df = df.set_index('date')

        # --- Indicators ---
        if 'SMA20' not in df.columns:
            df['SMA20'] = df['Close'].rolling(window=20).mean()

        # Rising MA: current > max of previous 5 days
        df['SMA20_prev_max'] = df['SMA20'].shift(1).rolling(5).max()
        df['Rising_MA'] = df['SMA20'] > df['SMA20_prev_max']

        # Above / Below MA
        df['Above_MA'] = df['Close'] > df['SMA20']

        # Near or above MA with tolerance
        df['Dist_to_MA_pct'] = abs(df['Close'] - df['SMA20']) / df['Close']
        df['Near_or_Above_MA'] = (df['Close'] > df['SMA20']) & (df['Dist_to_MA_pct'] <= NEAR_THRESHOLD)

        # ADR for depth and base filter
        recent = df.tail(ADR_PERIOD + 10)
        daily_range = recent['High'] - recent['Low']
        adr_abs = daily_range.mean()
        current_close = df['Close'].iloc[-1]
        adr_pct = adr_abs / current_close

        latest = df.iloc[-1]

        # --- PHASE 3 FIRST (Latest day) ---
        if not (latest['Near_or_Above_MA'] and latest['Rising_MA']):
            reason = f"Phase 3 FAIL: Near_MA={latest['Near_or_Above_MA']}, Rising_MA={latest['Rising_MA']}"
            if latest['Dist_to_MA_pct'] > NEAR_THRESHOLD:
                reason += f", Close {latest['Dist_to_MA_pct']*100:.1f}% from MA (>5% threshold)"
            return False, reason

        # --- BODY SIZE CHECK (Latest day candle) ---
        body_size_pct = abs(latest['Open'] - latest['Close']) / latest['Close']
        if body_size_pct >= MAX_BODY_THRESHOLD:
            return False, f"Body too large: {body_size_pct*100:.1f}% >= {MAX_BODY_THRESHOLD*100:.1f}% threshold"

        # Slice last 80 trading days
        recent_80 = df.iloc[-LOOKBACK_DAYS:].copy()
        if len(recent_80) < 50:
            return False, f"Not enough recent data in 80-day window ({len(recent_80)} < 50)"

        # --- Find recovery start (first close back above MA after last below) ---
        below_days = recent_80[~recent_80['Above_MA']]
        if below_days.empty:
            return False, "Phase 2 fail: No close below MA in 80 days"

        last_below_date = below_days.index[-1]
        after_pullback = recent_80.loc[last_below_date:]

        # First close above MA after pullback
        recovery_days = after_pullback[after_pullback['Above_MA']]
        if recovery_days.empty:
            return False, "No recovery above MA"

        recovery_start_date = recovery_days.index[0]
        recovery_segment = recent_80.loc[recovery_start_date:]

        # Phase 3 high (max high in recovery segment)
        phase3_high = recovery_segment['High'].max()

        # --- PHASE 1: Above-MA period before Phase 2 ---
        phase1_period = recent_80.loc[:last_below_date]
        phase1_above = phase1_period[phase1_period['Above_MA']]
        if phase1_above.empty:
            return False, "Phase 1 fail: No prior above-MA period"

        phase1_high = phase1_above['High'].max()
        phase1_high_date = phase1_above['High'].idxmax()  # date of the highest high

        # --- PHASE 2: Pullback after Phase 1 high ---
        # Period from day after high to today
        period_after_high = recent_80.loc[phase1_high_date:].iloc[1:]  # skip high day
        if period_after_high.empty:
            return False, "Phase 2 fail: No period after Phase 1 high"

        # Find days with close below MA
        below_days = period_after_high[period_after_high['Close'] < period_after_high['SMA20']]
        if below_days.empty:
            return False, "Phase 2 fail: No close below MA after Phase 1 high"

        phase2_low = below_days['Low'].min()
        phase2_low_date = below_days['Low'].idxmin()

        # --- Depth check ---
        depth_abs = phase1_high - phase2_low
        depth_required = adr_abs * ADR_MULT
        if depth_abs < depth_required:
            return False, f"Depth {depth_abs:.1f} < {depth_required:.1f} (1x ADR)"

        # --- Lower high check ---
        if phase3_high >= phase1_high:
            return False, f"No lower high (Phase3 {phase3_high:.2f} >= Phase1 {phase1_high:.2f})"

        # --- HIT: Zig-zag pattern detected ---
        details = {
            'Phase1_High': round(phase1_high, 2),
            'Phase2_Low': round(phase2_low, 2),
            'Phase3_High': round(phase3_high, 2),
            'Depth_Rs': round(depth_abs, 2),
            'Depth_%': round((depth_abs / phase1_high) * 100, 1),
            'ADR_%': round(adr_pct * 100, 1),
            'Dist_to_MA_%': round(latest['Dist_to_MA_pct'] * 100, 1),
        }

        return True, details
