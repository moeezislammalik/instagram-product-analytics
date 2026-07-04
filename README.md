# Instagram Product Analytics & AI Insights Platform

A production-quality full-stack Product Analytics platform inspired by Meta's Instagram Product Analytics team. Built for Product Data Scientists to monitor KPIs, run experiments, predict user behavior, and get AI-powered insights.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue)

## Overview

This platform simulates the internal analytics tools used by Meta Product Data Scientists at Instagram. It includes:

- **Executive Dashboard** — DAU/WAU/MAU, stickiness, engagement, retention, churn, geographic & device breakdowns
- **Product Analytics** — Growth trends, cohort retention, funnel analysis, segmentation, North Star metrics
- **Experimentation Center** — A/B test analysis with statistical significance, lift, confidence intervals
- **Predictive Analytics** — Churn prediction, engagement forecasting, Prophet time-series, SHAP explainability
- **AI Product Analyst** — LangChain + OpenAI chatbot that generates SQL, creates charts, and provides recommendations

## Screenshots

### Executive Dashboard
![Executive Dashboard](docs/screenshots/01-executive-dashboard.png)

Real-time KPIs including DAU/WAU/MAU, stickiness, engagement rate, retention, churn, feature adoption, geographic and device breakdowns, and Reels watch time.

### Product Analytics
![Product Analytics](docs/screenshots/02-product-analytics.png)

Growth trends, user segmentation, cohort retention heatmaps, conversion funnels, and North Star metric tracking.

### Experimentation Center
![Experimentation Center](docs/screenshots/03-experimentation-center.png)

A/B test analysis with conversion rates by variant, statistical significance testing, p-values, confidence intervals, lift calculations, and ship recommendations.

### Predictive Analytics
![Predictive Analytics](docs/screenshots/04-predictive-analytics.png)

Churn prediction with risk segmentation, engagement forecasting, Prophet-based DAU/retention projections, and SHAP feature importance.

### AI Product Analyst
![AI Product Analyst](docs/screenshots/05-ai-product-analyst.png)

Natural language analytics chatbot powered by LangChain and OpenAI — ask questions, generate SQL, view charts, and get executive recommendations.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit, Plotly |
| Backend | Python, SQLAlchemy |
| Database | PostgreSQL (SQLite fallback for local dev) |
| Analytics | Pandas, NumPy, SciPy |
| ML | Scikit-learn, Prophet, SHAP |
| AI | LangChain, OpenAI API |

## Quick Start

### 1. Clone and install

```bash
cd instagram-product-analytics
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

For **PostgreSQL**:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/instagram_analytics
```

For **local dev without PostgreSQL** (default):
```
DATABASE_URL=sqlite:///data/instagram_analytics.db
```

For **AI features**, add your OpenAI key:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. Seed the database

Generates 50,000 users and 1,000,000 events with realistic patterns:

```bash
python -m database.seed --force
```

Or use the **"Initialize / Seed Database"** button in the Streamlit sidebar.

### 4. Run the app

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501)

## Project Structure

```
instagram-product-analytics/
├── app.py                  # Main Streamlit entry point
├── config.py               # Application configuration
├── requirements.txt
├── database/
│   ├── models.py           # SQLAlchemy ORM models
│   ├── connection.py       # DB connection & session management
│   └── seed.py             # Database seeding script
├── analytics/
│   ├── metrics.py          # Executive & product KPIs
│   ├── cohorts.py          # Cohort retention analysis
│   ├── funnels.py          # Conversion funnel analysis
│   ├── experiments.py      # A/B test statistical testing
│   └── segmentation.py     # User segmentation & RFM
├── machine_learning/
│   ├── churn_model.py      # Gradient Boosting churn classifier
│   ├── engagement_model.py # Random Forest engagement regressor
│   ├── forecasting.py      # Prophet time-series forecasting
│   └── shap_analysis.py    # SHAP feature importance
├── ai/
│   ├── analyst.py          # LangChain Product Analyst chatbot
│   ├── sql_agent.py        # Natural language → SQL generation
│   └── prompts.py          # System prompts & templates
├── dashboard/
│   ├── styles.py           # Meta-inspired UI theme
│   ├── executive.py        # Executive Dashboard page
│   ├── product_analytics.py
│   ├── experimentation.py
│   ├── predictive.py
│   └── ai_chat.py
└── utils/
    ├── data_generator.py   # Synthetic Instagram data generator
    ├── constants.py        # Shared constants & enums
    ├── helpers.py          # Formatting & utility functions
    └── sql_compat.py       # PostgreSQL/SQLite SQL compatibility
```

## Analytics Methodology

### Active User Metrics

