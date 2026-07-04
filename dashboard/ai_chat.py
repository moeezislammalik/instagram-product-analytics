"""AI Product Analyst chat interface."""

import streamlit as st

from ai.analyst import ProductAnalyst
from config import OPENAI_API_KEY
from dashboard.styles import render_header


SAMPLE_QUESTIONS = [
    "Why did DAU decrease?",
    "Which feature has the highest adoption?",
    "Which experiment increased engagement?",
    "Summarize this dashboard.",
    "Recommend product improvements.",
    "Which user segments are at risk of churn?",
    "What is our DAU/MAU stickiness trend?",
    "Which countries drive the most engagement?",
]


def render():
    render_header(
        "AI Product Analyst",
        "Natural language analytics powered by LangChain & OpenAI",
    )

    if not OPENAI_API_KEY:
        st.info(
            "OpenAI API key not configured. The analyst will use rule-based fallback responses. "
            "Set `OPENAI_API_KEY` in your `.env` file for full AI capabilities."
        )

    if "analyst" not in st.session_state:
        st.session_state.analyst = ProductAnalyst()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    col1, col2 = st.columns([3, 1])

    with col2:
        st.subheader("Quick Questions")
        for q in SAMPLE_QUESTIONS:
            if st.button(q, key=f"q_{q}", use_container_width=True):
                st.session_state.pending_question = q

    with col1:
        st.subheader("Chat with Product Analyst")

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="ai-chat-user"><strong>You:</strong> {msg["content"]}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-chat-assistant"><strong>Analyst:</strong> {msg["content"]}</div>',
                            unsafe_allow_html=True)
                if msg.get("chart"):
                    st.plotly_chart(msg["chart"], use_container_width=True)
                if msg.get("sql"):
                    with st.expander("SQL Query"):
                        st.code(msg["sql"], language="sql")
                if msg.get("data") is not None and not msg["data"].empty:
                    with st.expander("Data Results"):
                        st.dataframe(msg["data"], use_container_width=True, hide_index=True)

        question = st.chat_input("Ask a product analytics question...")
        pending = st.session_state.pop("pending_question", None)
        active_question = pending or question

        if active_question:
            with st.spinner("Analyzing..."):
                result = st.session_state.analyst.ask(active_question)

            st.session_state.chat_history.append({"role": "user", "content": active_question})
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result["answer"],
                "sql": result.get("sql"),
                "data": result.get("data"),
                "chart": result.get("chart"),
            })

            if result.get("recommendations"):
                st.markdown("### Recommendations")
                st.markdown(result["recommendations"])

            if result.get("sql_error"):
                st.warning(f"SQL note: {result['sql_error']}")

            st.rerun()

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.session_state.analyst = ProductAnalyst()
            st.rerun()

        if st.button("Generate Executive Summary"):
            with st.spinner("Generating summary..."):
                summary = st.session_state.analyst.summarize_dashboard()
                st.session_state.chat_history.append({"role": "user", "content": "Summarize this dashboard."})
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": summary["answer"],
                    "chart": summary.get("chart"),
                })
                st.rerun()
