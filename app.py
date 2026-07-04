"""
Instagram Product Analytics & AI Insights Platform
Main Streamlit application entry point.
"""

import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import streamlit as st

from config import DATABASE_URL, NUM_EVENTS, NUM_USERS
from dashboard.styles import apply_custom_css
from database.connection import check_connection, init_db

st.set_page_config(
    page_title="Instagram Product Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_custom_css()


def sidebar():
    """Render sidebar navigation."""
    st.sidebar.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <span style="font-size:2rem;">📸</span>
        <h2 style="margin:0.5rem 0 0 0; font-size:1.1rem; color:#262626;">
            Instagram Analytics
        </h2>
        <p style="color:#8E8E8E; font-size:0.75rem; margin:0;">Product Data Science Platform</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    pages = {
        "Executive Dashboard": "executive",
        "Product Analytics": "product",
        "Experimentation Center": "experiments",
        "Predictive Analytics": "predictive",
        "AI Product Analyst": "ai_analyst",
    }

    selection = st.sidebar.radio("Navigation", list(pages.keys()), label_visibility="collapsed")

    st.sidebar.markdown("---")
    st.sidebar.markdown("##### Data Status")

    connected = check_connection()
    if connected:
        st.sidebar.success("Database connected")
    else:
        st.sidebar.error("Database disconnected")

    st.sidebar.caption(f"Target: {NUM_USERS:,} users, {NUM_EVENTS:,} events")
    st.sidebar.caption(f"DB: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")

    if st.sidebar.button("Initialize / Seed Database", use_container_width=True):
        with st.spinner("Creating tables and seeding data (this may take several minutes)..."):
            init_db()
            from database.connection import get_db_session
            from utils.data_generator import seed_database

            with get_db_session() as session:
                result = seed_database(session, force=True)
                if result.get("status") == "success":
                    st.sidebar.success(
                        f"Seeded {result['users']:,} users, {result['events']:,} events!"
                    )
                else:
                    st.sidebar.info(result.get("message", "Done"))

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<p style="color:#8E8E8E; font-size:0.7rem;">© 2025 Instagram Product Analytics<br>'
        "Internal Use Only — Meta Data Science</p>",
        unsafe_allow_html=True,
    )

    return pages[selection]


def main():
    page = sidebar()

    if page == "executive":
        from dashboard.executive import render
        render()
    elif page == "product":
        from dashboard.product_analytics import render
        render()
    elif page == "experiments":
        from dashboard.experimentation import render
        render()
    elif page == "predictive":
        from dashboard.predictive import render
        render()
    elif page == "ai_analyst":
        from dashboard.ai_chat import render
        render()


if __name__ == "__main__":
    main()
