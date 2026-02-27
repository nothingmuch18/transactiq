"""
UPI Data Intelligence Platform — FastAPI Backend
Wraps existing analysis modules into a clean REST API.
"""
import os
import sys
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_profiler import load_and_profile

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("upi-platform")

# Global state
DATA = {"df": None, "metadata": None, "load_time_ms": 0, "source": ""}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-load dataset on startup."""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    csv_files = [f for f in os.listdir(data_dir) if f.endswith(".csv")] if os.path.exists(data_dir) else []

    if csv_files:
        filepath = os.path.join(data_dir, csv_files[0])
        logger.info(f"Loading dataset: {filepath}")
        t0 = time.time()
        df, metadata = load_and_profile(filepath)
        DATA["df"] = df
        DATA["metadata"] = metadata
        DATA["load_time_ms"] = round((time.time() - t0) * 1000, 0)
        DATA["source"] = csv_files[0]
        logger.info(f"Loaded {len(df):,} rows in {DATA['load_time_ms']}ms")
    else:
        logger.warning("No CSV found in data/ directory")

    yield  # App runs here
    logger.info("Shutting down")


app = FastAPI(
    title="UPI Intelligence API",
    description="AI-powered analytics engine for UPI transaction data",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from api.overview import router as overview_router
from api.query import router as query_router
from api.insights import router as insights_router
from api.anomalies import router as anomalies_router
from api.risk import router as risk_router
from api.compare import router as compare_router
from api.quality import router as quality_router
from api.upload import router as upload_router


app.include_router(overview_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(insights_router, prefix="/api")
app.include_router(anomalies_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
app.include_router(compare_router, prefix="/api")
app.include_router(quality_router, prefix="/api")
app.include_router(upload_router, prefix="/api")



@app.get("/api/health")
async def health():
    loaded = DATA["df"] is not None
    return {
        "status": "ok" if loaded else "no_data",
        "rows": len(DATA["df"]) if loaded else 0,
        "load_time_ms": DATA["load_time_ms"],
        "source": DATA.get("source", ""),
    }
