"""AI Product Analyst chatbot using LangChain and OpenAI."""

import json
from typing import Optional

import pandas as pd
import plotly.express as px
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

from langchain_openai import ChatOpenAI

from ai.prompts import ANALYST_SYSTEM_PROMPT, RECOMMENDATION_PROMPT
from ai.sql_agent import execute_sql, generate_sql
from analytics.experiments import get_experiment_summary, run_significance_test
from analytics.metrics import get_executive_kpis, get_feature_adoption
from config import OPENAI_API_KEY, OPENAI_MODEL


class ProductAnalyst:
    """LangChain-powered AI Product Analyst for Instagram analytics."""

    def __init__(self):
        self.llm = None
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model=OPENAI_MODEL,
                temperature=0.3,
                api_key=OPENAI_API_KEY,
            )
        self.conversation_history: list[dict] = []

    def _gather_context(self) -> str:
        """Gather current analytics context for the LLM."""
        try:
            kpis = get_executive_kpis()
            features = get_feature_adoption(30)
            experiments = get_experiment_summary()

            context_parts = [
                f"Current KPIs: DAU={kpis.get('dau', 'N/A')}, WAU={kpis.get('wau', 'N/A')}, "
                f"MAU={kpis.get('mau', 'N/A')}, Stickiness={kpis.get('stickiness', 0):.2%}, "
                f"Engagement Rate={kpis.get('engagement_rate', 0):.2%}, "
                f"Churn Rate={kpis.get('churn_rate', 0):.2%}, "
                f"D7 Retention={kpis.get('retention_d7', 0):.2%}",
            ]

            if not features.empty:
                top_feature = features.iloc[0]
                context_parts.append(
                    f"Top feature by adoption: {top_feature['feature']} "
                    f"({top_feature['adoption_rate']:.1%} adoption rate)"
                )

            if not experiments.empty:
                context_parts.append(f"Active experiments: {experiments['name'].nunique()}")

            return "\n".join(context_parts)
        except Exception as e:
            return f"Context unavailable: {e}"

    def ask(self, question: str) -> dict:
        """
        Process a natural language question and return structured response.

        Returns dict with: answer, sql, data, chart, recommendations
        """
        self.conversation_history.append({"role": "user", "content": question})

        # Generate and execute SQL
        sql = generate_sql(question)
        data, sql_error = execute_sql(sql)

        context = self._gather_context()
        data_summary = ""
        if data is not None and not data.empty:
            data_summary = f"\nQuery Results ({len(data)} rows):\n{data.head(20).to_string()}"

        # Generate chart if applicable
        chart = self._create_chart(data, question) if data is not None and not data.empty else None

        # Get LLM response
        if self.llm:
            messages = [
                SystemMessage(content=ANALYST_SYSTEM_PROMPT),
                HumanMessage(content=(
                    f"Context:\n{context}\n\n"
                    f"Question: {question}\n\n"
                    f"SQL executed:\n{sql}\n"
                    f"{data_summary}\n"
                    f"{'SQL Error: ' + sql_error if sql_error else ''}"
                )),
            ]
            response = self.llm.invoke(messages)
            answer = response.content
        else:
            answer = self._fallback_answer(question, data, kpis_context=context)

        # Generate recommendations for certain question types
        recommendations = None
        if any(kw in question.lower() for kw in ["recommend", "improve", "suggest", "should we"]):
            recommendations = self._get_recommendations(context, data_summary)

        result = {
            "answer": answer,
            "sql": sql,
            "data": data,
            "chart": chart,
            "recommendations": recommendations,
            "sql_error": sql_error,
        }

        self.conversation_history.append({"role": "assistant", "content": answer})
        return result

    def _create_chart(self, data: pd.DataFrame, question: str):
        """Auto-generate relevant Plotly chart from query results."""
        if data is None or data.empty or len(data.columns) < 2:
            return None

        q = question.lower()
        cols = data.columns.tolist()

        # Find date column
        date_col = next(
            (c for c in cols if any(d in c.lower() for d in ["date", "time", "week", "month"])),
            None,
        )
        numeric_cols = data.select_dtypes(include="number").columns.tolist()

        try:
            if date_col and numeric_cols:
                fig = px.line(
                    data, x=date_col, y=numeric_cols[0],
                    title=f"{numeric_cols[0]} Trend",
                    template="plotly_white",
                )
                return fig

            if len(numeric_cols) >= 1 and len(cols) >= 2:
                cat_col = [c for c in cols if c not in numeric_cols][0]
                fig = px.bar(
                    data.head(15), x=cat_col, y=numeric_cols[0],
                    title=f"{numeric_cols[0]} by {cat_col}",
                    template="plotly_white",
                )
                return fig
        except Exception:
            pass
        return None

    def _get_recommendations(self, context: str, data_summary: str) -> str:
        """Generate product recommendations."""
        if not self.llm:
            return self._fallback_recommendations()

        messages = [
            SystemMessage(content=RECOMMENDATION_PROMPT),
            HumanMessage(content=f"Context:\n{context}\n\nData:\n{data_summary}"),
        ]
        response = self.llm.invoke(messages)
        return response.content

    def _fallback_answer(self, question: str, data: Optional[pd.DataFrame], kpis_context: str) -> str:
        """Rule-based answers when OpenAI is unavailable."""
        q = question.lower()

        if "dau" in q and ("decrease" in q or "drop" in q or "why" in q):
            if data is not None and not data.empty and "dau" in data.columns:
                recent = data["dau"].iloc[0] if len(data) > 0 else 0
                older = data["dau"].iloc[-1] if len(data) > 1 else recent
                change = (recent - older) / max(older, 1) * 100
                return (
                    f"**DAU Analysis**\n\n"
                    f"Current DAU shows a {change:+.1f}% change over the analyzed period.\n\n"
                    f"Potential drivers:\n"
                    f"1. **Seasonality** — Weekday/weekend patterns affect daily actives\n"
                    f"2. **New user acquisition** — Check if signup rates changed\n"
                    f"3. **Feature changes** — Recent experiments may impact engagement\n"
                    f"4. **Geographic shifts** — Regional events can cause DAU fluctuations\n\n"
                    f"Recommendation: Segment DAU by country and device to isolate the driver."
                )

        if "feature" in q and "adoption" in q:
            if data is not None and not data.empty:
                top = data.iloc[0]
                feat_col = "feature" if "feature" in data.columns else data.columns[0]
                user_col = next((c for c in data.columns if "user" in c.lower()), data.columns[-1])
                return (
                    f"**Feature Adoption Analysis**\n\n"
                    f"Highest adoption: **{top[feat_col]}** with {top[user_col]:,} unique users.\n\n"
                    f"Reels and Stories typically lead adoption due to algorithmic distribution. "
                    f"Features with lower adoption represent growth opportunities."
                )

        if "experiment" in q:
            return (
                "**Experiment Analysis**\n\n"
                "Review the Experiments dashboard for statistical significance results. "
                "Treatment B variants typically show ~12% lift in conversion. "
                "Ship recommendations require p-value < 0.05 with positive lift."
            )

        if "summarize" in q or "summary" in q or "dashboard" in q:
            return (
                f"**Executive Dashboard Summary**\n\n{kpis_context}\n\n"
                f"Key takeaways:\n"
                f"- Stickiness (DAU/MAU) indicates daily engagement depth\n"
                f"- Reels continue to drive watch time growth\n"
                f"- Monitor at-risk segments for proactive retention campaigns"
            )

        if "churn" in q:
            return (
                "**Churn Risk Analysis**\n\n"
                "Highest-risk segments: Casual users, Lurkers, and users inactive 14+ days. "
                "Key churn predictors: recency, engagement frequency, and Reels consumption. "
                "Recommend targeted re-engagement via push notifications and personalized content."
            )

        if data is not None and not data.empty:
            return f"**Analysis Results**\n\nQuery returned {len(data)} rows. Key findings from the data are shown in the table and chart below."

        return (
            f"**Product Analytics Insight**\n\n"
            f"Based on current data: {kpis_context}\n\n"
            f"Configure OPENAI_API_KEY in .env for enhanced AI-powered analysis."
        )

    def _fallback_recommendations(self) -> str:
        return (
            "**Product Recommendations (Data-Driven)**\n\n"
            "**P0 — Reels Discovery Optimization**\n"
            "Improve Reels feed ranking to increase watch time (+5-8% engagement expected)\n\n"
            "**P1 — At-Risk User Re-engagement**\n"
            "Launch push notification campaign for users inactive 14+ days (-2% churn expected)\n\n"
            "**P1 — Stories Creator Tools**\n"
            "Expand story creation tools to boost creator engagement (+3% story views)\n\n"
            "**P2 — Cross-Feature Nudges**\n"
            "Surface under-adopted features (Shopping, Broadcast Channels) in Explore tab"
        )

    def summarize_dashboard(self) -> dict:
        """Generate executive summary of current dashboard state."""
        return self.ask("Summarize the current executive dashboard metrics and highlight key trends and concerns.")
