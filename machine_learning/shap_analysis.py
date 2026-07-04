"""SHAP-based feature importance analysis."""

import pickle

import numpy as np
import pandas as pd

from config import MODELS_DIR
from machine_learning.churn_model import _build_churn_features, train_churn_model


def get_shap_values(sample_size: int = 500) -> dict:
    """
    Compute SHAP values for churn model feature importance.

    Returns feature importance DataFrame and summary statistics.
    """
    model_path = MODELS_DIR / "churn_model.pkl"
    if not model_path.exists():
        result = train_churn_model()
        if "error" in result:
            return {"error": result["error"]}

    with open(model_path, "rb") as f:
        saved = pickle.load(f)

    model = saved["model"]
    feature_cols = saved["features"]

    df = _build_churn_features()
    if df.empty:
        return {"error": "No data"}

    X = df[feature_cols].fillna(0)
    if len(X) > sample_size:
        X = X.sample(sample_size, random_state=42)

    try:
        import shap
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        importance = pd.DataFrame({
            "feature": feature_cols,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0),
            "mean_shap": shap_values.mean(axis=0),
        }).sort_values("mean_abs_shap", ascending=False)

        return {
            "importance": importance,
            "shap_values": shap_values,
            "features": feature_cols,
            "X_sample": X,
        }
    except Exception:
        # Fallback to model's built-in feature importance
        importance = pd.DataFrame({
            "feature": feature_cols,
            "mean_abs_shap": model.feature_importances_,
            "mean_shap": model.feature_importances_,
        }).sort_values("mean_abs_shap", ascending=False)

        return {"importance": importance, "fallback": True}
