"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'instagram_analytics.db'}",
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Synthetic data generation defaults
NUM_USERS = int(os.getenv("NUM_USERS", "50000"))
NUM_EVENTS = int(os.getenv("NUM_EVENTS", "1000000"))
DATA_START_DATE = os.getenv("DATA_START_DATE", "2024-01-01")
DATA_END_DATE = os.getenv("DATA_END_DATE", "2025-06-30")

# Analytics constants
COHORT_PERIODS = [1, 7, 14, 30, 60, 90]
FUNNEL_STEPS = ["app_open", "feed_view", "content_engagement", "share", "follow"]
NORTH_STAR_METRIC = "weekly_engaged_users"
