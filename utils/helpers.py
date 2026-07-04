"""Utility helper functions."""

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd


def format_number(n: float, decimals: int = 1) -> str:
    """Format large numbers with K/M/B suffixes."""
    if pd.isna(n):
        return "N/A"
    n = float(n)
    if abs(n) >= 1_000_000_000:
        return f"{n / 1_000_000_000:.{decimals}f}B"
    if abs(n) >= 1_000_000:
        return f"{n / 1_000_000:.{decimals}f}M"
    if abs(n) >= 1_000:
        return f"{n / 1_000:.{decimals}f}K"
    return f"{n:,.0f}"


def format_pct(n: float, decimals: int = 1) -> str:
    """Format a ratio as a percentage string."""
    if pd.isna(n):
        return "N/A"
    return f"{n * 100:.{decimals}f}%"


def calc_delta(current: float, previous: float) -> Optional[float]:
    """Calculate percent change between two values."""
    if previous is None or previous == 0 or pd.isna(previous):
        return None
    return (current - previous) / previous


def date_range_filter(
    df: pd.DataFrame,
    date_col: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> pd.DataFrame:
    """Filter DataFrame by date range."""
    if df.empty or date_col not in df.columns:
        return df
    result = df.copy()
    result[date_col] = pd.to_datetime(result[date_col])
    if start:
        result = result[result[date_col] >= pd.Timestamp(start)]
    if end:
        result = result[result[date_col] <= pd.Timestamp(end)]
    return result


def rolling_avg(series: pd.Series, window: int = 7) -> pd.Series:
    """Compute rolling average."""
    return series.rolling(window=window, min_periods=1).mean()


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division avoiding zero-division."""
    if denominator is None or denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator


def get_reference_date() -> pd.Timestamp:
    """Analytics reference date aligned with synthetic dataset end."""
    from config import DATA_END_DATE
    return pd.Timestamp(DATA_END_DATE)


def generate_date_series(start: str, end: str) -> pd.DatetimeIndex:
    """Generate daily date range."""
    return pd.date_range(start=start, end=end, freq="D")
