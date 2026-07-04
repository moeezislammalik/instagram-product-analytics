"""SQLAlchemy database models for Instagram Product Analytics."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    country = Column(String(64), nullable=False, index=True)
    device = Column(String(32), nullable=False, index=True)
    acquisition_channel = Column(String(64), nullable=False)
    is_creator = Column(Boolean, default=False, index=True)
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    segment = Column(String(32), default="Regular")

    sessions = relationship("Session", back_populates="user")
    events = relationship("UserEvent", back_populates="user")
    feature_usage = relationship("FeatureUsage", back_populates="user")
    experiment_assignments = relationship("ExperimentAssignment", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=False)
    duration_sec = Column(Float, nullable=False)
    device = Column(String(32), nullable=False)
    country = Column(String(64), nullable=False)

    user = relationship("User", back_populates="sessions")


class UserEvent(Base):
    __tablename__ = "user_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.session_id"), nullable=True)
    event_type = Column(String(32), nullable=False, index=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    feature = Column(String(64), nullable=True, index=True)
    content_type = Column(String(32), nullable=True)
    content_id = Column(Integer, nullable=True)
    country = Column(String(64), nullable=True)
    device = Column(String(32), nullable=True)
    value = Column(Float, nullable=True)

    user = relationship("User", back_populates="events")

    __table_args__ = (
        Index("ix_events_user_timestamp", "user_id", "event_timestamp"),
        Index("ix_events_type_timestamp", "event_type", "event_timestamp"),
    )


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    content_type = Column(String(32), default="post")
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    save_count = Column(Integer, default=0)


class Reel(Base):
    __tablename__ = "reels"

    reel_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    duration_sec = Column(Float, default=30.0)
    watch_time_sec = Column(Float, default=0.0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)


class Story(Base):
    __tablename__ = "stories"

    story_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, index=True)
    view_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)
    tap_forward_count = Column(Integer, default=0)


class Experiment(Base):
    __tablename__ = "experiments"

    experiment_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    status = Column(String(32), default="running")
    primary_metric = Column(String(64), default="engagement_rate")


class ExperimentAssignment(Base):
    __tablename__ = "experiment_assignments"

    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey("experiments.experiment_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    variant = Column(String(32), nullable=False, index=True)
    assigned_at = Column(DateTime, nullable=False)
    converted = Column(Boolean, default=False)
    conversion_value = Column(Float, default=0.0)
    sessions_count = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)

    user = relationship("User", back_populates="experiment_assignments")
    experiment = relationship("Experiment")

    __table_args__ = (
        Index("ix_exp_user_variant", "experiment_id", "user_id", "variant"),
    )


class FeatureUsage(Base):
    __tablename__ = "feature_usage"

    usage_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    feature = Column(String(64), nullable=False, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    usage_count = Column(Integer, default=1)
    time_spent_sec = Column(Float, default=0.0)

    user = relationship("User", back_populates="feature_usage")

    __table_args__ = (
        Index("ix_feature_user_date", "user_id", "feature", "usage_date"),
    )


class DailyMetric(Base):
    """Pre-aggregated daily metrics for fast dashboard queries."""

    __tablename__ = "daily_metrics"

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    metric_date = Column(Date, nullable=False, unique=True, index=True)
    dau = Column(Integer, default=0)
    wau = Column(Integer, default=0)
    mau = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    sessions = Column(Integer, default=0)
    avg_session_length = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    reels_watch_time_hours = Column(Float, default=0.0)
    churn_rate = Column(Float, default=0.0)
    retention_d7 = Column(Float, default=0.0)
