"""
Synthetic Instagram dataset generator.

Generates realistic user behavior patterns including seasonality,
geographic distribution, device mix, and experiment assignments.
"""

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from tqdm import tqdm

from config import DATA_END_DATE, DATA_START_DATE, NUM_EVENTS, NUM_USERS
from database.models import (
    DailyMetric,
    Experiment,
    ExperimentAssignment,
    FeatureUsage,
    Post,
    Reel,
    Session as UserSession,
    Story,
    User,
    UserEvent,
)
from utils.constants import (
    ACQUISITION_CHANNELS,
    CONTENT_TYPES,
    COUNTRIES,
    DEVICES,
    EVENT_TYPES,
    EXPERIMENT_NAMES,
    EXPERIMENT_VARIANTS,
    FEATURES,
    USER_SEGMENTS,
)


def _random_dates(start: str, end: str, n: int) -> np.ndarray:
    """Generate n random timestamps between start and end."""
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    delta = (end_ts - start_ts).total_seconds()
    offsets = np.random.uniform(0, delta, n)
    return start_ts + pd.to_timedelta(offsets, unit="s")


def _country_weights() -> list[float]:
    """Realistic country distribution weights."""
    weights = [
        0.18, 0.15, 0.10, 0.08, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03,
        0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02,
    ]
    total = sum(weights)
    return [w / total for w in weights]


def generate_users(n: int = NUM_USERS) -> pd.DataFrame:
    """Generate synthetic user profiles."""
    rng = np.random.default_rng(42)
    countries = rng.choice(COUNTRIES, size=n, p=_country_weights())
    devices = rng.choice(DEVICES, size=n, p=[0.45, 0.48, 0.07])
    channels = rng.choice(
        ACQUISITION_CHANNELS, size=n,
        p=[0.35, 0.20, 0.12, 0.10, 0.08, 0.05, 0.05, 0.05],
    )
    is_creator = rng.random(n) < 0.08
    created_at = _random_dates(DATA_START_DATE, DATA_END_DATE, n)

    segment_probs = [0.08, 0.25, 0.30, 0.15, 0.10, 0.07, 0.05]
    segments = rng.choice(USER_SEGMENTS, size=n, p=segment_probs)

    return pd.DataFrame({
        "username": [f"user_{i:06d}" for i in range(1, n + 1)],
        "created_at": created_at,
        "country": countries,
        "device": devices,
        "acquisition_channel": channels,
        "is_creator": is_creator,
        "follower_count": rng.integers(0, 50000, n) * is_creator.astype(int)
        + rng.integers(0, 500, n) * (~is_creator).astype(int),
        "following_count": rng.integers(10, 2000, n),
        "segment": segments,
    })


def _event_type_weights() -> dict[str, float]:
    return {
        "app_open": 0.12, "feed_view": 0.15, "reel_view": 0.18,
        "story_view": 0.12, "post_view": 0.10, "like": 0.12,
        "comment": 0.04, "share": 0.03, "follow": 0.02,
        "unfollow": 0.005, "save": 0.04, "dm_send": 0.03,
        "profile_view": 0.03, "search": 0.025, "explore_view": 0.035,
    }


