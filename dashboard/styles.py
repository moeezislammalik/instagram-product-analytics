"""Meta-inspired dashboard styling and chart utilities."""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from utils.constants import META_COLORS


def apply_custom_css():
    """Apply Instagram/Meta-inspired custom CSS."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #405DE6 0%, #833AB4 50%, #C13584 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        color: white !important;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: rgba(255,255,255,0.85);
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
    }

    .metric-card {
        background: white;
        border: 1px solid #EFEFEF;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-label {
        color: #8E8E8E;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #262626;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0.2rem 0;
    }
    .metric-delta-positive { color: #00C853; font-size: 0.85rem; font-weight: 600; }
    .metric-delta-negative { color: #F44336; font-size: 0.85rem; font-weight: 600; }

    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #262626;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E1306C;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FAFAFA 0%, #F5F5F5 100%);
    }
    div[data-testid="stSidebar"] .stRadio label {
        font-weight: 500;
    }

    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #EFEFEF;
    }

    .ai-chat-user {
        background: #EFEFEF;
        padding: 0.8rem 1rem;
        border-radius: 12px 12px 12px 0;
        margin: 0.5rem 0;
    }
    .ai-chat-assistant {
        background: linear-gradient(135deg, #f8f0ff 0%, #fff0f5 100%);
        padding: 0.8rem 1rem;
        border-radius: 12px 12px 0 12px;
        margin: 0.5rem 0;
        border-left: 3px solid #E1306C;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = ""):
    """Render page header with gradient."""
    st.markdown(f"""
    <div class="main-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str = "", positive: bool = True):
    """Render a KPI metric card."""
    delta_class = "metric-delta-positive" if positive else "metric-delta-negative"
    delta_html = f'<div class="{delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def plotly_theme(fig, height: int = 400):
    """Apply consistent Plotly theme."""
    fig.update_layout(
        height=height,
        template="plotly_white",
        font=dict(family="Inter, sans-serif", size=12),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=20, t=50, b=40),
        colorway=[META_COLORS["primary"], META_COLORS["secondary"],
                  META_COLORS["gradient_start"], META_COLORS["blue"],
                  META_COLORS["success"], META_COLORS["warning"]],
    )
    return fig


def create_line_chart(df, x, y, title, color=META_COLORS["primary"]):
    """Create themed line chart."""
    fig = px.line(df, x=x, y=y, title=title, color_discrete_sequence=[color])
    return plotly_theme(fig)


def create_bar_chart(df, x, y, title, orientation="v"):
    """Create themed bar chart."""
    fig = px.bar(df, x=x, y=y, title=title, orientation=orientation,
                 color_discrete_sequence=[META_COLORS["primary"]])
    return plotly_theme(fig)


def create_pie_chart(df, names, values, title):
    """Create themed pie chart."""
    fig = px.pie(df, names=names, values=values, title=title,
                 color_discrete_sequence=px.colors.sequential.RdPu)
    return plotly_theme(fig, height=350)


def create_heatmap(df, title):
    """Create retention heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=df.columns.tolist(),
        y=df.index.tolist(),
        colorscale="RdPu",
        text=[[f"{v:.0%}" for v in row] for row in df.values],
        texttemplate="%{text}",
        textfont={"size": 10},
    ))
    fig.update_layout(title=title)
    return plotly_theme(fig, height=500)


def create_funnel_chart(df, title="Conversion Funnel"):
    """Create funnel chart."""
    fig = go.Figure(go.Funnel(
        y=df["step"],
        x=df["users"],
        textinfo="value+percent initial",
        marker=dict(color=[META_COLORS["gradient_start"], META_COLORS["secondary"],
                           META_COLORS["primary"], META_COLORS["gradient_end"],
                           META_COLORS["blue"]]),
    ))
    fig.update_layout(title=title)
    return plotly_theme(fig, height=450)
