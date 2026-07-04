"""Churn prediction model using scikit-learn."""

import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

from config import MODELS_DIR
from database.connection import read_sql
from utils.helpers import get_reference_date


def _build_churn_features() -> pd.DataFrame:
    """Build feature matrix for churn prediction."""
    query = """
        SELECT u.user_id, u.segment, u.country, u.device,
               u.is_creator, u.follower_count, u.following_count,
               u.created_at,
               MAX(e.event_timestamp) AS last_active,
               COUNT(e.event_id) AS total_events,
               COUNT(DISTINCT DATE(e.event_timestamp)) AS active_days,
               COUNT(DISTINCT e.session_id) AS session_count,
               SUM(CASE WHEN e.event_type = 'reel_view' THEN 1 ELSE 0 END) AS reel_views,
               SUM(CASE WHEN e.event_type IN ('like','comment','share') THEN 1 ELSE 0 END) AS engagements
        FROM users u
        LEFT JOIN user_events e ON u.user_id = e.user_id
        GROUP BY u.user_id, u.segment, u.country, u.device,
                 u.is_creator, u.follower_count, u.following_count, u.created_at
    """
    df = read_sql(query)
    if df.empty:
        return df

    ref = get_reference_date()
    df["last_active"] = pd.to_datetime(df["last_active"])
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["recency_days"] = (ref - df["last_active"]).dt.days.fillna(999)
    df["account_age_days"] = (ref - df["created_at"]).dt.days

    # Churn label: inactive for 30+ days as of dataset end date
    df["churned"] = (df["recency_days"] > 30).astype(int)

    df["engagement_rate"] = df["engagements"] / df["total_events"].clip(lower=1)
    df["events_per_day"] = df["total_events"] / df["active_days"].clip(lower=1)

    return df


def train_churn_model() -> dict:
    """Train and persist churn prediction model."""
    df = _build_churn_features()
    if df.empty:
        return {"error": "No data available"}

    feature_cols = [
        "recency_days", "total_events", "active_days", "session_count",
        "reel_views", "engagements", "follower_count", "following_count",
        "account_age_days", "engagement_rate", "events_per_day",
    ]
    X = df[feature_cols].fillna(0)
    y = df["churned"]

    if y.nunique() < 2:
        return {
            "error": "Insufficient class variation for churn model. "
            "Ensure event data spans multiple activity periods.",
        }

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify,
    )

    model = GradientBoostingClassifier(
        n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob) if y_test.nunique() > 1 else 0.0

    model_path = MODELS_DIR / "churn_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({"model": model, "features": feature_cols}, f)

    return {
        "auc_score": float(auc),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "churn_rate": float(y.mean()),
        "feature_importance": dict(zip(feature_cols, model.feature_importances_.tolist())),
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
    }


def predict_churn_risk() -> pd.DataFrame:
    """Predict churn probability for all users."""
    model_path = MODELS_DIR / "churn_model.pkl"
    if not model_path.exists():
        result = train_churn_model()
        if "error" in result:
            return pd.DataFrame()

    try:
        with open(model_path, "rb") as f:
            saved = pickle.load(f)
    except Exception:
        return pd.DataFrame()

    model = saved["model"]
    feature_cols = saved["features"]

    df = _build_churn_features()
    if df.empty:
        return df

    X = df[feature_cols].fillna(0)
    df["churn_probability"] = model.predict_proba(X)[:, 1]
    df["risk_level"] = pd.cut(
        df["churn_probability"],
        bins=[0, 0.3, 0.6, 1.0],
        labels=["Low", "Medium", "High"],
    )

    return df[["user_id", "segment", "country", "recency_days", "churn_probability", "risk_level"]]
