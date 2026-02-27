"""Predictions API — Forecasting and scenario simulation."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["predictions"])


class ForecastRequest(BaseModel):
    months: int = 3


class ScenarioRequest(BaseModel):
    scenario: str
    value: float


@router.post("/forecast")
async def forecast(req: ForecastRequest):
    from main import DATA
    from src.predictor import forecast_monthly

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    result = forecast_monthly(df, meta, forecast_months=req.months)
    if "error" in result:
        return result

    return {
        "historical": result["historical_df"].to_dict(orient="records"),
        "forecast": result["forecast_df"].to_dict(orient="records"),
        "metrics": result["metrics"],
        "model_info": result["model_info"],
        "explanation": result["explanation"],
    }


@router.get("/scenarios")
async def get_scenarios():
    from main import DATA
    from src.scenario_engine import get_available_scenarios

    meta = DATA["metadata"]
    if meta is None:
        return {"error": "No data loaded"}

    return {"scenarios": get_available_scenarios(meta)}


@router.post("/scenario")
async def run_scenario(req: ScenarioRequest):
    from main import DATA
    from src.scenario_engine import simulate_scenario

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    result = simulate_scenario(df, meta, req.scenario, req.value)
    if "error" in result:
        return result

    return {
        "comparison": result["comparison_df"].to_dict(orient="records"),
        "explanation": result["explanation"],
    }
