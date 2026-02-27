"""Overview API — KPIs, profile, stats."""
from fastapi import APIRouter
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["overview"])


@router.get("/overview")
async def get_overview():
    from main import DATA
    from src.risk_analyzer import compute_risk_summary
    from src.utils import safe_divide

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    roles = meta.get("roles", {})
    amount_col = roles.get("amount")
    date_col = roles.get("date")
    status_col = roles.get("status")
    fraud_col = roles.get("fraud")

    risk = compute_risk_summary(df, meta)

    kpis = {
        "total_transactions": int(len(df)),
        "total_value": float(df[amount_col].sum()) if amount_col else 0,
        "avg_transaction": float(df[amount_col].mean()) if amount_col else 0,
        "median_transaction": float(df[amount_col].median()) if amount_col else 0,
        "risk_index": risk.get("risk_index", 0),
        "risk_level": risk.get("risk_level", "N/A"),
    }

    if status_col:
        failed = int(len(df[df[status_col] == "FAILED"]))
        kpis["success_rate"] = round(safe_divide(len(df) - failed, len(df)) * 100, 2)
        kpis["failed_count"] = failed

    if fraud_col:
        fraud_count = int(df[fraud_col].sum())
        kpis["fraud_count"] = fraud_count
        kpis["fraud_rate"] = round(safe_divide(fraud_count, len(df)) * 100, 4)

    # Monthly trend
    monthly_trend = []
    if date_col and amount_col:
        monthly = df.set_index(date_col).resample("M").agg({amount_col: ["sum", "count"]}).reset_index()
        monthly.columns = ["month", "value", "volume"]
        monthly["month"] = monthly["month"].astype(str)
        monthly_trend = monthly.to_dict(orient="records")

    # Top states
    top_states = []
    region_col = roles.get("region")
    if region_col and amount_col:
        top = df.groupby(region_col)[amount_col].sum().nlargest(10).reset_index()
        top.columns = ["state", "value"]
        top_states = top.to_dict(orient="records")

    # Category breakdown
    categories = []
    cat_col = roles.get("category")
    if cat_col and amount_col:
        cat = df.groupby(cat_col)[amount_col].sum().reset_index()
        cat.columns = ["category", "value"]
        categories = cat.to_dict(orient="records")

    return {
        "kpis": kpis,
        "roles": roles,
        "date_range": meta.get("date_range", {}),
        "monthly_trend": monthly_trend,
        "top_states": top_states,
        "categories": categories,
        "columns": len(df.columns),
        "load_time_ms": DATA["load_time_ms"],
    }
