from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import models


class SpendingForecaster:
    """
    True Holt-Winters Spending Forecasting Engine using statsmodels.
    Implements ExponentialSmoothing with additive trend and additive seasonality (seasonal_periods=7).
    
    Robust Fallback Hierarchy:
    - >= 14 days (>= 2 full weekly seasonal cycles): Full Holt-Winters Triple Exponential Smoothing
    - 7 to 13 days: Holt's Linear Trend (Double Exponential Smoothing, no seasonality)
    - < 7 days: Weighted Moving Average Run-Rate
    
    Supports 7-day, 30-day, and 90-day forecast horizons.
    """

    MINIMUM_SEASONAL_DAYS: int = 14
    SEASONAL_PERIODS: int = 7

    @classmethod
    def generate_forecast(
        cls,
        transactions: List[models.Transaction],
        monthly_income: float = 0.0,
        fixed_expenses: float = 0.0
    ) -> Dict[str, Any]:
        if not transactions:
            return cls._empty_forecast(monthly_income)

        # Sort chronologically
        txns = sorted(
            [t for t in transactions if t.amount and t.amount > 0 and t.date],
            key=lambda x: x.date
        )
        if not txns:
            return cls._empty_forecast(monthly_income)

        # Compute continuous daily spend over available historical window
        first_date = txns[0].date.date()
        last_date = txns[-1].date.date()
        total_days = max(1, (last_date - first_date).days + 1)

        daily_totals = defaultdict(float)
        cat_totals = defaultdict(float)
        for t in txns:
            amt = float(t.amount)
            daily_totals[t.date.date()] += amt
            cat_totals[(t.category or "other").lower()] += amt

        # Build continuous daily array (fill missing days with 0.0)
        daily_series = [daily_totals.get(first_date + timedelta(days=i), 0.0) for i in range(total_days)]
        daily_avg = float(np.mean(daily_series))

        # Generate 90-step forecast using statsmodels ExponentialSmoothing
        forecast_90_steps: List[float] = []
        model_type = "Statsmodels Holt-Winters Triple Exponential Smoothing (trend='add', seasonal='add', m=7)"
        trend_applied = "add"
        seasonal_applied = "add"

        try:
            if total_days >= cls.MINIMUM_SEASONAL_DAYS:
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                series_arr = np.array(daily_series, dtype=float)
                if np.all(series_arr == 0):
                    forecast_90_steps = [0.0] * 90
                else:
                    hw_model = ExponentialSmoothing(
                        series_arr,
                        trend="add",
                        seasonal="add",
                        seasonal_periods=cls.SEASONAL_PERIODS,
                        initialization_method="estimated"
                    )
                    hw_fit = hw_model.fit(optimized=True)
                    raw_fc = hw_fit.forecast(steps=90)
                    forecast_90_steps = np.clip(raw_fc, 0.0, None).tolist()
            elif total_days >= 7:
                from statsmodels.tsa.holtwinters import ExponentialSmoothing
                series_arr = np.array(daily_series, dtype=float)
                hw_model = ExponentialSmoothing(
                    series_arr,
                    trend="add",
                    seasonal=None,
                    initialization_method="estimated"
                )
                hw_fit = hw_model.fit(optimized=True)
                raw_fc = hw_fit.forecast(steps=90)
                forecast_90_steps = np.clip(raw_fc, 0.0, None).tolist()
                model_type = "Statsmodels Holt Linear Trend Fallback (insufficient history for seasonality, total_days < 14)"
                seasonal_applied = None
            else:
                # Weighted run rate fallback
                smoothed = daily_series[0] if daily_series else 0.0
                alpha = 0.25
                for val in daily_series[1:]:
                    smoothed = alpha * val + (1 - alpha) * smoothed
                effective_rate = 0.6 * smoothed + 0.4 * daily_avg
                forecast_90_steps = [max(0.0, effective_rate)] * 90
                model_type = "Weighted Moving Average Fallback (total_days < 7)"
                trend_applied = None
                seasonal_applied = None
        except Exception as e:
            # Graceful numerical fallback if optimization fails
            smoothed = daily_series[0] if daily_series else 0.0
            alpha = 0.25
            for val in daily_series[1:]:
                smoothed = alpha * val + (1 - alpha) * smoothed
            effective_rate = 0.6 * smoothed + 0.4 * daily_avg
            forecast_90_steps = [max(0.0, effective_rate)] * 90
            model_type = f"Robust Moving Average Fallback (Optimization note: {str(e)[:40]})"
            trend_applied = None
            seasonal_applied = None

        # Category shares
        total_hist_spend = sum(cat_totals.values())
        cat_weights = {k: (v / total_hist_spend) if total_hist_spend > 0 else 0.0 for k, v in cat_totals.items()}
        effective_daily_rate = round(float(np.mean(forecast_90_steps[:30])), 2)

        def project_horizon(days: int) -> Dict[str, Any]:
            projected_spend = round(float(sum(forecast_90_steps[:days])), 2)
            horizon_income = round((monthly_income / 30.0) * days, 2)
            expected_savings = round(max(0.0, horizon_income - projected_spend), 2)
            net_cash_flow = round(horizon_income - projected_spend, 2)

            cat_breakdown = {
                cat: round(projected_spend * weight, 2)
                for cat, weight in cat_weights.items()
            }

            return {
                "horizon_days": days,
                "projected_spending": projected_spend,
                "projected_income": horizon_income,
                "expected_savings": expected_savings,
                "net_cash_flow": net_cash_flow,
                "cash_flow_risk": "high" if net_cash_flow < 0 else "moderate" if net_cash_flow < (horizon_income * 0.1) else "low",
                "category_breakdown": cat_breakdown,
                "daily_forecast": [round(float(x), 2) for x in forecast_90_steps[:days]]
            }

        return {
            "model_metadata": {
                "model_type": model_type,
                "seasonal_periods": cls.SEASONAL_PERIODS,
                "trend": trend_applied,
                "seasonal": seasonal_applied,
                "history_days_analyzed": total_days,
                "minimum_history_required": "14 days for seasonal Holt-Winters (2 weekly cycles); 7 days for linear trend",
                "historical_daily_average": round(daily_avg, 2),
                "smoothed_daily_rate": effective_daily_rate,
                "assumptions": [
                    "Triple exponential smoothing captures additive level, additive trend, and 7-day weekly seasonality.",
                    "Category spending shares project proportionally according to historical spending distribution.",
                    "Expected income assumes pro-rated monthly baseline."
                ],
                "limitations": "Forecast does not account for unexpected large capital purchases or exogenous macroeconomic shocks."
            },
            "forecast_7_day": project_horizon(7),
            "forecast_30_day": project_horizon(30),
            "forecast_90_day": project_horizon(90)
        }

    @staticmethod
    def _empty_forecast(monthly_income: float) -> Dict[str, Any]:
        return {
            "model_metadata": {
                "model_type": "Baseline Default",
                "seasonal_periods": 7,
                "trend": None,
                "seasonal": None,
                "history_days_analyzed": 0,
                "minimum_history_required": "14 days for seasonal Holt-Winters (2 weekly cycles); 7 days for linear trend",
                "historical_daily_average": 0.0,
                "smoothed_daily_rate": 0.0,
                "assumptions": ["Insufficient transaction history for time-series projection."],
                "limitations": "Requires at least 7 transactions to build predictive trend velocity."
            },
            "forecast_7_day": {"horizon_days": 7, "projected_spending": 0.0, "projected_income": round((monthly_income / 30) * 7, 2), "expected_savings": 0.0, "net_cash_flow": 0.0, "cash_flow_risk": "low", "category_breakdown": {}, "daily_forecast": []},
            "forecast_30_day": {"horizon_days": 30, "projected_spending": 0.0, "projected_income": monthly_income, "expected_savings": monthly_income, "net_cash_flow": monthly_income, "cash_flow_risk": "low", "category_breakdown": {}, "daily_forecast": []},
            "forecast_90_day": {"horizon_days": 90, "projected_spending": 0.0, "projected_income": monthly_income * 3, "expected_savings": monthly_income * 3, "net_cash_flow": monthly_income * 3, "cash_flow_risk": "low", "category_breakdown": {}, "daily_forecast": []}
        }
