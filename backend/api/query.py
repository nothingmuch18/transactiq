"""Query API — Natural language query plan + execute."""
from fastapi import APIRouter
from pydantic import BaseModel
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
async def run_query(req: QueryRequest):
    from main import DATA
    from src.query_planner import plan_query
    from src.query_executor import execute_plan

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    plan = plan_query(req.query, df, meta)
    result = execute_plan(plan, df, meta)

    result_records = result["result_df"].to_dict(orient="records") if len(result["result_df"]) > 0 else []

    return {
        "plan": {
            "intent": plan.get("intent"),
            "aggregation": plan.get("aggregation"),
            "group_by": plan.get("group_by"),
            "metric_column": plan.get("metric_column"),
            "visualization": plan.get("visualization"),
            "filters": plan.get("filters", []),
        },
        "results": result_records,
        "columns": result["result_df"].columns.tolist() if len(result["result_df"]) > 0 else [],
        "chart_spec": result["chart_spec"],
        "explanation": result["explanation"],
        "rows_scanned": result["rows_scanned"],
        "exec_time_ms": result["exec_time_ms"],
    }
