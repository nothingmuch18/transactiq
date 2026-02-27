"""Upload API — CSV upload, reset, schema, preview, export."""
import os
import io
import time
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(tags=["upload"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and replace the active dataset."""
    from main import DATA, logger
    from src.data_profiler import load_and_profile, get_column_summary_df
    import pandas as pd

    # Validate file type
    if not file.filename.endswith(('.csv', '.tsv', '.txt')):
        raise HTTPException(400, "Only CSV/TSV files are supported")

    # Read file
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large ({len(contents) / 1024 / 1024:.1f}MB). Max is {MAX_FILE_SIZE // 1024 // 1024}MB.")
    if len(contents) < 10:
        raise HTTPException(400, "File appears to be empty")

    # Try multiple delimiters and encodings
    df = None
    errors = []
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        for sep in [',', '\t', ';', '|']:
            try:
                text = contents.decode(encoding)
                df = pd.read_csv(io.StringIO(text), sep=sep)
                if len(df.columns) >= 2 and len(df) >= 1:
                    break
                df = None
            except Exception as e:
                errors.append(str(e))
                df = None
        if df is not None:
            break

    if df is None:
        raise HTTPException(400, f"Could not parse CSV. Make sure it is a valid tabular file. Errors: {'; '.join(errors[:3])}")

    # Profile the dataset
    t0 = time.time()
    try:
        df, metadata = load_and_profile(df)
    except Exception as e:
        raise HTTPException(400, f"Failed to profile dataset: {str(e)}")

    load_time = round((time.time() - t0) * 1000, 0)

    # Replace global state
    DATA["df"] = df
    DATA["metadata"] = metadata
    DATA["load_time_ms"] = load_time
    DATA["source"] = file.filename

    logger.info(f"Uploaded: {file.filename} — {len(df):,} rows, {len(df.columns)} cols in {load_time}ms")

    # Build response
    col_summary = get_column_summary_df(metadata).to_dict(orient="records")
    roles = metadata.get("roles", {})

    return {
        "status": "ok",
        "filename": file.filename,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "load_time_ms": load_time,
        "numeric_columns": metadata.get("numeric_columns", []),
        "categorical_columns": metadata.get("categorical_columns", []),
        "datetime_columns": metadata.get("datetime_columns", []),
        "id_columns": metadata.get("id_columns", []),
        "roles": roles,
        "duplicate_rows": metadata.get("duplicate_rows", 0),
        "column_summary": col_summary,
        "date_range": metadata.get("date_range"),
        "correlation_matrix": metadata.get("correlation_matrix"),
    }


@router.post("/reset")
async def reset_dataset():
    """Reset to the default dataset from data/ directory."""
    from main import DATA, logger
    from src.data_profiler import load_and_profile

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")] if os.path.exists(data_dir) else []

    if not csv_files:
        raise HTTPException(404, "No default CSV in data/ directory")

    filepath = os.path.join(data_dir, csv_files[0])
    t0 = time.time()
    df, metadata = load_and_profile(filepath)
    load_time = round((time.time() - t0) * 1000, 0)

    DATA["df"] = df
    DATA["metadata"] = metadata
    DATA["load_time_ms"] = load_time
    DATA["source"] = csv_files[0]

    logger.info(f"Reset to default: {csv_files[0]} — {len(df):,} rows in {load_time}ms")

    return {
        "status": "ok",
        "filename": csv_files[0],
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "load_time_ms": load_time,
    }


@router.get("/schema")
async def get_schema():
    """Return full schema metadata for the current dataset."""
    from main import DATA
    from src.data_profiler import get_descriptive_stats

    df = DATA["df"]
    meta = DATA["metadata"]
    if df is None:
        return {"error": "No data loaded"}

    stats = get_descriptive_stats(df, meta)

    return {
        "source": DATA.get("source", "unknown"),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": df.columns.tolist(),
        "column_details": meta.get("column_details", {}),
        "numeric_columns": meta.get("numeric_columns", []),
        "categorical_columns": meta.get("categorical_columns", []),
        "datetime_columns": meta.get("datetime_columns", []),
        "id_columns": meta.get("id_columns", []),
        "roles": meta.get("roles", {}),
        "duplicate_rows": meta.get("duplicate_rows", 0),
        "date_range": meta.get("date_range"),
        "correlation_matrix": meta.get("correlation_matrix"),
        "summary_stats": stats.to_dict() if not stats.empty else {},
    }


@router.get("/preview")
async def preview_data(limit: int = 50):
    """Return first N rows of the current dataset."""
    from main import DATA

    df = DATA["df"]
    if df is None:
        return {"error": "No data loaded"}

    limit = min(limit, 200)
    preview = df.head(limit)

    # Convert datetime columns to strings for JSON serialization
    for col in preview.select_dtypes(include=["datetime64"]).columns:
        preview[col] = preview[col].astype(str)

    return {
        "columns": preview.columns.tolist(),
        "rows": preview.to_dict(orient="records"),
        "total_rows": int(len(df)),
        "showing": int(len(preview)),
    }


@router.get("/export")
async def export_data(format: str = "csv"):
    """Export current dataset as CSV download."""
    from main import DATA

    df = DATA["df"]
    if df is None:
        raise HTTPException(404, "No data loaded")

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)

    filename = DATA.get("source", "export") .replace(".csv", "") + "_export.csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
