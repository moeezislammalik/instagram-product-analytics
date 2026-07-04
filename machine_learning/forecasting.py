"""Time series forecasting with Prophet."""

import warnings

import pandas as pd

from analytics.metrics import get_daily_metrics, get_engagement_trends

warnings.filterwarnings("ignore")


def _prepare_prophet_df(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Convert to Prophet-required format (ds, y)."""
    result = df[[date_col, value_col]].copy()
    result.columns = ["ds", "y"]
    result["ds"] = pd.to_datetime(result["ds"])
    return result.dropna()


def forecast_dau(periods: int = 30) -> pd.DataFrame:
    """Forecast DAU using Prophet."""
    try:
        from prophet import Prophet
    except ImportError:
        return _fallback_forecast("dau", periods)

    df = get_daily_metrics(180)
    if df.empty:
        return pd.DataFrame()

    prophet_df = _prepare_prophet_df(df, "metric_date", "dau")
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods + 30)


def forecast_engagement(periods: int = 30) -> pd.DataFrame:
    """Forecast engagement rate."""
    try:
        from prophet import Prophet
    except ImportError:
        return _fallback_forecast("engagement_rate", periods)

    df = get_engagement_trends(180)
    if df.empty:
        return pd.DataFrame()

    prophet_df = _prepare_prophet_df(df, "event_date", "engagement_rate")
    model = Prophet(weekly_seasonality=True, changepoint_prior_scale=0.05)
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods + 30)


def forecast_retention(periods: int = 30) -> pd.DataFrame:
    """Forecast D7 retention rate."""
    try:
        from prophet import Prophet
    except ImportError:
        return _fallback_forecast("retention_d7", periods)

    df = get_daily_metrics(180)
    if df.empty:
        return pd.DataFrame()

    prophet_df = _prepare_prophet_df(df, "metric_date", "retention_d7")
    model = Prophet(weekly_seasonality=True)
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods + 30)


def _fallback_forecast(metric: str, periods: int) -> pd.DataFrame:
    """Simple linear trend fallback when Prophet unavailable."""
    if metric == "engagement_rate":
        df = get_engagement_trends(90)
        date_col, val_col = "event_date", "engagement_rate"
    else:
        df = get_daily_metrics(90)
        date_col, val_col = "metric_date", metric

    if df.empty:
        return pd.DataFrame()

    df[date_col] = pd.to_datetime(df[date_col])
    last_date = df[date_col].max()
    last_val = df[val_col].iloc[-1]
    trend = (df[val_col].iloc[-1] - df[val_col].iloc[0]) / len(df)

    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")
    return pd.DataFrame({
        "ds": future_dates,
        "yhat": [last_val + trend * (i + 1) for i in range(periods)],
        "yhat_lower": [last_val + trend * (i + 1) * 0.95 for i in range(periods)],
        "yhat_upper": [last_val + trend * (i + 1) * 1.05 for i in range(periods)],
    })