def generate_events(
    user_ids: list[int],
    user_meta: pd.DataFrame,
    n_events: int = NUM_EVENTS,
    batch_size: int = 100_000,
) -> pd.DataFrame:
    """Generate user events in batches for memory efficiency."""
    weights = _event_type_weights()
    event_types = list(weights.keys())
    probs = np.array(list(weights.values()))
    probs /= probs.sum()

    rng = np.random.default_rng(123)
    all_batches = []

    for batch_start in tqdm(range(0, n_events, batch_size), desc="Generating events"):
        batch_n = min(batch_size, n_events - batch_start)
        uids = rng.choice(user_ids, size=batch_n)
        types = rng.choice(event_types, size=batch_n, p=probs)
        timestamps = _random_dates(DATA_START_DATE, DATA_END_DATE, batch_n)

        feature_map = {
            "reel_view": "Reels", "story_view": "Stories", "feed_view": "Feed",
            "explore_view": "Explore", "dm_send": "DMs", "like": "Feed",
            "comment": "Feed", "share": "Feed", "save": "Feed",
        }
        features = [feature_map.get(t, rng.choice(FEATURES)) for t in types]
        content_types = [
            "reel" if t == "reel_view" else
            "story" if t == "story_view" else
            rng.choice(CONTENT_TYPES)
            for t in types
        ]

        meta = user_meta.set_index("user_id").loc[uids]
        values = np.where(
            types == "reel_view",
            rng.exponential(45, batch_n),
            np.where(types == "story_view", rng.exponential(8, batch_n), 1.0),
        )

        batch = pd.DataFrame({
            "user_id": uids,
            "session_id": None,
            "event_type": types,
            "event_timestamp": timestamps,
            "feature": features,
            "content_type": content_types,
            "content_id": rng.integers(1, 100000, batch_n),
            "country": meta["country"].values,
            "device": meta["device"].values,
            "value": values,
        })
        all_batches.append(batch)

    return pd.concat(all_batches, ignore_index=True)


def generate_sessions(user_ids: list[int], user_meta: pd.DataFrame, n_sessions: int = 200_000) -> pd.DataFrame:
    """Generate session records."""
    rng = np.random.default_rng(456)
    uids = rng.choice(user_ids, size=n_sessions)
    started = _random_dates(DATA_START_DATE, DATA_END_DATE, n_sessions)
    duration = rng.exponential(420, n_sessions).clip(30, 3600)
    meta = user_meta.set_index("user_id").loc[uids]

    return pd.DataFrame({
        "user_id": uids,
        "started_at": started,
        "ended_at": started + pd.to_timedelta(duration, unit="s"),
        "duration_sec": duration,
        "device": meta["device"].values,
        "country": meta["country"].values,
    })


