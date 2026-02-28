"""Documentation — Architecture, sample queries, demo script."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Documentation", page_icon="📖", layout="wide")

st.markdown("""
<div class="page-header">
    <h1>📖 Documentation</h1>
    <div class="page-subtitle">Architecture, methodology, sample queries, and demo script</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Architecture", "📝 Sample Queries", "🎬 Demo Script", "📊 Methodology"])

with tab1:
    st.markdown("""
    ### System Architecture

    ```
    ┌─────────────────────────────────────────────────────────┐
    │                   STREAMLIT FRONTEND                     │
    │  Overview │ Ask AI │ Explore │ Insights │ Risk │ ...     │
    └──────────────────────────┬──────────────────────────────┘
                               │
    ┌──────────────────────────▼──────────────────────────────┐
    │                 AI QUERY PLANNER                         │
    │   Natural Language → Intent Classification               │
    │   Entity Extraction → Structured JSON Plan               │
    └──────────────────────────┬──────────────────────────────┘
                               │
    ┌──────────────────────────▼──────────────────────────────┐
    │              QUERY EXECUTION ENGINE                      │
    │   JSON Plan → Pandas Operations → Results                │
    │   DataFrame + Chart Spec + Explanation                   │
    └──────────────────────────┬──────────────────────────────┘
                               │
    ┌──────────────────────────▼──────────────────────────────┐
    │                 DATA LAYER (Pandas)                      │
    │   Auto-profiled CSV with metadata & role detection       │
    └─────────────────────────────────────────────────────────┘
    ```

    ### Modules

    | Module | Purpose |
    |--------|---------|
    | `data_profiler.py` | Auto-detect schema, column roles, statistics |
    | `query_planner.py` | NL → structured JSON plan (18+ intent types) |
    | `query_executor.py` | Execute plans via Pandas, return results |
    | `insight_engine.py` | Auto-generate 10 financial insights with explainability |
    | `anomaly_detector.py` | IQR, Z-score, rolling, spike, concentration, percentile |
    | `predictor.py` | Linear trend + seasonal decomposition forecasting |
    | `scenario_engine.py` | What-if simulation (value/volume/fraud/failure) |
    | `risk_analyzer.py` | HHI, volatility, risk index |
    | `comparator.py` | Side-by-side group/period comparisons |
    | `data_quality.py` | Missing, duplicates, outliers, consistency |
    | `utils.py` | Formatting, column matching, helpers |

    ### Design Decisions

    1. **No LLM dependency** — Keyword-based intent classification ensures zero hallucination
    2. **Plan-then-execute** — AI produces structured plans, backend executes them
    3. **Auto schema detection** — No hardcoded column names; works on any tabular dataset
    4. **Every result is explainable** — Shows filters, aggregation logic, and reasoning
    5. **Minimal dependencies** — Only streamlit, pandas, plotly, scikit-learn, numpy
    6. **Predictive module** — Simple statistical models with disclosed methodology
    """)

with tab2:
    st.markdown("""
    ### 25+ Sample Queries

    **Basic:**
    1. What is the total transaction value?
    2. How many transactions are there?
    3. What is the average transaction amount?
    4. Show monthly trend of transaction volume
    5. Top 10 states by transaction value

    **Analytical:**
    6. Show month-over-month growth rate
    7. Peak transaction month
    8. Distribution of transactions by category
    9. Bottom 5 states by total value
    10. Concentration analysis by state

    **Comparison:**
    11. Compare Delhi vs Maharashtra
    12. Compare P2P vs P2M transactions
    13. Weekend vs weekday volume

    **Risk & Anomaly:**
    14. What is the fraud rate?
    15. Show failed transactions by state
    16. Anomaly detection in transaction amounts

    **Filtered:**
    17. Total value of grocery transactions
    18. Show transactions above 5000
    19. Transactions between January and March
    20. Top 5 categories by average value

    **Predictive:**
    21. Forecast next month trend
    22. Predict future transaction volume
    23. Show histogram of transaction values

    **Behavioral:**
    24. Average value by age group
    25. Which bank has the most transactions?
    """)

with tab3:
    st.markdown("""
    ### Demo Script (3–5 Minutes)

    **Opening (30s):**
    > "This is an AI-powered data intelligence platform that analyzes UPI transaction data.
    > It converts natural language questions into structured execution plans — zero hallucination."

    **1. Executive Overview (45s):**
    - Navigate to Overview
    - Highlight: Total transactions, value, growth rate, risk index
    - Show trend chart and state distribution

    **2. Ask AI (90s):**
    - Query: "Top 10 states by transaction value" → table + bar chart + explanation
    - Query: "Show month-over-month growth" → growth rates from real data
    - Query: "Compare Delhi vs Maharashtra" → side-by-side comparison
    - Emphasize: "Every number is computed from actual data."

    **3. Insights (30s):**
    - Show 10 auto-generated insights with "Why?" explanations
    - Highlight: skewness, concentration, fraud rate

    **4. Anomalies (30s):**
    - Show IQR, Z-score, and percentile results
    - Point out flagged rows with explanations

    **5. Predictions (30s):**
    - Show forecast with confidence intervals and RMSE
    - Run what-if simulation

    **Closing (15s):**
    > "Modular architecture. Zero hallucination. Works on any tabular dataset.
    > Reproducible locally in under 5 minutes."
    """)

with tab4:
    st.markdown("""
    ### Methodology

    **Query Processing Pipeline:**
    1. **Intent Classification** — Rule-based keyword matching across 18+ intent patterns
    2. **Entity Extraction** — Column names, values, date ranges, numeric thresholds
    3. **Plan Generation** — Structured JSON with intent, groupby, aggregation, filters, visualization
    4. **Execution** — Pandas operations on the raw DataFrame
    5. **Explanation** — Auto-generated reasoning for every result

    **Anomaly Detection Methods:**
    | Method | How It Works |
    |--------|-------------|
    | IQR | Flags values outside Q1 - 1.5×IQR and Q3 + 1.5×IQR |
    | Z-Score | Flags values with |z| > threshold (default 3.0) |
    | Percentile | Flags values outside 1st–99th percentile |
    | Rolling Deviation | Flags daily values > 2σ from rolling mean |
    | Growth Spikes | Flags months with >50% MoM growth |
    | Concentration | Flags entities with >30% market share |

    **Forecasting Model:**
    - **Method:** Linear trend + seasonal decomposition
    - **Validation:** 80/20 train/test split with RMSE metric
    - **Confidence:** 95% confidence intervals based on residual std
    - **Disclosure:** Simple statistical model, not deep learning

    **Risk Scoring:**
    - **HHI:** Herfindahl-Hirschman Index for market concentration
    - **CV:** Coefficient of Variation for volatility
    - **Composite:** Weighted index combining concentration, failure rate, and fraud rate
    """)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
