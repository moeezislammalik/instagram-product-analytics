"""Product Analytics dashboard page."""

import streamlit as st
import plotly.express as px

from analytics.cohorts import get_cohort_retention, get_retention_curve
from analytics.funnels import get_funnel_analysis, get_funnel_by_segment
from analytics.metrics import (
    get_engagement_trends,
    get_feature_adoption,
    get_north_star_metrics,
    get_user_growth_trend,
)
from analytics.segmentation import get_segment_distribution, get_segment_engagement
from dashboard.styles import (
    create_funnel_chart,
    create_heatmap,
    create_line_chart,
    plotly_theme,
    render_header,
)
from utils.helpers import format_pct


def render():
    render_header(
        "Product Analytics",
        "Growth trends, segmentation, cohorts, funnels & North Star metrics",
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Growth & Engagement", "Segmentation", "Cohort Retention",
        "Funnel Analysis", "North Star & KPIs",
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            growth = get_user_growth_trend(180)
            if not growth.empty:
                fig = create_line_chart(growth, "signup_date", "new_users", "Daily New User Signups")
                st.plotly_chart(fig, use_container_width=True)

                fig2 = create_line_chart(growth, "signup_date", "cumulative_users", "Cumulative User Growth")
                st.plotly_chart(fig2, use_container_width=True)

        with col2:
            engagement = get_engagement_trends(90)
            if not engagement.empty:
                fig = create_line_chart(engagement, "event_date", "engagement_rate", "Engagement Rate Trend")
                fig.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)

                fig2 = create_line_chart(engagement, "event_date", "reels_hours", "Reels Watch Time (Hours/Day)")
                st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Feature Adoption Trends")
        features = get_feature_adoption(90)
        if not features.empty:
            fig = px.treemap(features, path=["feature"], values="total_usage",
                             color="adoption_rate", title="Feature Usage Treemap",
                             color_continuous_scale="RdPu")
            fig = plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            segments = get_segment_distribution()
            if not segments.empty:
                fig = px.pie(segments, names="segment", values="user_count",
                             title="User Segment Distribution", color_discrete_sequence=px.colors.sequential.RdPu)
                fig = plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            seg_eng = get_segment_engagement(30)
            if not seg_eng.empty:
                fig = px.bar(seg_eng, x="segment", y="events_per_user",
                             title="Events per User by Segment", color="segment",
                             color_discrete_sequence=px.colors.sequential.RdPu)
                fig = plotly_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

        if not segments.empty:
            st.dataframe(segments, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Weekly Cohort Retention Matrix")
        retention = get_cohort_retention(max_periods=8)
        if not retention.empty:
            fig = create_heatmap(retention, "Cohort Retention (% of cohort active)")
            st.plotly_chart(fig, use_container_width=True)

            curve = get_retention_curve()
            if not curve.empty:
                fig2 = create_line_chart(curve, "period_num", "retention_rate", "Average Retention Curve")
                fig2.update_yaxes(tickformat=".0%")
                st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        days = st.slider("Funnel lookback (days)", 7, 90, 30)
        funnel = get_funnel_analysis(days)
        if not funnel.empty:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = create_funnel_chart(funnel)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("Conversion Rates")
                for _, row in funnel.iterrows():
                    st.metric(row["step"], f"{row['conversion_rate']:.1%}", f"{row['users']:,} users")

        seg_funnel = get_funnel_by_segment(days)
        if not seg_funnel.empty:
            fig = px.bar(seg_funnel, x="event_type", y="users", color="segment",
                         title="Events by Segment", barmode="group")
            fig = plotly_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    with tab5:
        ns = get_north_star_metrics(90)
        if not ns.empty:
            st.subheader("North Star Metric: Weekly Engaged Users (WEU)")
            fig = create_line_chart(ns, "event_date", "weu_7d", "7-Day Rolling Engaged Users")
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current WEU", f"{ns['weu_7d'].iloc[-1]:,.0f}")
            with col2:
                st.metric("Daily Engaged", f"{ns['engaged_users'].iloc[-1]:,.0f}")
            with col3:
                wow = (ns["weu_7d"].iloc[-1] - ns["weu_7d"].iloc[-8]) / ns["weu_7d"].iloc[-8] if len(ns) >= 8 else 0
                st.metric("WEU WoW Change", format_pct(wow))

        engagement = get_engagement_trends(30)
        if not engagement.empty:
            st.subheader("KPI Tracking (30 Days)")
            kpi_cols = st.columns(4)
            metrics_display = [
                ("DAU", engagement["dau"].iloc[-1], engagement["dau"].iloc[-8] if len(engagement) >= 8 else engagement["dau"].iloc[0]),
                ("Engagements/Day", engagement["engagements"].iloc[-1], engagement["engagements"].iloc[-8] if len(engagement) >= 8 else engagement["engagements"].iloc[0]),
                ("Engagement Rate", engagement["engagement_rate"].iloc[-1], engagement["engagement_rate"].iloc[-8] if len(engagement) >= 8 else engagement["engagement_rate"].iloc[0]),
                ("Reels Hours", engagement["reels_hours"].iloc[-1], engagement["reels_hours"].iloc[-8] if len(engagement) >= 8 else engagement["reels_hours"].iloc[0]),
            ]
            for col, (name, current, previous) in zip(kpi_cols, metrics_display):
                with col:
                    delta = (current - previous) / max(previous, 0.001)
                    fmt = format_pct(current) if "Rate" in name else f"{current:,.0f}"
                    st.metric(name, fmt, f"{delta*100:+.1f}%")
