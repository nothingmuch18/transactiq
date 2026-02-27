"""Compare API — Side-by-side analysis."""
from fastapi import APIRouter
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["compare"])


class CompareRequest(BaseModel):
    dimension: str
    group_a: str
    group_b: str


@router.get("/compare/dimensions")
async def get_dimensions():
    from main import DATA
    from src.comparator import get_available_comparisons

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    comps = get_available_comparisons(df, meta)
    return {"dimensions": {k: {"values": v["values"], "column": v["column"]} for k, v in comps.items()}}


@router.post("/compare")
async def compare(req: CompareRequest):
    from main import DATA
    from src.comparator import compare_groups, compare_time_periods, get_available_comparisons

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    roles = meta.get("roles", {})
    amount_col = roles.get("amount")
    date_col = roles.get("date")

    comps = get_available_comparisons(df, meta)
    dim_info = comps.get(req.dimension)
    if not dim_info:
        return {"error": f"Unknown dimension: {req.dimension}"}

    if req.dimension in ("Months", "Quarters"):
        result = compare_time_periods(df, date_col, amount_col, req.group_a, req.group_b)
    else:
        result = compare_groups(df, dim_info["column"], req.group_a, req.group_b, amount_col, meta)

    if result is None:
        return {"error": "No data for the selected groups"}

    return {
        "comparison": result["comparison_df"].to_dict(orient="records"),
        "columns": result["comparison_df"].columns.tolist(),
        "chart_data": result["chart_data"].to_dict(orient="records") if result.get("chart_data") is not None else [],
        "explanation": result["explanation"],
    }
