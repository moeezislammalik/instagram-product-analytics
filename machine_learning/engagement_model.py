"""Engagement prediction model."""

import pickle

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from config import MODELS_DIR
from database.connection import read_sql


def _build_engagement_features() -> pd.DataFrame:
    """Build features for engagement score prediction."""
    query = """
        SELECT u.user_id, u.segment, u.is_creator, u.device,
               COUNT(e.event_id) AS total_events,
               COUNT(DISTINCT DATE(e.event_timestamp)) AS active_days,
               SUM(CASE WHEN e.event_type = 'reel_view' THEN 1 ELSE 0 END) AS reel_views,
               SUM(CASE WHEN e.event_type = 'story_view' THEN 1 ELSE 0 END) AS story_views,
               SUM(CASE WHEN e.event_type IN ('like','comment','share','save') THEN 1 ELSE 0 END) AS engagements,
               AVG(CASE WHEN e.event_type = 'reel_view' THEN e.value END) AS avg_reel_time
        FROM users u
        LEFT JOIN user_events e ON u.user_id = e.user_id
        GROUP BY u.user_id, u.segment, u.is_creator, u.device
    """
    return read_sql(query)


def train_engagement_model() -> dict:
    """Train engagement prediction model."""
    df = _build_engagement_features()
    if df.empty:
        return {"error": "No data"}

    df["engagement_score"] = (
        df["engagements"] * 2 + df["reel_views"] + df["story_views"] * 0.5
    ) / df["active_days"].clip(lower=1)

    feature_cols = [
        "total_events", "active_days", "reel_views", "story_views",
        "engagements", "avg_reel_time",
    ]
    X = df[feature_cols].fillna(0)
    y = df["engagement_score"].fillna(0)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    model_path = MODELS_DIR / "engagement_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols}, f)

    return {
        "mae": float(mean_absolute_error(y_test, y_pred)),
        "r2": float(r2_score(y_test, y_pred)),
        "feature_importance": dict(zip(feature_cols, model.feature_importances_.tolist())),
    }


def predict_engagement() -> pd.DataFrame:
    """Predict engagement scores for users."""
    model_path = MODELS_DIR / "engagement_model.pkl"
    if not model_path.exists():
        train_engagement_model()

    with open(model_path, "rb") as f:
        saved = pickle.load(f)

    df = _build_engagement_features()
    X = df[saved["features"]].fillna(0)
    df["predicted_engagement"] = saved["model"].predict(X)
    return df[["user_id", "segment", "device", "predicted_engagement"]].sort_values(
        "predicted_engagement", ascending=False,
    )
