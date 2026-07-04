"""A/B test statistical analysis."""

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats

from database.connection import read_sql
from utils.sql_compat import bool_avg, date_filter


def get_experiment_summary(experiment_id: Optional[int] = None) -> pd.DataFrame:
    """Get summary statistics for all experiments."""
    where = "WHERE e.experiment_id = :exp_id" if experiment_id else ""
    params = {"exp_id": experiment_id} if experiment_id else {}

    query = f"""
        SELECT ex.experiment_id, ex.name, ex.status, ex.primary_metric,
               ea.variant,
               COUNT(*) AS sample_size,
               SUM(CASE WHEN ea.converted THEN 1 ELSE 0 END) AS conversions,
               {bool_avg("ea.converted")} AS conversion_rate,
               AVG(ea.engagement_score) AS avg_engagement,
               AVG(ea.sessions_count) AS avg_sessions,
               AVG(ea.conversion_value) AS avg_conversion_value
        FROM experiments ex
        JOIN experiment_assignments ea ON ex.experiment_id = ea.experiment_id
        {where}
        GROUP BY ex.experiment_id, ex.name, ex.status, ex.primary_metric, ea.variant
        ORDER BY ex.experiment_id, ea.variant
    """
    return read_sql(query, params)


def run_significance_test(
    experiment_id: int,
    metric: str = "conversion_rate",
) -> dict:
    """
    Run two-sample z-test comparing treatment vs control.

    Returns p-value, confidence interval, lift, and winner recommendation.
    """
    query = """
        SELECT variant, converted, engagement_score, sessions_count, conversion_value
        FROM experiment_assignments
        WHERE experiment_id = :exp_id
    """
    df = read_sql(query, {"exp_id": experiment_id})
    if df.empty:
        return {"error": "No data for experiment"}

    control = df[df["variant"] == "control"]
    treatment = df[df["variant"] != "control"]

    if metric == "conversion_rate":
        c_vals = control["converted"].astype(float)
        t_vals = treatment["converted"].astype(float)
    elif metric == "engagement_score":
        c_vals = control["engagement_score"]
        t_vals = treatment["engagement_score"]
    else:
        c_vals = control["sessions_count"].astype(float)
        t_vals = treatment["sessions_count"].astype(float)

    c_mean, t_mean = c_vals.mean(), t_vals.mean()
    c_n, t_n = len(c_vals), len(t_vals)

    if c_n == 0 or t_n == 0:
        return {"error": "Insufficient sample size"}

    # Two-sample t-test
    t_stat, p_value = stats.ttest_ind(t_vals, c_vals, equal_var=False)

    # Lift calculation
    lift = (t_mean - c_mean) / c_mean if c_mean != 0 else 0

    # Confidence interval for difference in means
    se = np.sqrt(c_vals.var() / c_n + t_vals.var() / t_n)
    ci_low = (t_mean - c_mean) - 1.96 * se
    ci_high = (t_mean - c_mean) + 1.96 * se

    # Winner recommendation
    alpha = 0.05
    if p_value < alpha and lift > 0:
        winner = "Treatment (statistically significant positive lift)"
        recommendation = "Ship treatment variant"
    elif p_value < alpha and lift < 0:
        winner = "Control (treatment underperforms)"
        recommendation = "Do not ship; investigate treatment"
    else:
        winner = "Inconclusive"
        recommendation = "Continue experiment or increase sample size"

    return {
        "experiment_id": experiment_id,
        "metric": metric,
        "control_mean": float(c_mean),
        "treatment_mean": float(t_mean),
        "control_n": c_n,
        "treatment_n": t_n,
        "lift": float(lift),
        "lift_pct": f"{lift * 100:.2f}%",
        "p_value": float(p_value),
        "significant": p_value < alpha,
        "confidence_interval": (float(ci_low), float(ci_high)),
        "t_statistic": float(t_stat),
        "winner": winner,
        "recommendation": recommendation,
    }


def analyze_uploaded_experiment(df: pd.DataFrame) -> dict:
    """
    Analyze uploaded A/B test CSV data.

    Expected columns: variant, converted (or metric column).
    """
    required = {"variant"}
    if not required.issubset(df.columns):
        return {"error": f"CSV must contain columns: {required}"}

    metric_col = "converted" if "converted" in df.columns else df.select_dtypes(include=[np.number]).columns[0]
    df[metric_col] = pd.to_numeric(df[metric_col], errors="coerce")

    control = df[df["variant"].str.lower() == "control"][metric_col]
    treatment = df[df["variant"].str.lower() != "control"][metric_col]

    if len(control) == 0 or len(treatment) == 0:
        return {"error": "Need both control and treatment variants"}

    t_stat, p_value = stats.ttest_ind(treatment, control, equal_var=False)
    c_mean, t_mean = control.mean(), treatment.mean()
    lift = (t_mean - c_mean) / c_mean if c_mean != 0 else 0

    return {
        "control_mean": float(c_mean),
        "treatment_mean": float(t_mean),
        "control_n": len(control),
        "treatment_n": len(treatment),
        "lift": float(lift),
        "lift_pct": f"{lift * 100:.2f}%",
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "winner": "Treatment" if p_value < 0.05 and lift > 0 else "Control" if p_value < 0.05 else "Inconclusive",
        "recommendation": "Ship treatment" if p_value < 0.05 and lift > 0 else "Do not ship",
    }
