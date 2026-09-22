from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db
import models
import auth
from app.services.simulation_service import FinancialSimulatorService

router = APIRouter(prefix="/simulation", tags=["simulation"])


class PurchaseSimulationRequest(BaseModel):
    purchase_amount: float = Field(..., gt=0, description="Hypothetical purchase price")
    purchase_category: Optional[str] = Field("shopping", description="Category of the expense")
    purchase_date: Optional[datetime] = None
    description: Optional[str] = None


@router.post("/purchase")
def simulate_purchase(
    req: PurchaseSimulationRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Simulate the financial impact of a potential purchase on budget, cash flow, and goals.
    """
    service = FinancialSimulatorService(db)
    return service.simulate_purchase(
        user=current_user,
        purchase_amount=req.purchase_amount,
        purchase_category=req.purchase_category or "shopping",
        purchase_date=req.purchase_date,
        description=req.description
    )
