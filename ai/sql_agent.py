"""SQL generation and execution for AI analyst."""

import re

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:
    from langchain.schema import HumanMessage, SystemMessage

from langchain_openai import ChatOpenAI

from ai.prompts import SQL_GENERATION_PROMPT
from config import OPENAI_API_KEY, OPENAI_MODEL
from database.connection import read_sql
from utils.sql_compat import date_filter


def generate_sql(question: str) -> str:
    """Generate SQL from natural language question."""
    if not OPENAI_API_KEY:
        return _fallback_sql(question)

    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0, api_key=OPENAI_API_KEY)
    messages = [
        SystemMessage(content=SQL_GENERATION_PROMPT),
        HumanMessage(content=question),
    ]
    response = llm.invoke(messages)
    sql = response.content.strip()
    sql = re.sub(r"```sql?\n?", "", sql)
    sql = re.sub(r"```", "", sql).strip()
    return sql


def execute_sql(sql: str):
    """Safely execute generated SQL (SELECT only)."""
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        return None, "Only SELECT queries are allowed"
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "TRUNCATE", "CREATE"]
    if any(kw in sql_upper for kw in forbidden):
        return None, "Query contains forbidden operations"

    try:
        df = read_sql(sql)
        return df, None
    except Exception as e:
        return None, str(e)


def _fallback_sql(question: str) -> str:
    """Rule-based SQL fallback when OpenAI unavailable."""
    q = question.lower()
    if "dau" in q and ("decrease" in q or "drop" in q or "why" in q):
        return """
            SELECT metric_date, dau, wau, mau, engagement_rate, new_users
            FROM daily_metrics
            ORDER BY metric_date DESC LIMIT 30
        """
    if "feature" in q and "adoption" in q:
        return """
            SELECT feature, COUNT(DISTINCT user_id) AS users,
                   SUM(usage_count) AS total_usage
            FROM feature_usage
            GROUP BY feature ORDER BY users DESC
        """
    if "experiment" in q or "a/b" in q:
        return """
            SELECT ex.name, ea.variant, COUNT(*) AS n,
                   AVG(ea.converted::float) AS conversion_rate,
                   AVG(ea.engagement_score) AS avg_engagement
            FROM experiments ex
            JOIN experiment_assignments ea ON ex.experiment_id = ea.experiment_id
            GROUP BY ex.name, ea.variant ORDER BY ex.name, ea.variant
        """
    if "churn" in q or "risk" in q:
        return """
            SELECT segment, country, COUNT(*) AS users
            FROM users WHERE segment IN ('At Risk', 'Casual', 'Lurker')
            GROUP BY segment, country ORDER BY users DESC LIMIT 20
        """
    if "country" in q or "geographic" in q:
        return f"""
            SELECT u.country, COUNT(DISTINCT e.user_id) AS active_users
            FROM user_events e JOIN users u ON e.user_id = u.user_id
            WHERE {date_filter("e.event_timestamp", 30)}
            GROUP BY u.country ORDER BY active_users DESC LIMIT 15
        """
    return """
        SELECT metric_date, dau, wau, mau, engagement_rate, churn_rate, retention_d7
        FROM daily_metrics ORDER BY metric_date DESC LIMIT 14
    """
