from pydantic import BaseModel, EmailStr, field_validator, Field
from typing import Optional, List, Literal
from datetime import datetime

CurrencyCode = Literal["USD", "INR", "EUR", "GBP"]

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    created_at: datetime
    currency: Optional[str] = "USD"
    currency_symbol: Optional[str] = "$"

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = "uncategorized"
    date: Optional[datetime] = None
    source: Optional[str] = "manual"

class TransactionOut(BaseModel):
    transaction_id: int
    amount: float
    category: str
    description: str
    date: datetime
    source: str

    class Config:
        from_attributes = True

class BudgetGoalCreate(BaseModel):
    goal_type: str = Field(..., pattern="^(savings|debt_repayment|investment)$")
    target_amount: float = Field(..., gt=0)
    deadline: datetime

class BudgetGoalUpdate(BaseModel):
    goal_type: Optional[str] = None
    target_amount: Optional[float] = None
    current_progress: Optional[float] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None

class BudgetGoalOut(BaseModel):
    goal_id: int
    goal_type: str
    target_amount: float
    current_progress: float
    deadline: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    roast_mode: bool = False
    
class ChatResponse(BaseModel):
    response: str
    action_type: Optional[str] = None
    action_payload: Optional[dict] = None

class UserStatsOut(BaseModel):
    total_xp: int
    current_streak: int
    longest_streak: int
    total_transactions: int
    total_spending: float

    class Config:
        from_attributes = True

class AchievementOut(BaseModel):
    achievement_id: int
    achievement_type: str
    title: str
    description: str
    icon: str
    xp_reward: int
    unlocked_at: datetime

    class Config:
        from_attributes = True

class NotificationOut(BaseModel):
    notification_id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ReceiptConfirmRequest(BaseModel):
    receipt_id: int
    confirmed: bool
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None


class SubscriptionCandidate(BaseModel):
    candidate_id: str
    merchant: str
    avg_amount: float
    estimated_monthly_cost: float
    occurrences: int
    interval_days: int
    last_seen_at: datetime
    confidence: float = Field(..., ge=0, le=1)


class SubscriptionDetectResponse(BaseModel):
    candidates: List[SubscriptionCandidate]
    estimated_monthly_leak: float
    estimated_monthly_savings: float


class SubscriptionActionRequest(BaseModel):
    action: Literal["keep", "cancel", "negotiate"]
    merchant: str
    avg_amount: float
    interval_days: int = 30
    occurrences: int = 0
    last_seen_at: Optional[datetime] = None


class SubscriptionActionResponse(BaseModel):
    status: str
    action: str
    estimated_monthly_savings: float
    current_streak: int
    total_xp: int
    action_type: Optional[str] = None
    action_payload: Optional[dict] = None


class SubscriptionSuspectOut(BaseModel):
    candidate_id: str
    merchant: str
    avg_amount: float
    estimated_monthly_cost: float
    occurrences: int
    interval_days: int
    last_seen_at: datetime
    confidence: float
    decision: Optional[str] = None


class SubscriptionSuspectDecisionRequest(BaseModel):
    decision: Literal["keep", "removed"]


# --- DEBATE / OFFER COMPARISON ---

DebatePriority = Literal["cheapest", "fastest", "best_overall"]
OfferProvider = Literal["amazon", "flipkart", "blinkit", "bigbasket", "zepto"]


class OfferQueryIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    max_results: int = Field(8, ge=1, le=25)
    priority: DebatePriority = "best_overall"
    location: Optional[str] = Field(None, max_length=80)


class OfferOut(BaseModel):
    provider: OfferProvider
    title: str
    price: Optional[float] = None
    currency: CurrencyCode = "INR"
    unit: Optional[str] = None
    delivery_eta_minutes: Optional[int] = Field(None, ge=0, le=7 * 24 * 60)
    rating: Optional[float] = Field(None, ge=0, le=5)
    url: str
    in_stock: Optional[bool] = None
    image_url: Optional[str] = None


class OfferAggregateOut(BaseModel):
    query: str
    priority: DebatePriority
    offers: List[OfferOut]
    errors_by_provider: dict[str, str] = Field(default_factory=dict)
    recommended_offer: Optional[OfferOut] = None


class DebateRunIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    max_results: int = Field(8, ge=1, le=25)
    priority: DebatePriority = "best_overall"
    location: Optional[str] = Field(None, max_length=80)


class DebateRoleOut(BaseModel):
    role: Literal["FrugalCoach", "ValueAnalyst", "ConvenienceAdvocate", "Referee"]
    text: str


class DebateOut(BaseModel):
    query: str
    priority: DebatePriority
    offers: List[OfferOut]
    chosen_offer: Optional[OfferOut] = None
    confidence: float = Field(0.5, ge=0, le=1)
    roles: List[DebateRoleOut]
    final_recommendation: str
