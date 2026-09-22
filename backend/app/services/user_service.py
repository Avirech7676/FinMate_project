from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import models
import schemas
import auth
import gamification
from app.repositories.user_repo import UserRepository

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(self, user_in: schemas.UserCreate) -> models.User:
        # Check duplicate
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Password validation
        if len(user_in.password) < 6:
            raise HTTPException(status_code=422, detail="Password too short")

        currency = "USD"
        currency_symbol = "$"
        email_lower = user_in.email.strip().lower()
        if email_lower.endswith(('.in', '.co.in')):
            currency = "INR"
            currency_symbol = "₹"
        elif email_lower.endswith(('.uk', '.co.uk')):
            currency = "GBP"
            currency_symbol = "£"
        elif email_lower.endswith(('.eu', '.de', '.fr', '.it', '.es')):
            currency = "EUR"
            currency_symbol = "€"

        hashed_pw = auth.get_password_hash(user_in.password)
        new_user = models.User(
            email=email_lower,
            password_hash=hashed_pw,
            full_name=user_in.full_name,
            currency=currency,
            currency_symbol=currency_symbol
        )
        created_user = self.user_repo.create(new_user)
        
        # Profile
        new_profile = models.FinancialProfile(user_id=created_user.user_id)
        self.db.add(new_profile)
        
        # Stats
        new_stats = models.UserStats(user_id=created_user.user_id)
        self.db.add(new_stats)
        self.db.commit()

        # Gamification welcome
        gamification.check_and_award_achievement(self.db, created_user, "first_transaction")
        gamification.create_notification(
            self.db,
            created_user.user_id,
            "Welcome to FinMate!",
            "Start by importing transactions or scanning receipts to get insights.",
            "info"
        )
        return created_user

    def authenticate_user(self, username: str, password: str) -> models.User:
        user = self.user_repo.get_by_email(username)
        if not user or not auth.verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