def generate_content(user_ids: list[int], creator_ids: list[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate posts, reels, and stories."""
    rng = np.random.default_rng(789)
    n_posts = 80_000
    n_reels = 60_000
    n_stories = 100_000

    post_users = rng.choice(user_ids, n_posts)
    posts = pd.DataFrame({
        "user_id": post_users,
        "created_at": _random_dates(DATA_START_DATE, DATA_END_DATE, n_posts),
        "content_type": rng.choice(["post", "carousel"], n_posts, p=[0.7, 0.3]),
        "like_count": rng.integers(0, 50000, n_posts),
        "comment_count": rng.integers(0, 5000, n_posts),
        "share_count": rng.integers(0, 2000, n_posts),
        "save_count": rng.integers(0, 3000, n_posts),
    })

    reel_users = rng.choice(creator_ids if creator_ids else user_ids, n_reels)
    reels = pd.DataFrame({
        "user_id": reel_users,
        "created_at": _random_dates(DATA_START_DATE, DATA_END_DATE, n_reels),
        "duration_sec": rng.uniform(5, 90, n_reels),
        "watch_time_sec": rng.exponential(120, n_reels),
        "view_count": rng.integers(100, 500000, n_reels),
        "like_count": rng.integers(10, 100000, n_reels),
        "share_count": rng.integers(0, 10000, n_reels),
    })

    story_users = rng.choice(user_ids, n_stories)
    stories = pd.DataFrame({
        "user_id": story_users,
        "created_at": _random_dates(DATA_START_DATE, DATA_END_DATE, n_stories),
        "view_count": rng.integers(10, 5000, n_stories),
        "reply_count": rng.integers(0, 200, n_stories),
        "tap_forward_count": rng.integers(0, 1000, n_stories),
    })

    return posts, reels, stories


def generate_experiments(user_ids: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate A/B test experiments and assignments."""
    rng = np.random.default_rng(101)
    start = pd.Timestamp(DATA_START_DATE)
    end = pd.Timestamp(DATA_END_DATE)

    experiments = pd.DataFrame({
        "name": EXPERIMENT_NAMES,
        "description": [
            f"A/B test for {name.replace('_', ' ')}" for name in EXPERIMENT_NAMES
        ],
        "start_date": [start + pd.Timedelta(days=i * 30) for i in range(len(EXPERIMENT_NAMES))],
        "end_date": [start + pd.Timedelta(days=i * 30 + 60) for i in range(len(EXPERIMENT_NAMES))],
        "status": ["completed"] * 5 + ["running"] * 4,
        "primary_metric": ["engagement_rate"] * len(EXPERIMENT_NAMES),
    })

    assignments = []
    for exp_idx in range(len(EXPERIMENT_NAMES)):
        sample_size = min(5000, len(user_ids))
        assigned_users = rng.choice(user_ids, size=sample_size, replace=False)
        variants = rng.choice(
            EXPERIMENT_VARIANTS, size=sample_size, p=[0.34, 0.33, 0.33],
        )
        # Treatment B typically shows lift
        base_conv = 0.12
        conv_rates = {
            "control": base_conv,
            "treatment_a": base_conv * 1.05,
            "treatment_b": base_conv * 1.12,
        }
        for uid, variant in zip(assigned_users, variants):
            converted = rng.random() < conv_rates[variant]
            assignments.append({
                "experiment_id": exp_idx + 1,
                "user_id": uid,
                "variant": variant,
                "assigned_at": start + pd.Timedelta(days=exp_idx * 30 + rng.integers(0, 14)),
                "converted": converted,
                "conversion_value": rng.exponential(5) if converted else 0,
                "sessions_count": rng.integers(1, 50),
                "engagement_score": rng.uniform(0.1, 1.0) * (1.1 if variant == "treatment_b" else 1.0),
            })

    return experiments, pd.DataFrame(assignments)


def generate_feature_usage(user_ids: list[int], n_records: int = 150_000) -> pd.DataFrame:
    """Generate daily feature usage records."""
    rng = np.random.default_rng(202)
    uids = rng.choice(user_ids, size=n_records)
    features = rng.choice(FEATURES, size=n_records, p=[0.25, 0.20, 0.20, 0.10, 0.08, 0.05, 0.04, 0.03, 0.03, 0.02])
    dates = _random_dates(DATA_START_DATE, DATA_END_DATE, n_records).date

    return pd.DataFrame({
        "user_id": uids,
        "feature": features,
        "usage_date": dates,
        "usage_count": rng.integers(1, 30, n_records),
        "time_spent_sec": rng.exponential(300, n_records),
    })


def _bulk_insert(session: Session, model, df: pd.DataFrame, desc: str = "") -> None:
    """Bulk insert DataFrame records."""
    records = df.to_dict(orient="records")
    batch = 5000
    for i in tqdm(range(0, len(records), batch), desc=desc or f"Inserting {model.__tablename__}"):
        session.bulk_insert_mappings(model, records[i : i + batch])
        session.commit()


def compute_daily_metrics(events_df: pd.DataFrame, users_df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute daily aggregated metrics."""
    events_df = events_df.copy()
    events_df["event_timestamp"] = pd.to_datetime(events_df["event_timestamp"])
    events_df["date"] = events_df["event_timestamp"].dt.date

    dates = pd.date_range(DATA_START_DATE, DATA_END_DATE, freq="D")
    metrics = []

    for d in dates:
        day = d.date()
        day_events = events_df[events_df["date"] == day]
        dau = day_events["user_id"].nunique()

        week_start = d - pd.Timedelta(days=6)
        month_start = d - pd.Timedelta(days=29)
        week_events = events_df[
            (events_df["event_timestamp"] >= week_start) &
            (events_df["event_timestamp"] <= d)
        ]
        month_events = events_df[
            (events_df["event_timestamp"] >= month_start) &
            (events_df["event_timestamp"] <= d)
        ]
        wau = week_events["user_id"].nunique()
        mau = month_events["user_id"].nunique()

        new_users = len(users_df[pd.to_datetime(users_df["created_at"]).dt.date == day])
        sessions = len(day_events[day_events["event_type"] == "app_open"])
        engaged = day_events[day_events["event_type"].isin(["like", "comment", "share", "save"])]
        engagement_rate = engaged["user_id"].nunique() / max(dau, 1)

        reels_time = day_events.loc[day_events["event_type"] == "reel_view", "value"].sum() / 3600

        # Simulate retention/churn with slight trend
        day_idx = (d - pd.Timestamp(DATA_START_DATE)).days
        retention_d7 = 0.42 + 0.02 * np.sin(day_idx / 30) + np.random.normal(0, 0.01)
        churn_rate = max(0.01, 0.08 - retention_d7 * 0.05 + np.random.normal(0, 0.005))

        metrics.append({
            "metric_date": day,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "new_users": new_users,
            "sessions": sessions,
            "avg_session_length": day_events.groupby("user_id").size().mean() * 45 if dau else 0,
            "engagement_rate": min(engagement_rate, 1.0),
            "reels_watch_time_hours": reels_time,
            "churn_rate": churn_rate,
            "retention_d7": min(max(retention_d7, 0.2), 0.7),
        })

    return pd.DataFrame(metrics)


def seed_database(session: Session, force: bool = False) -> dict:
    """
    Seed the database with synthetic Instagram data.

    Returns summary statistics about generated data.
    """
    from sqlalchemy import func
    from database.models import User as UserModel

    existing = session.query(func.count(UserModel.user_id)).scalar()
    if existing and existing > 0 and not force:
        return {"status": "skipped", "message": f"Database already has {existing:,} users. Use force=True to regenerate."}

    if force:
        session.query(DailyMetric).delete()
        session.query(FeatureUsage).delete()
        session.query(ExperimentAssignment).delete()
        session.query(Experiment).delete()
        session.query(UserEvent).delete()
        session.query(UserSession).delete()
        session.query(Story).delete()
        session.query(Reel).delete()
        session.query(Post).delete()
        session.query(UserModel).delete()
        session.commit()

    print(f"Generating {NUM_USERS:,} users and {NUM_EVENTS:,} events...")
    users_df = generate_users(NUM_USERS)
    _bulk_insert(session, User, users_df, "Inserting users")

    user_ids = session.query(UserModel.user_id).all()
    user_ids = [u[0] for u in user_ids]
    users_df["user_id"] = user_ids
    creator_ids = users_df[users_df["is_creator"]]["user_id"].tolist()

    sessions_df = generate_sessions(user_ids, users_df)
    _bulk_insert(session, UserSession, sessions_df, "Inserting sessions")

    events_df = generate_events(user_ids, users_df, NUM_EVENTS)
    _bulk_insert(session, UserEvent, events_df, "Inserting events")

    posts_df, reels_df, stories_df = generate_content(user_ids, creator_ids)
    _bulk_insert(session, Post, posts_df, "Inserting posts")
    _bulk_insert(session, Reel, reels_df, "Inserting reels")
    _bulk_insert(session, Story, stories_df, "Inserting stories")

    exp_df, assign_df = generate_experiments(user_ids)
    _bulk_insert(session, Experiment, exp_df, "Inserting experiments")
    _bulk_insert(session, ExperimentAssignment, assign_df, "Inserting experiment assignments")

    feature_df = generate_feature_usage(user_ids)
    _bulk_insert(session, FeatureUsage, feature_df, "Inserting feature usage")

    print("Computing daily metrics...")
    daily_df = compute_daily_metrics(events_df, users_df)
    _bulk_insert(session, DailyMetric, daily_df, "Inserting daily metrics")

    return {
        "status": "success",
        "users": len(users_df),
        "events": len(events_df),
        "sessions": len(sessions_df),
        "posts": len(posts_df),
        "reels": len(reels_df),
        "stories": len(stories_df),
        "experiments": len(exp_df),
        "feature_usage_records": len(feature_df),
    }
