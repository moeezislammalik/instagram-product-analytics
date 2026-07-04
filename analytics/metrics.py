"""Core product metrics calculations."""

from datetime import datetime
from typing import Optional

import pandas as pd

from database.connection import read_sql
from utils.helpers import safe_divide
from utils.sql_compat import date_filter


def get_daily_metrics(days: int = 90) -> pd.DataFrame:
    """Fetch pre-aggregated daily metrics."""
    query = """
        SELECT * FROM daily_metrics
        ORDER BY metric_date DESC
        LIMIT :days
    """
    df = read_sql(query, {"days": days})
    if not df.empty:
        df["metric_date"] = pd.to_datetime(df["metric_date"])
        df = df.sort_values("metric_date")
    return df


def get_executive_kpis(as_of_date: Optional[datetime] = None) -> dict:
    """Calculate executive dashboard KPIs."""
    df = get_daily_metrics(90)
    if df.empty:
        return {}

    latest_row = df[df["dau"] > 0]
    latest = latest_row.iloc[-1] if not latest_row.empty else df.iloc[-1]
    prev_week = df.iloc[-8] if len(df) >= 8 else df.iloc[0]
    prev_month = df.iloc[-31] if len(df) >= 31 else df.iloc[0]

    dau = int(latest["dau"])
    wau = int(latest["wau"])
    mau = int(latest["mau"])
    stickiness = safe_divide(dau, mau)

    return {
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "stickiness": stickiness,
        "dau_wow_change": safe_divide(dau - prev_week["dau"], prev_week["dau"]),
        "wau_wow_change": safe_divide(wau - prev_week["wau"], prev_week["wau"]),
        "mau_mom_change": safe_divide(mau - prev_month["mau"], prev_month["mau"]),
        "avg_session_length": float(latest["avg_session_length"]),
        "engagement_rate": float(latest["engagement_rate"]),
        "reels_watch_time_hours": float(latest["reels_watch_time_hours"]),
        "churn_rate": float(latest["churn_rate"]),
        "retention_d7": float(latest["retention_d7"]),
        "new_users": int(latest["new_users"]),
        "sessions": int(latest["sessions"]),
    }


def get_feature_adoption(days: int = 30) -> pd.DataFrame:
    """Feature adoption rates by unique users."""
    query = f"""
        SELECT feature,
               COUNT(DISTINCT user_id) AS unique_users,
               SUM(usage_count) AS total_usage,
               AVG(time_spent_sec) AS avg_time_spent
        FROM feature_usage
        WHERE {date_filter("usage_date", days)}
        GROUP BY feature
        ORDER BY unique_users DESC
    """
    df = read_sql(query)
    if not df.empty:
        total_users = read_sql("SELECT COUNT(*) AS cnt FROM users")["cnt"].iloc[0]
        df["adoption_rate"] = df["unique_users"] / max(total_users, 1)
    return df


def get_geographic_breakdown(days: int = 30) -> pd.DataFrame:
    """DAU by country."""
    query = f"""
        SELECT u.country,
               COUNT(DISTINCT e.user_id) AS active_users,
               COUNT(*) AS total_events,
               AVG(CASE WHEN e.event_type IN ('like','comment','share') THEN 1.0 ELSE 0.0 END) AS engagement_rate
        FROM user_events e
        JOIN users u ON e.user_id = u.user_id
        WHERE {date_filter("e.event_timestamp", days)}
        GROUP BY u.country
        ORDER BY active_users DESC
    """
    return read_sql(query)


def get_device_breakdown(days: int = 30) -> pd.DataFrame:
    """Metrics by device type."""
    query = f"""
        SELECT u.device,
               COUNT(DISTINCT e.user_id) AS active_users,
               COUNT(*) AS total_events,
               AVG(s.duration_sec) AS avg_session_length
        FROM user_events e
        JOIN users u ON e.user_id = u.user_id
        LEFT JOIN sessions s ON e.user_id = s.user_id
        WHERE {date_filter("e.event_timestamp", days)}
        GROUP BY u.device
        ORDER BY active_users DESC
    """
    return read_sql(query)


def get_creator_engagement(days: int = 30) -> pd.DataFrame:
    """Creator vs consumer engagement metrics."""
    query = f"""
        SELECT u.is_creator,
               COUNT(DISTINCT u.user_id) AS user_count,
               COUNT(e.event_id) AS total_events,
               AVG(CASE WHEN e.event_type = 'reel_view' THEN e.value END) AS avg_reel_watch_time
        FROM users u
        LEFT JOIN user_events e ON u.user_id = e.user_id
            AND {date_filter("e.event_timestamp", days)}
        GROUP BY u.is_creator
    """
    return read_sql(query)


def get_user_growth_trend(days: int = 180) -> pd.DataFrame:
    """Daily new user signups."""
    query = f"""
        SELECT DATE(created_at) AS signup_date, COUNT(*) AS new_users
        FROM users
        WHERE {date_filter("created_at", days)}
        GROUP BY DATE(created_at)
        ORDER BY signup_date
    """
    df = read_sql(query)
    if not df.empty:
        df["signup_date"] = pd.to_datetime(df["signup_date"])
        df["cumulative_users"] = df["new_users"].cumsum()
    return df


def get_engagement_trends(days: int = 90) -> pd.DataFrame:
    """Daily engagement metrics trend."""
    query = f"""
        SELECT DATE(event_timestamp) AS event_date,
               COUNT(DISTINCT user_id) AS dau,
               SUM(CASE WHEN event_type IN ('like','comment','share','save') THEN 1 ELSE 0 END) AS engagements,
               SUM(CASE WHEN event_type = 'reel_view' THEN value ELSE 0 END) / 3600.0 AS reels_hours
        FROM user_events
        WHERE {date_filter("event_timestamp", days)}
        GROUP BY DATE(event_timestamp)
        ORDER BY event_date
    """
    df = read_sql(query)
    if not df.empty:
        df["event_date"] = pd.to_datetime(df["event_date"])
        df["engagement_rate"] = df["engagements"] / df["dau"].clip(lower=1)
    return df


def get_north_star_metrics(days: int = 90) -> pd.DataFrame:
    """Weekly Engaged Users (WEU) - North Star metric."""
    query = f"""
        SELECT DATE(event_timestamp) AS event_date,
               COUNT(DISTINCT CASE
                   WHEN event_type IN ('like','comment','share','reel_view','story_view','post_view')
                   THEN user_id END) AS engaged_users
        FROM user_events
        WHERE {date_filter("event_timestamp", days)}
        GROUP BY DATE(event_timestamp)
        ORDER BY event_date
    """
    df = read_sql(query)
    if not df.empty:
        df["event_date"] = pd.to_datetime(df["event_date"])
        df["weu_7d"] = df["engaged_users"].rolling(7, min_periods=1).mean()
    return df
