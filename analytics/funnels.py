"""Funnel analysis for user conversion paths."""

import pandas as pd

from database.connection import read_sql
from config import FUNNEL_STEPS
from utils.sql_compat import date_filter


def get_funnel_analysis(days: int = 30) -> pd.DataFrame:
    """
    Calculate conversion funnel from app open to follow.

    Returns step-wise user counts and conversion rates.
    """
    step_map = {
        "app_open": "app_open",
        "feed_view": "feed_view",
        "content_engagement": "('like','comment','share','save')",
        "share": "share",
        "follow": "follow",
    }

    results = []
    for step in FUNNEL_STEPS:
        if step == "content_engagement":
            condition = "event_type IN ('like','comment','share','save')"
        else:
            condition = f"event_type = '{step_map[step]}'"

        query = f"""
            SELECT COUNT(DISTINCT user_id) AS users
            FROM user_events
            WHERE {condition}
              AND {date_filter("event_timestamp", days)}
        """
        count = read_sql(query)["users"].iloc[0]
        results.append({"step": step.replace("_", " ").title(), "users": count})

    df = pd.DataFrame(results)
    top = df["users"].iloc[0] if not df.empty else 1
    df["conversion_rate"] = df["users"] / max(top, 1)
    df["step_order"] = range(len(df))
    return df


def get_funnel_by_segment(days: int = 30) -> pd.DataFrame:
    """Funnel conversion rates by user segment."""
    query = f"""
        SELECT u.segment,
               e.event_type,
               COUNT(DISTINCT e.user_id) AS users
        FROM user_events e
        JOIN users u ON e.user_id = u.user_id
        WHERE {date_filter("e.event_timestamp", days)}
        GROUP BY u.segment, e.event_type
        ORDER BY u.segment, users DESC
    """
    return read_sql(query)
