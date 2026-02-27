"""Insights API — Auto-generated intelligence."""
from fastapi import APIRouter
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["insights"])


@router.get("/insights")
async def get_insights():
    from main import DATA
    from src.insight_engine import generate_insights

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    insights = generate_insights(df, meta)
    return {"insights": insights, "count": len(insights)}
