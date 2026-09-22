from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.transactions import router as transactions_router
from app.api.v1.goals import router as goals_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.cashflow import router as cashflow_router
from app.api.v1.ai import router as ai_router
from app.api.v1.simulation import router as simulation_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(goals_router)
api_v1_router.include_router(subscriptions_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(cashflow_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(simulation_router)
