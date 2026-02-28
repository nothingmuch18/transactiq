"""Anomalies API — Multi-method anomaly detection."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["anomalies"])


class AnomalyRequest(BaseModel):
    method: str = "all"
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0


@router.post("/anomalies")
async def detect_anomalies(req: AnomalyRequest):
    from main import DATA, CACHE
    cache_key = f"anomalies_{req.method}"
    if cache_key in CACHE:
        return CACHE[cache_key]
    from src.anomaly_detector import (
        run_full_anomaly_detection, detect_iqr_anomalies,
        detect_zscore_anomalies, detect_percentile_anomalies
    )

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    amount_col = meta.get("roles", {}).get("amount")
    if not amount_col:
        return {"error": "No amount column"}

    if req.method == "iqr":
        anomalies, stats = detect_iqr_anomalies(df, amount_col, multiplier=req.iqr_multiplier)
        results = {"IQR Method": {
            "anomalies": anomalies.head(20).to_dict(orient="records"),
            "count": len(anomalies),
            "description": f"Found {len(anomalies)} anomalies using IQR ({req.iqr_multiplier}x)."
        }}
    elif req.method == "zscore":
        anomalies, stats = detect_zscore_anomalies(df, amount_col, threshold=req.zscore_threshold)
        results = {"Z-Score Method": {
            "anomalies": anomalies.head(20).to_dict(orient="records"),
            "count": len(anomalies),
            "description": f"Found {len(anomalies)} anomalies with |Z| > {req.zscore_threshold}."
        }}
    elif req.method == "percentile":
        anomalies, stats = detect_percentile_anomalies(df, amount_col)
        results = {"Percentile": {
            "anomalies": anomalies.head(20).to_dict(orient="records"),
            "count": len(anomalies),
            "description": f"Found {len(anomalies)} anomalies outside 1st-99th percentile."
        }}
    else:
        raw_results = run_full_anomaly_detection(df, meta, method=req.method)
        results = {}
        for name, r in raw_results.items():
            anom_df = r.get("anomalies")
            results[name] = {
                "anomalies": anom_df.head(20).to_dict(orient="records") if anom_df is not None and len(anom_df) > 0 else [],
                "count": r["count"],
                "description": r["description"],
            }

    total = sum(r["count"] for r in results.values())
    result = {
        "results": results,
        "total_anomalies": total,
        "anomaly_rate": round(total / len(df) * 100, 2),
        "methods_used": len(results),
    }
    CACHE[cache_key] = result
    return result
