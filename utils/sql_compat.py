"""SQL dialect compatibility helpers."""

from config import DATA_END_DATE, DATABASE_URL


def is_sqlite() -> bool:
    return DATABASE_URL.startswith("sqlite")


def _reference_date() -> str:
    """Use dataset end date as analytics 'as of' date."""
    return DATA_END_DATE


def date_filter(column: str, days: int) -> str:
    """Generate dialect-aware date filter clause relative to dataset end date."""
    ref = _reference_date()
    if is_sqlite():
        return f"{column} >= date('{ref}', '-{days} days')"
    return f"{column} >= DATE '{ref}' - INTERVAL '{days} days'"


def bool_avg(column: str) -> str:
    """Average of boolean/boolean-like column."""
    if is_sqlite():
        return f"AVG(CAST({column} AS FLOAT))"
    return f"AVG({column}::float)"
