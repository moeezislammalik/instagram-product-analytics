"""Predictive Analytics dashboard page."""

import streamlit as st
import plotly.express as px
import pandas as pd

from machine_learning.churn_model import predict_churn_risk, train_churn_model
from machine_learning.engagement_model import predict_engagement, train_engagement_model
from machine_learning.forecasting import forecast_dau, forecast_engagement, forecast_retention
from machine_learning.shap_analysis import get_shap_values
from dashboard.styles import create_bar_chart, create_line_chart, plotly_theme, render_header


def render():
    render_header(
        "Predictive Analytics",
        "Churn prediction, engagement forecasting, DAU projections & SHAP explainability",
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Churn Prediction", "Engagement Prediction", "Forecasting", "SHAP Analysis",
    ])

    with tab1:
        if st.button("Train / Retrain Churn Model"):
            with st.spinner("Training churn model..."):
                try:
                    result = train_churn_model()
                    if "error" not in result:
                        st.success(
                            f"Model trained successfully — AUC: {result['auc_score']:.3f}, "
                            f"churn rate: {result['churn_rate']:.1%}"
                        )
                        with st.expander("Feature importance details"):
                            st.json(result["feature_importance"])
                    else:
                        st.error(result["error"])
                except Exception as exc:
                    st.error(f"Training failed: {exc}")

        try:
            churn = predict_churn_risk()
        except Exception as exc:
            st.error(f"Could not load churn predictions: {exc}")
            churn = pd.DataFrame()

        if churn.empty:
            st.info("Train the churn model using the button above to see predictions.")
        else:
            col1, col2, col3 = st.columns(3)
            risk_counts = churn["risk_level"].value_counts()
            with col1:
                st.metric("High Risk Users", f"{risk_counts.get('High', 0):,}")
            with col2:
                st.metric("Medium Risk", f"{risk_counts.get('Medium', 0):,}")
            with col3:
                st.metric("Low Risk", f"{risk_counts.get('Low', 0):,}")

            fig = px.histogram(churn, x="churn_probability", color="risk_level",
                               title="Churn Probability Distribution",
                               nbins=50, color_discrete_sequence=px.colors.sequential.RdPu)
            fig = plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Highest Churn Risk Users")
            high_risk = churn[churn["risk_level"] == "High"].head(20)
            st.dataframe(high_risk, use_container_width=True, hide_index=True)

            by_segment = churn.groupby("segment")["churn_probability"].mean().reset_index()
            fig2 = create_bar_chart(by_segment, "segment", "churn_probability", "Avg Churn Probability by Segment")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        if st.button("Train / Retrain Engagement Model"):
            with st.spinner("Training engagement model..."):
                result = train_engagement_model()
                if "error" not in result:
                    st.success(f"Model trained! R²: {result['r2']:.3f}, MAE: {result['mae']:.3f}")
                else:
                    st.error(result["error"])

        engagement = predict_engagement()
        if not engagement.empty:
            fig = px.scatter(engagement.head(500), x="predicted_engagement", color="segment",
                             title="Predicted Engagement by Segment",
                             color_discrete_sequence=px.colors.sequential.RdPu)
            fig = plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Top 20 Predicted Engaged Users")
            st.dataframe(engagement.head(20), use_container_width=True, hide_index=True)

    with tab3:
        periods = st.slider("Forecast horizon (days)", 7, 90, 30)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("DAU Forecast")
            dau_fc = forecast_dau(periods)
            if not dau_fc.empty:
                fig = px.line(dau_fc, x="ds", y=["yhat", "yhat_lower", "yhat_upper"],
                              title="DAU Forecast with Confidence Interval",
                              labels={"ds": "Date", "value": "DAU", "variable": "Metric"})
                fig = plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Engagement Rate Forecast")
            eng_fc = forecast_engagement(periods)
            if not eng_fc.empty:
                fig = px.line(eng_fc, x="ds", y=["yhat", "yhat_lower", "yhat_upper"],
                              title="Engagement Rate Forecast")
                fig = plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("D7 Retention Forecast")
        ret_fc = forecast_retention(periods)
        if not ret_fc.empty:
            fig = px.line(ret_fc, x="ds", y=["yhat", "yhat_lower", "yhat_upper"],
                          title="D7 Retention Forecast")
            fig.update_yaxes(tickformat=".0%")
            fig = plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Feature Importance (SHAP Values)")
        st.markdown("SHAP (SHapley Additive exPlanations) reveals which features drive churn predictions.")

        if st.button("Compute SHAP Values"):
            with st.spinner("Computing SHAP values..."):
                shap_result = get_shap_values()
                if "error" in shap_result:
                    st.error(shap_result["error"])
                else:
                    importance = shap_result["importance"]
                    fig = create_bar_chart(
                        importance, "feature", "mean_abs_shap",
                        "Feature Importance (Mean |SHAP|)",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(importance, use_container_width=True, hide_index=True)

                    if shap_result.get("fallback"):
                        st.info("Using model feature importance (SHAP library fallback).")

                    st.markdown("""
                    **Interpretation Guide:**
                    - **recency_days**: Days since last activity — strongest churn signal
                    - **engagement_rate**: Ratio of engaging actions to total events
                    - **active_days**: Number of distinct active days
                    - **reel_views**: Reels consumption depth
                    """)
