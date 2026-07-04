"""Executive Dashboard page."""

import streamlit as st
import plotly.express as px

from analytics.metrics import (
    get_creator_engagement,
    get_daily_metrics,
    get_device_breakdown,
    get_executive_kpis,
    get_feature_adoption,
    get_geographic_breakdown,
)
from dashboard.styles import (
    create_bar_chart,
    create_line_chart,
    create_pie_chart,
    kpi_card,
    plotly_theme,
    render_header,
)
from utils.helpers import format_number, format_pct


def render():
    render_header(
        "Executive Dashboard",
        "Instagram Product Analytics — Real-time KPIs & Business Metrics",
    )

    kpis = get_executive_kpis()
    if not kpis:
        st.warning("No data available. Please seed the database first.")
        return

    # Primary KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("DAU", format_number(kpis["dau"]),
                 f"{kpis.get('dau_wow_change', 0)*100:+.1f}% WoW",
                 kpis.get("dau_wow_change", 0) >= 0)
    with col2:
        kpi_card("WAU", format_number(kpis["wau"]),
                 f"{kpis.get('wau_wow_change', 0)*100:+.1f}% WoW",
                 kpis.get("wau_wow_change", 0) >= 0)
    with col3:
        kpi_card("MAU", format_number(kpis["mau"]),
                 f"{kpis.get('mau_mom_change', 0)*100:+.1f}% MoM",
                 kpis.get("mau_mom_change", 0) >= 0)
    with col4:
        kpi_card("Stickiness (DAU/MAU)", format_pct(kpis["stickiness"]))

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Avg Session Length", f"{kpis['avg_session_length']:.0f}s")
    with col6:
        st.metric("Engagement Rate", format_pct(kpis["engagement_rate"]))
    with col7:
        st.metric("D7 Retention", format_pct(kpis["retention_d7"]))
    with col8:
        st.metric("Churn Rate", format_pct(kpis["churn_rate"]))

    st.markdown('<div class="section-title">Active Users Trend</div>', unsafe_allow_html=True)
    daily = get_daily_metrics(90)
    if not daily.empty:
        fig = px.line(daily, x="metric_date", y=["dau", "wau", "mau"],
                      title="DAU / WAU / MAU Trend (90 Days)",
                      labels={"value": "Users", "metric_date": "Date", "variable": "Metric"})
        fig = plotly_theme(fig, height=400)
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-title">Feature Adoption</div>', unsafe_allow_html=True)
        features = get_feature_adoption(30)
        if not features.empty:
            fig = create_bar_chart(
                features.head(10), "feature", "adoption_rate",
                "Feature Adoption Rate (30D)",
            )
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Reels Watch Time</div>', unsafe_allow_html=True)
        if not daily.empty:
            fig = create_line_chart(
                daily, "metric_date", "reels_watch_time_hours",
                "Daily Reels Watch Time (Hours)",
            )
            st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="section-title">Geographic Breakdown</div>', unsafe_allow_html=True)
        geo = get_geographic_breakdown(30)
        if not geo.empty:
            fig = create_bar_chart(
                geo.head(10), "country", "active_users",
                "Active Users by Country (Top 10)",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.markdown('<div class="section-title">Device Breakdown</div>', unsafe_allow_html=True)
        devices = get_device_breakdown(30)
        if not devices.empty:
            fig = create_pie_chart(devices, "device", "active_users", "Users by Device")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-title">Creator Engagement</div>', unsafe_allow_html=True)
    creators = get_creator_engagement(30)
    if not creators.empty:
        creators["type"] = creators["is_creator"].map({True: "Creators", False: "Consumers"})
        fig = create_bar_chart(creators, "type", "total_events", "Creator vs Consumer Activity")
        st.plotly_chart(fig, use_container_width=True)

    # Engagement & Retention trends
    col_e, col_f = st.columns(2)
    with col_e:
        if not daily.empty:
            fig = create_line_chart(daily, "metric_date", "engagement_rate", "Engagement Rate Trend")
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)
    with col_f:
        if not daily.empty:
            fig = create_line_chart(daily, "metric_date", "retention_d7", "D7 Retention Trend")
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)
