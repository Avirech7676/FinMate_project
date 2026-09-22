from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    preferences = Column(String, default="{}") # JSON string
    currency = Column(String, default="USD") # USD, INR, EUR, GBP, etc.
    currency_symbol = Column(String, default="$")

    @property
    def monthly_budget(self) -> float:
        try:
            import json
            prefs = json.loads(self.preferences or "{}")
            return float(prefs.get("monthly_budget", 0.0))
        except Exception:
            return 0.0

    profile = relationship("FinancialProfile", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    goals = relationship("BudgetGoal", back_populates="user")
    stats = relationship("UserStats", back_populates="user", uselist=False)
    achievements = relationship("Achievement", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    subscription_decisions = relationship("SubscriptionDecision", back_populates="user")

class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    monthly_income = Column(Float, default=0.0)
    employment_type = Column(String)
    risk_tolerance = Column(String)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile")

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
    )

    transaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)
    amount = Column(Float)
    category = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    description = Column(String)
    source = Column(String) # manual/import/linked/receipt

    user = relationship("User", back_populates="transactions")

class BudgetGoal(Base):
    __tablename__ = "budget_goals"
    __table_args__ = (
        Index("ix_budget_goals_user", "user_id"),
    )

    goal_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    goal_type = Column(String) # savings/debt_repayment/investment
    target_amount = Column(Float)
    deadline = Column(DateTime)
    current_progress = Column(Float, default=0.0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="goals")

class UserStats(Base):
    __tablename__ = "user_stats"

    stat_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    total_xp = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)  # days under budget
    longest_streak = Column(Integer, default=0)
    total_transactions = Column(Integer, default=0)
    total_spending = Column(Float, default=0.0)
    last_streak_date = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="stats")

class Achievement(Base):
    __tablename__ = "achievements"

    achievement_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    achievement_type = Column(String)  # first_transaction, week_streak_7, big_saver, etc
    title = Column(String)
    description = Column(String)
    icon = Column(String)  # emoji or icon name
    xp_reward = Column(Integer, default=0)
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="achievements")

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    title = Column(String)
    message = Column(String)
    notification_type = Column(String)  # achievement, budget_alert, anomaly, reminder
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class ReceiptPending(Base):
    __tablename__ = "receipts_pending"

    receipt_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    extracted_data = Column(String)  # JSON string
    receipt_image_path = Column(String)
    status = Column(String, default="pending")  # pending/confirmed/rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class SubscriptionDecision(Base):
    """
    User decision on a detected recurring/subscription-like merchant.
    candidate_id is a stable identifier computed by backend detection.
    """
    __tablename__ = "subscription_decisions"

    decision_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), index=True)

    candidate_id = Column(String, index=True)  # e.g., hash from merchant key
    merchant = Column(String)
    avg_amount = Column(Float, default=0.0)
    interval_days = Column(Integer, default=30)
    occurrences = Column(Integer, default=0)
    last_seen_at = Column(DateTime)

    action = Column(String)  # keep/cancel/negotiate
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="subscription_decisions")
