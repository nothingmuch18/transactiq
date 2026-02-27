"""Quality API — Data quality checks."""
from fastapi import APIRouter
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["quality"])


@router.get("/quality")
async def get_quality():
    from main import DATA
    from src.data_quality import run_quality_checks

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    results = run_quality_checks(df, meta)

    # Serialize DataFrames
    missing = results["missing_values"]
    return {
        "quality_score": results["quality_score"],
        "quality_grade": results["quality_grade"],
        "total_records": int(len(df)),
        "total_columns": int(len(df.columns)),
        "missing_values": {
            "table": missing["df"].to_dict(orient="records"),
            "total": missing["total_missing"],
            "pct": missing["overall_pct"],
        },
        "duplicates": results["duplicates"]["exact_duplicates"],
        "negative_values": {
            "table": results["negative_values"]["df"].to_dict(orient="records"),
            "found": results["negative_values"]["found"],
        },
        "extreme_outliers": {
            "table": results["extreme_outliers"]["df"].to_dict(orient="records"),
            "found": results["extreme_outliers"]["found"],
        },
        "consistency": {
            "table": results["consistency"]["df"].to_dict(orient="records"),
            "found": results["consistency"]["found"],
        },
    }
