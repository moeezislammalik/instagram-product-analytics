"""User segmentation analytics."""

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from database.connection import read_sql
from utils.sql_compat import date_filter


def get_segment_distribution() -> pd.DataFrame:
    """Current user segment distribution."""
    query = """
        SELECT segment, COUNT(*) AS user_count,
               AVG(follower_count) AS avg_followers,
               AVG(following_count) AS avg_following
        FROM users
        GROUP BY segment
        ORDER BY user_count DESC
    """
    df = read_sql(query)
    if not df.empty:
        total = df["user_count"].sum()
        df["pct_of_total"] = df["user_count"] / total
    return df


def get_segment_engagement(days: int = 30) -> pd.DataFrame:
    """Engagement metrics by user segment."""
    query = f"""
        SELECT u.segment,
               COUNT(DISTINCT e.user_id) AS active_users,
               COUNT(e.event_id) AS total_events,
               CAST(COUNT(e.event_id) AS FLOAT) / NULLIF(COUNT(DISTINCT e.user_id), 0) AS events_per_user
        FROM users u
        JOIN user_events e ON u.user_id = e.user_id
        WHERE {date_filter("e.event_timestamp", days)}
        GROUP BY u.segment
        ORDER BY events_per_user DESC
    """
    return read_sql(query)


def get_rfm_segments() -> pd.DataFrame:
    """
    RFM (Recency, Frequency, Monetary proxy) segmentation.

    Uses event frequency and recency as engagement proxies.
    """
    query = """
        SELECT u.user_id, u.segment, u.country, u.device,
               MAX(e.event_timestamp) AS last_active,
               COUNT(e.event_id) AS frequency,
               COUNT(DISTINCT DATE(e.event_timestamp)) AS active_days
        FROM users u
        LEFT JOIN user_events e ON u.user_id = e.user_id
        GROUP BY u.user_id, u.segment, u.country, u.device
    """
    df = read_sql(query)
    if df.empty:
        return df

    df["last_active"] = pd.to_datetime(df["last_active"])
    df["recency_days"] = (pd.Timestamp.now() - df["last_active"]).dt.days.fillna(999)

    features = df[["recency_days", "frequency", "active_days"]].fillna(0)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df["rfm_cluster"] = kmeans.fit_predict(scaled)

    cluster_labels = {
        0: "Champions", 1: "Loyal", 2: "At Risk", 3: "Hibernating", 4: "New",
    }
    df["rfm_segment"] = df["rfm_cluster"].map(cluster_labels)
    return df


def get_churn_risk_segments() -> pd.DataFrame:
    """Identify user segments at highest churn risk."""
    rfm = get_rfm_segments()
    if rfm.empty:
        return rfm

    at_risk = rfm[
        (rfm["recency_days"] > 14) |
        (rfm["segment"].isin(["At Risk", "Casual", "Lurker"]))
    ].copy()

    summary = at_risk.groupby(["segment", "country"]).agg(
        user_count=("user_id", "count"),
        avg_recency=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
    ).reset_index().sort_values("user_count", ascending=False)

    return summary.head(50)
