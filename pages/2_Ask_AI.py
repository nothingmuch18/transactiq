"""Ask AI — Natural language query engine with premium UI."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Ask AI", page_icon="🧠", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata

from src.query_planner import plan_query
from src.query_executor import execute_plan
from src.utils import format_currency, format_number

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#7c3aed", "#0d9488", "#3b82f6", "#ec4899", "#f59e0b", "#10b981"]

st.markdown("""
<div class="page-header">
    <h1>🧠 Ask AI</h1>
    <div class="page-subtitle">Ask any question in plain English — the AI converts it into a structured execution plan</div>
</div>
""", unsafe_allow_html=True)

if 'query_history' not in st.session_state:
    st.session_state.query_history = []

# Sample Queries
SAMPLE_QUERIES = {
    "📊 Basic": [
        "What is the total transaction value?",
        "How many transactions are there?",
        "What is the average transaction amount?",
        "Show monthly trend of transaction volume",
        "Top 10 states by transaction value",
    ],
    "📈 Analysis": [
        "Show month-over-month growth rate",
        "Peak transaction month",
        "Distribution by category",
        "Bottom 5 states by total value",
        "Concentration analysis by state",
    ],
    "⚖️ Compare": [
        "Compare Delhi vs Maharashtra",
        "Compare P2P vs P2M transactions",
    ],
    "🚨 Risk": [
        "What is the fraud rate?",
        "Show failed transactions by state",
        "Anomaly detection in amounts",
    ],
    "🔍 Filtered": [
        "Show transactions above 5000",
        "Total value of grocery transactions",
        "Transactions between January and March",
    ],
    "🔮 Predict": [
        "Forecast next month trend",
        "Show histogram of transaction values",
    ],
}

with st.expander("📝 Sample Queries", expanded=False):
    tabs = st.tabs(list(SAMPLE_QUERIES.keys()))
    for tab, (cat, queries) in zip(tabs, SAMPLE_QUERIES.items()):
        with tab:
            cols = st.columns(2)
            for i, q in enumerate(queries):
                if cols[i % 2].button(q, key=f"sq_{cat}_{i}", use_container_width=True):
                    st.session_state.current_query = q

# Query Input
default_query = st.session_state.get('current_query', '')
query = st.text_input("🔍 Enter your question:", value=default_query,
                       placeholder="e.g., Top 10 states by total transaction value")

if query:
    with st.spinner("Processing query..."):
        plan = plan_query(query, df, metadata)
        result = execute_plan(plan, df, metadata)

    st.session_state.query_history.append({
        'query': query, 'intent': plan['intent'], 'time_ms': result['exec_time_ms']
    })

    st.markdown("---")

    # Execution metadata
    st.markdown(f"""
    <div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:1rem;">
        <div class="exec-meta">🎯 {plan['intent']}</div>
        <div class="exec-meta">📊 {result['rows_scanned']:,} rows</div>
        <div class="exec-meta">⚡ {result['exec_time_ms']:.1f}ms</div>
    </div>
    """, unsafe_allow_html=True)

    # Explanation
    st.markdown(f"""
    <div class="explanation-box">
        <p>{result['explanation']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Result Table
    result_df = result['result_df']
    if len(result_df) > 0:
        st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        csv = result_df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, "query_result.csv", "text/csv")

        # Chart
        chart_spec = result['chart_spec']
        if chart_spec['type'] not in ('metric', 'table') and len(result_df) >= 2 and len(result_df.columns) >= 2:
            st.markdown('<div class="section-label">Visualization</div>', unsafe_allow_html=True)
            x, y = chart_spec['x'], chart_spec['y']

            fig = None
            if chart_spec['type'] == 'line':
                fig = px.line(result_df, x=x, y=y, markers=True,
                             template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            elif chart_spec['type'] == 'bar':
                fig = px.bar(result_df, x=x, y=y,
                            template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            elif chart_spec['type'] == 'pie':
                fig = px.pie(result_df, values=y, names=x, hole=0.45,
                            template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            elif chart_spec['type'] == 'scatter':
                fig = px.scatter(result_df, x=x, y=y,
                                template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            elif chart_spec['type'] == 'histogram':
                fig = px.bar(result_df, x='Range', y='Count',
                            template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            elif chart_spec['type'] == 'grouped_bar':
                value_cols = [c for c in result_df.columns if c not in ['Metric', 'Absolute Diff', '% Difference', 'Higher', 'Diff %', 'Difference']]
                if len(value_cols) >= 2:
                    melt_df = result_df.melt(id_vars=['Metric'], value_vars=value_cols[:2],
                                           var_name='Group', value_name='Value')
                    fig = px.bar(melt_df, x='Metric', y='Value', color='Group', barmode='group',
                                template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
                else:
                    fig = px.bar(result_df, x=x, y=y, template=CHART_TEMPLATE,
                                color_discrete_sequence=CHART_COLORS)
            else:
                fig = px.bar(result_df, x=x, y=y, template=CHART_TEMPLATE,
                            color_discrete_sequence=CHART_COLORS)

            if fig:
                fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20),
                                 font=dict(family="Inter"), xaxis_title="", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)

    # Execution Plan
    with st.expander("🔧 Execution Plan"):
        cols = st.columns(3)
        cols[0].write(f"**Intent:** {plan.get('intent')}")
        cols[0].write(f"**Aggregation:** {plan.get('aggregation')}")
        cols[1].write(f"**Group By:** {plan.get('group_by', 'None')}")
        cols[1].write(f"**Metric:** {plan.get('metric_column')}")
        cols[2].write(f"**Chart:** {plan.get('visualization')}")
        cols[2].write(f"**Filters:** {len(plan.get('filters', []))}")

# Query History
if st.session_state.query_history:
    with st.expander(f"📜 History ({len(st.session_state.query_history)})"):
        for i, h in enumerate(reversed(st.session_state.query_history[-10:])):
            st.caption(f"{i+1}. {h['query']} — `{h['intent']}` ({h['time_ms']}ms)")

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
