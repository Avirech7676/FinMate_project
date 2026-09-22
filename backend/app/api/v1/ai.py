from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
import models
import auth
from app.ai.financial_agent import FinancialAgent
from app.ai.tool_registry import ToolRegistry

router = APIRouter(prefix="/ai", tags=["ai"])


class AIAgentRequest(BaseModel):
    message: str
    roast_mode: Optional[bool] = False


class AIToolExecuteRequest(BaseModel):
    tool_name: str
    parameters: Optional[Dict[str, Any]] = None


@router.post("/chat")
def chat_with_financial_agent(
    req: AIAgentRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Production financial intelligence agent with guardrails, deterministic context,
    and graceful fallback.
    """
    return FinancialAgent.execute(
        db=db,
        user=current_user,
        user_query=req.message,
        roast_mode=bool(req.roast_mode)
    )


@router.get("/tools")
def list_available_tools(
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    List whitelisted financial tools available to the AI agent.
    """
    return {
        "tools": [
            {"name": "get_transactions", "description": "Fetch recent transactions"},
            {"name": "get_budget", "description": "Fetch current month budget status"},
            {"name": "get_goals", "description": "Fetch active goals and pacing status"},
            {"name": "get_spending_summary", "description": "Calculate categorical spend breakdown"},
            {"name": "get_anomalies", "description": "Run 3-tier anomaly detection"},
            {"name": "get_forecast", "description": "Generate 7, 30, and 90 day spending forecast"},
            {"name": "get_cashflow", "description": "Calculate cash flow trajectory and risk"},
            {"name": "get_subscriptions", "description": "Detect recurring subscription charges"},
            {"name": "get_health_score", "description": "Compute explainable financial health score"}
        ]
    }


@router.post("/tools/execute")
def execute_tool(
    req: AIToolExecuteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Directly execute a whitelisted deterministic tool for the authenticated user.
    """
    registry = ToolRegistry(db, current_user)
    params = req.parameters or {}
    result = registry.dispatch(req.tool_name, **params)
    return {
        "tool_name": req.tool_name,
        "result": result
    }