| Metric | Definition |
|--------|-----------|
| **DAU** | Distinct users with ≥1 event on a given day |
| **WAU** | Distinct users active in trailing 7 days |
| **MAU** | Distinct users active in trailing 30 days |
| **Stickiness** | DAU / MAU — measures daily engagement depth |

### Engagement & Retention

- **Engagement Rate**: Users performing like/comment/share/save actions / DAU
- **D7 Retention**: % of cohort users active 7 days after signup
- **Churn Rate**: Users inactive for 30+ days / total user base

### Cohort Analysis

Weekly signup cohorts tracked across 12 periods. Retention matrix shows % of each cohort returning in subsequent weeks, enabling identification of onboarding quality changes.

### Funnel Analysis

5-step conversion funnel: App Open → Feed View → Content Engagement → Share → Follow. Step-over-step and segment-level conversion rates identify drop-off points.

### North Star Metric

**Weekly Engaged Users (WEU)**: 7-day rolling average of users performing meaningful engagement actions (views, likes, comments, shares). Chosen as the primary product health indicator.

## Experimentation Framework

### A/B Test Analysis

1. **Randomization**: Users assigned to control/treatment variants
2. **Primary Metric**: Conversion rate (binary) or engagement score (continuous)
3. **Statistical Test**: Two-sample Welch's t-test (unequal variances)
4. **Decision Criteria**:
   - p-value < 0.05 → statistically significant
   - Positive lift → recommend ship
   - Negative lift → do not ship, investigate
   - Inconclusive → continue experiment or increase power

### Key Outputs

- Conversion rate by variant
- Lift (% change vs control)
- p-value and 95% confidence interval
- Winner recommendation with ship/no-ship guidance

### Upload Custom Experiments

Upload CSV with `variant` and `converted` columns for ad-hoc analysis.

## Machine Learning Models

### Churn Prediction (Gradient Boosting Classifier)

**Label**: User inactive for 30+ days  
**Features**: recency, frequency, active days, session count, reel views, engagements, follower/following counts, account age, engagement rate  
**Evaluation**: ROC-AUC score on 80/20 train/test split  
**Output**: Churn probability per user with Low/Medium/High risk tiers

### Engagement Prediction (Random Forest Regressor)

**Target**: Composite engagement score (weighted actions / active days)  
**Features**: total events, active days, reel/story views, engagements, avg reel time  
**Evaluation**: R² and MAE

### Time-Series Forecasting (Prophet)

- DAU forecasting with weekly/yearly seasonality
- Engagement rate and D7 retention projections
- 95% confidence intervals for all forecasts

### SHAP Explainability

TreeSHAP values explain individual churn predictions. Features ranked by mean |SHAP| value reveal the strongest churn drivers (typically recency and engagement frequency).

## AI Architecture

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐
│  LangChain   │────▶│  SQL Agent   │──▶ PostgreSQL
│  ChatOpenAI  │     │  (NL → SQL)  │
└─────────────┘     └──────────────┘
     │                      │
     ▼                      ▼
┌─────────────┐     ┌──────────────┐
│  Context     │     │  Query Data   │
│  (Live KPIs) │     │  (Pandas)     │
└─────────────┘     └──────────────┘
     │                      │
     ▼                      ▼
┌─────────────────────────────────┐
│  Response: Analysis + Chart +   │
│  SQL + Recommendations          │
└─────────────────────────────────┘
```

The AI Product Analyst:
1. Gathers live KPI context from the database
2. Generates SQL from natural language (OpenAI or rule-based fallback)
3. Executes read-only SELECT queries
4. Auto-generates Plotly charts from results
5. Provides executive-level narrative with actionable recommendations

### Example Questions

- "Why did DAU decrease?"
- "Which feature has the highest adoption?"
- "Which experiment increased engagement?"
- "Summarize this dashboard."
- "Recommend product improvements."
- "Which user segments are at risk of churn?"

## Synthetic Dataset

The data generator creates realistic Instagram-like data:

| Entity | Count | Details |
|--------|-------|---------|
| Users | 50,000 | 20 countries, 3 devices, 8 acquisition channels, 7 segments |
| Events | 1,000,000 | 15 event types with realistic frequency weights |
| Sessions | 200,000 | Exponential duration distribution (30s–3600s) |
| Posts | 80,000 | Likes, comments, shares, saves |
| Reels | 60,000 | Watch time, views, engagement |
| Stories | 100,000 | Views, replies, tap-forwards |
| Experiments | 9 | Control + 2 treatment variants each |
| Feature Usage | 150,000 | 10 Instagram features tracked daily |

Data spans January 2024 – June 2025 with seasonality patterns and treatment lift baked into experiments.

## PostgreSQL Setup

```bash
# Create database
createdb instagram_analytics

# Set connection string
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/instagram_analytics

# Seed
python -m database.seed --force
```

## License

Internal use — demonstration project for Product Analytics portfolio.
