# Technical Documentation

## Architecture

The UPI Data Intelligence Platform uses a **plan-then-execute** architecture:

1. **Data Profiling Engine** — Auto-detects column types, roles, and statistics on load
2. **AI Query Planner** — Converts natural language → structured JSON plan (keyword-based, no LLM)
3. **Query Execution Engine** — Executes JSON plan via Pandas → returns DataFrame + chart + explanation
4. **Insight/Anomaly/Risk engines** — Specialized modules for financial intelligence

## Query Flow

```
User NL query → classify_intent() → extract entities → build JSON plan → execute_plan() → result
```

### Intent Types (15)
total_volume, total_value, average_value, trend_analysis, month_over_month,
top_k, bottom_k, comparison, distribution, anomaly_detection, data_quality,
concentration, fraud, failure_analysis, peak_analysis

## Zero Hallucination Guarantee

- AI only produces **plans** (JSON), never actual numbers
- All numbers computed by Pandas from raw data
- Every result includes an explanation of how it was computed
- No external LLM API calls

## Module Reference

| File | Lines | Purpose |
|------|-------|---------|
| `data_profiler.py` | ~120 | Schema detection, stats, metadata |
| `query_planner.py` | ~250 | Intent classification, entity extraction |
| `query_executor.py` | ~350 | Plan execution via Pandas |
| `insight_engine.py` | ~150 | Auto-generated financial insights |
| `anomaly_detector.py` | ~130 | Multi-method anomaly detection |
| `risk_analyzer.py` | ~130 | Concentration & risk metrics |
| `comparator.py` | ~130 | Group/period comparisons |
| `data_quality.py` | ~130 | Quality scoring & checks |
| `utils.py` | ~120 | Shared formatting & helpers |
