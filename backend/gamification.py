"""
Gamification utilities for FinMate
Handles XP, streaks, and achievements
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, Tuple
import models

# Achievement definitions
ACHIEVEMENTS = {
    "first_transaction": {
        "title": "Getting Started",
        "description": "Added your first transaction",
        "icon": "🎉",
        "xp": 10
    },
    "week_streak_7": {
        "title": "Week Warrior",
        "description": "Stayed under budget for 7 days",
        "icon": "🔥",
        "xp": 50
    },
    "week_streak_30": {
        "title": "Monthly Master",
        "description": "Stayed under budget for 30 days",
        "icon": "👑",
        "xp": 200
    },
    "big_spender": {
        "title": "Big Spender",
        "description": "Added a transaction over $100",
        "icon": "💰",
        "xp": 15
    },
    "categoric_master": {
        "title": "Categorization Expert",
        "description": "Categorized 50 transactions",
        "icon": "📊",
        "xp": 30
    },
    "budget_crushed": {
        "title": "Budget Crusher",
        "description": "Stayed 50% under budget",
        "icon": "💪",
        "xp": 100
    },
    "receipt_scanner": {
        "title": "Receipt Master",
        "description": "Scanned 5 receipts",
        "icon": "📸",
        "xp": 25
    }
}

def check_and_award_achievement(db: Session, user: models.User, achievement_type: str) -> Optional[models.Achievement]:
    """Check if achievement should be awarded and create it"""
    
    # Check if already unlocked
    existing = db.query(models.Achievement).filter(
        models.Achievement.user_id == user.user_id,
        models.Achievement.achievement_type == achievement_type
    ).first()
    
    if existing:
        return None
    
    if achievement_type not in ACHIEVEMENTS:
        return None
    
    achievement_data = ACHIEVEMENTS[achievement_type]
    achievement = models.Achievement(
        user_id=user.user_id,
        achievement_type=achievement_type,
        title=achievement_data["title"],
        description=achievement_data["description"],
        icon=achievement_data["icon"],
        xp_reward=achievement_data["xp"]
    )
    
    db.add(achievement)
    
    # Add XP to user stats
    if not user.stats:
        user.stats = models.UserStats(user_id=user.user_id)
        db.add(user.stats)
    
    user.stats.total_xp += achievement_data["xp"]
    
    db.commit()
    db.refresh(achievement)
    return achievement

def update_streak(db: Session, user: models.User, under_budget: bool) -> Tuple[int, int]:
    """Update user streak. Returns (current_streak, longest_streak)"""
    
    if not user.stats:
        user.stats = models.UserStats(user_id=user.user_id)
        db.add(user.stats)
    
    today = datetime.utcnow().date()
    
    if user.stats.last_streak_date:
        last_streak_date = user.stats.last_streak_date.date() if isinstance(user.stats.last_streak_date, datetime) else user.stats.last_streak_date
    else:
        last_streak_date = None
    
    # If user was under budget today, increment streak
    if under_budget:
        if last_streak_date == today:
            # Already updated today, don't increment again
            pass
        elif last_streak_date == today - timedelta(days=1):
            # Consecutive day, increment
            user.stats.current_streak += 1
        else:
            # Restart streak
            user.stats.current_streak = 1
        
        user.stats.last_streak_date = datetime.utcnow()
        
        # Update longest streak
        if user.stats.current_streak > user.stats.longest_streak:
            user.stats.longest_streak = user.stats.current_streak
    else:
        # User went over budget, reset streak
        if last_streak_date != today:
            user.stats.current_streak = 0
    
    db.commit()
    return user.stats.current_streak, user.stats.longest_streak

def create_notification(db: Session, user_id: int, title: str, message: str, notification_type: str = "info"):
    """Create a notification for the user"""
    notification = models.Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification

def check_streak_milestones(db: Session, user: models.User) -> Optional[models.Achievement]:
    """Check if user hit a streak milestone and award achievement"""
    if not user.stats:
        return None
    
    if user.stats.current_streak == 7:
        return check_and_award_achievement(db, user, "week_streak_7")
    elif user.stats.current_streak == 30:
        return check_and_award_achievement(db, user, "week_streak_30")
    
    return None
