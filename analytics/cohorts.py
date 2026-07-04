"""Cohort retention analysis."""

import pandas as pd
import numpy as np

from database.connection import read_sql


def get_cohort_retention(max_periods: int = 12) -> pd.DataFrame:
    """
    Calculate weekly cohort retention matrix.

    Returns DataFrame with cohort week as index and period (0, 1, 2, ...) as columns.
    """
    query = """
        SELECT user_id, DATE(created_at) AS cohort_date, created_at
        FROM users
    """
    users = read_sql(query)
    if users.empty:
        return pd.DataFrame()

    users["cohort_date"] = pd.to_datetime(users["cohort_date"])
    users["cohort_week"] = users["cohort_date"].dt.to_period("W").dt.start_time

    events_query = """
        SELECT user_id, DATE(event_timestamp) AS activity_date
        FROM user_events
        GROUP BY user_id, DATE(event_timestamp)
    """
    events = read_sql(events_query)
    events["activity_date"] = pd.to_datetime(events["activity_date"])
    events["activity_week"] = events["activity_date"].dt.to_period("W").dt.start_time

    merged = events.merge(users[["user_id", "cohort_week"]], on="user_id")
    merged["period"] = (
        (merged["activity_week"] - merged["cohort_week"]).dt.days // 7
    ).clip(lower=0)

    cohort_sizes = users.groupby("cohort_week")["user_id"].nunique()
    retention = merged.groupby(["cohort_week", "period"])["user_id"].nunique().unstack(fill_value=0)

    for col in retention.columns:
        retention[col] = retention[col] / cohort_sizes

    retention = retention.loc[:, :max_periods]
    retention.index = retention.index.strftime("%Y-%m-%d")
    retention.columns = [f"Week {c}" for c in retention.columns]

    return retention.tail(20)


def get_retention_curve() -> pd.DataFrame:
    """Average retention curve across all cohorts."""
    retention = get_cohort_retention()
    if retention.empty:
        return pd.DataFrame()

    avg = retention.mean(axis=0).reset_index()
    avg.columns = ["period", "retention_rate"]
    avg["period_num"] = avg["period"].str.extract(r"(\d+)").astype(int)
    return avg.sort_values("period_num")
