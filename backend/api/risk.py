"""Risk API — Concentration, volatility, composite risk."""
from fastapi import APIRouter
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["risk"])


@router.get("/risk")
async def get_risk(dimension: Optional[str] = None):
    from main import DATA, CACHE
    cache_key = f"risk_{dimension or 'default'}"
    if cache_key in CACHE:
        return CACHE[cache_key]
    from src.risk_analyzer import compute_risk_summary, compute_concentration_metrics, compute_volatility_index

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    roles = meta.get("roles", {})
    amount_col = roles.get("amount")
    date_col = roles.get("date")
    if not amount_col:
        return {"error": "No amount column"}

    risk = compute_risk_summary(df, meta)
    dim = dimension or roles.get("region") or list(df.select_dtypes(include=["object"]).columns)[0]

    # Concentration
    conc = compute_concentration_metrics(df, dim, amount_col)
    conc_table = conc["shares_df"].to_dict(orient="records") if "shares_df" in conc else []
    conc.pop("shares_df", None)

    # Volatility
    volatility = {}
    if date_col:
        vol = compute_volatility_index(df, date_col, amount_col)
        vol.pop("monthly_series", None)
        volatility = vol

        monthly = df.set_index(date_col).resample("M")[amount_col].sum().reset_index()
        monthly.columns = ["month", "value"]
        monthly["month"] = monthly["month"].astype(str)
        volatility["monthly_data"] = monthly.to_dict(orient="records")

    # Available dimensions
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    result = {
        "risk_index": risk.get("risk_index", 0),
        "risk_level": risk.get("risk_level", "N/A"),
        "concentration": {**conc, "table": conc_table},
        "volatility": volatility,
        "current_dimension": dim,
        "available_dimensions": cat_cols,
    }
    CACHE[cache_key] = result
    return result
