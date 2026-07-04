"""Experimentation Center dashboard page."""

import streamlit as st
import plotly.express as px
import pandas as pd

from analytics.experiments import (
    analyze_uploaded_experiment,
    get_experiment_summary,
    run_significance_test,
)
from dashboard.styles import plotly_theme, render_header


def render():
    render_header(
        "Experimentation Center",
        "A/B test analysis, statistical significance & ship recommendations",
    )

    tab1, tab2 = st.tabs(["Experiment Dashboard", "Upload A/B Test Data"])

    with tab1:
        summary = get_experiment_summary()
        if summary.empty:
            st.warning("No experiments found. Seed the database first.")
            return

        experiments = summary["name"].unique()
        selected = st.selectbox("Select Experiment", experiments)

        exp_data = summary[summary["name"] == selected]
        exp_id = exp_data["experiment_id"].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", exp_data["status"].iloc[0].title())
        with col2:
            st.metric("Primary Metric", exp_data["primary_metric"].iloc[0])
        with col3:
            st.metric("Total Sample", f"{exp_data['sample_size'].sum():,}")

        # Conversion rate comparison
        fig = px.bar(exp_data, x="variant", y="conversion_rate", color="variant",
                     title=f"Conversion Rate by Variant — {selected}",
                     text=exp_data["conversion_rate"].apply(lambda x: f"{x:.2%}"),
                     color_discrete_sequence=px.colors.sequential.RdPu)
        fig.update_traces(textposition="outside")
        fig = plotly_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            fig2 = px.bar(exp_data, x="variant", y="avg_engagement", color="variant",
                          title="Average Engagement Score", color_discrete_sequence=px.colors.sequential.RdPu)
            fig2 = plotly_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)
        with col_b:
            fig3 = px.bar(exp_data, x="variant", y="sample_size", color="variant",
                          title="Sample Size by Variant", color_discrete_sequence=px.colors.sequential.RdPu)
            fig3 = plotly_theme(fig3)
            st.plotly_chart(fig3, use_container_width=True)

        # Statistical significance
        st.subheader("Statistical Significance Testing")
        metric = st.selectbox("Test Metric", ["conversion_rate", "engagement_score", "sessions_count"])
        results = run_significance_test(exp_id, metric)

        if "error" not in results:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Control Mean", f"{results['control_mean']:.4f}")
            with col2:
                st.metric("Treatment Mean", f"{results['treatment_mean']:.4f}")
            with col3:
                st.metric("Lift", results["lift_pct"],
                          delta_color="normal" if results["lift"] > 0 else "inverse")
            with col4:
                sig_label = "Yes ✓" if results["significant"] else "No ✗"
                st.metric("Significant (p<0.05)", sig_label)

            col5, col6 = st.columns(2)
            with col5:
                st.metric("P-Value", f"{results['p_value']:.6f}")
                st.metric("T-Statistic", f"{results['t_statistic']:.4f}")
            with col6:
                ci = results["confidence_interval"]
                st.metric("95% CI", f"[{ci[0]:.4f}, {ci[1]:.4f}]")
                st.metric("Sample Sizes", f"Control: {results['control_n']:,} | Treatment: {results['treatment_n']:,}")

            if results["significant"]:
                st.success(f"**Winner: {results['winner']}** — {results['recommendation']}")
            else:
                st.warning(f"**Result: {results['winner']}** — {results['recommendation']}")
        else:
            st.error(results["error"])

        st.subheader("All Experiments Overview")
        pivot = summary.pivot_table(
            index="name", columns="variant", values="conversion_rate", aggfunc="first",
        ).reset_index()
        st.dataframe(pivot, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Upload A/B Test Results")
        st.markdown("""
        Upload a CSV with columns: **variant** (control/treatment), **converted** (0/1 or numeric metric).
        Additional columns like user_id, sessions, revenue are supported.
        """)

        uploaded = st.file_uploader("Upload experiment CSV", type=["csv"])
        if uploaded:
            df = pd.read_csv(uploaded)
            st.dataframe(df.head(10), use_container_width=True)

            results = analyze_uploaded_experiment(df)
            if "error" in results:
                st.error(results["error"])
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Control Mean", f"{results['control_mean']:.4f}")
                with col2:
                    st.metric("Treatment Mean", f"{results['treatment_mean']:.4f}")
                with col3:
                    st.metric("Lift", results["lift_pct"])

                col4, col5 = st.columns(2)
                with col4:
                    st.metric("P-Value", f"{results['p_value']:.6f}")
                with col5:
                    st.metric("Winner", results["winner"])

                if results["significant"]:
                    st.success(f"Statistically significant! Recommendation: **{results['recommendation']}**")
                else:
                    st.info("Not statistically significant. Consider running longer or increasing sample size.")

        else:
            st.info("Upload a CSV file to analyze custom A/B test data.")
            sample = pd.DataFrame({
                "variant": ["control"] * 100 + ["treatment"] * 100,
                "converted": [1] * 12 + [0] * 88 + [1] * 15 + [0] * 85,
                "user_id": range(200),
            })
            st.download_button(
                "Download Sample CSV",
                sample.to_csv(index=False),
                "sample_experiment.csv",
                "text/csv",
            )
