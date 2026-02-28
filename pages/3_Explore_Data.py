"""Explore Data — Interactive multi-condition filter, search, and aggregation."""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Explore Data", page_icon="🔍", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})

from src.utils import get_numeric_columns, get_categorical_columns
from src.data_profiler import get_column_summary_df

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#7c3aed", "#0d9488", "#3b82f6", "#ec4899"]

st.markdown("""
<div class="page-header">
    <h1>🔍 Explore Data</h1>
    <div class="page-subtitle">Aggregate, filter, and search your dataset interactively</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Aggregate", "🔎 Filter & Search", "📋 Column Summary"])

with tab1:
    st.markdown('<div class="section-label">Group By & Aggregate</div>', unsafe_allow_html=True)
    cat_cols = get_categorical_columns(df)
    num_cols = get_numeric_columns(df)
    date_col = roles.get('date')
    derived = ['Month', 'Quarter'] if date_col else []

    c1, c2, c3 = st.columns(3)
    with c1:
        group_col = st.selectbox("Group By", cat_cols + derived)
    with c2:
        metric = st.selectbox("Metric", ['Count'] + num_cols)
    with c3:
        agg_func = st.selectbox("Function", ['sum', 'mean', 'count', 'max', 'min', 'median'])

    if st.button("Run Analysis", type="primary"):
        work_df = df.copy()
        if group_col == 'Month' and date_col:
            work_df['Month'] = work_df[date_col].dt.to_period('M').astype(str)
            actual_col = 'Month'
        elif group_col == 'Quarter' and date_col:
            work_df['Quarter'] = work_df[date_col].dt.to_period('Q').astype(str)
            actual_col = 'Quarter'
        else:
            actual_col = group_col

        if actual_col in work_df.columns:
            if metric == 'Count':
                result = work_df.groupby(actual_col).size().reset_index(name='Count')
                sort_col = 'Count'
            else:
                result = work_df.groupby(actual_col)[metric].agg(agg_func).reset_index()
                result[metric] = result[metric].round(2)
                sort_col = metric

            result = result.sort_values(sort_col, ascending=False)
            st.dataframe(result, use_container_width=True, hide_index=True)

            fig = px.bar(result.head(20), x=actual_col, y=sort_col,
                        template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
            fig.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20),
                             font=dict(family="Inter"), xaxis_title="", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

            st.download_button("📥 Download", result.to_csv(index=False), "aggregation.csv", "text/csv")

with tab2:
    st.markdown('<div class="section-label">Quick Search</div>', unsafe_allow_html=True)
    search = st.text_input("Search across all text columns", placeholder="e.g., Delhi, Grocery, FAILED")

    st.markdown('<div class="section-label">Multi-Condition Filters</div>', unsafe_allow_html=True)
    logic = st.radio("Logic:", ["AND", "OR"], horizontal=True)

    if 'n_filters' not in st.session_state:
        st.session_state.n_filters = 1

    fc1, fc2 = st.columns(2)
    with fc1:
        if st.button("➕ Add Filter"):
            st.session_state.n_filters = min(st.session_state.n_filters + 1, 5)
    with fc2:
        if st.button("➖ Remove"):
            st.session_state.n_filters = max(st.session_state.n_filters - 1, 1)

    filters = []
    for i in range(st.session_state.n_filters):
        cols = st.columns([2, 1, 2])
        with cols[0]:
            fc = st.selectbox(f"Column", df.columns.tolist(), key=f"fc_{i}")
        with cols[1]:
            ops = ['=', '>', '<', '>=', '<=', '!='] if pd.api.types.is_numeric_dtype(df[fc]) else ['=', '!=', 'contains']
            op = st.selectbox(f"Op", ops, key=f"fo_{i}")
        with cols[2]:
            if pd.api.types.is_numeric_dtype(df[fc]):
                val = st.number_input(f"Value", value=float(df[fc].min()), key=f"fv_{i}")
            else:
                uniq = df[fc].dropna().unique().tolist()[:100]
                val = st.selectbox(f"Value", uniq, key=f"fv_{i}")
        filters.append((fc, op, val))

    if st.button("🔍 Apply Filters", type="primary"):
        filtered = df.copy()

        if search:
            text_cols = get_categorical_columns(df)
            mask = pd.Series(False, index=filtered.index)
            for c in text_cols:
                mask = mask | filtered[c].str.contains(search, case=False, na=False)
            filtered = filtered[mask]

        masks = []
        for fc, op, val in filters:
            if op == '=': m = filtered[fc] == val
            elif op == '!=': m = filtered[fc] != val
            elif op == '>': m = filtered[fc] > val
            elif op == '<': m = filtered[fc] < val
            elif op == '>=': m = filtered[fc] >= val
            elif op == '<=': m = filtered[fc] <= val
            elif op == 'contains': m = filtered[fc].astype(str).str.contains(str(val), case=False, na=False)
            else: m = pd.Series(True, index=filtered.index)
            masks.append(m)

        if masks:
            combined = masks[0]
            for m in masks[1:]:
                combined = (combined & m) if logic == "AND" else (combined | m)
            filtered = filtered[combined]

        st.success(f"**{len(filtered):,}** rows matched (out of {len(df):,})")
        st.dataframe(filtered.head(200), use_container_width=True, hide_index=True)
        st.download_button("📥 Download", filtered.to_csv(index=False), "filtered.csv", "text/csv")

with tab3:
    st.markdown('<div class="section-label">Column Profile</div>', unsafe_allow_html=True)
    summary_df = get_column_summary_df(metadata)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    num_cols = get_numeric_columns(df)
    if len(num_cols) >= 2:
        st.markdown('<div class="section-label">Correlations</div>', unsafe_allow_html=True)
        corr = df[num_cols].corr().round(3)
        fig = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', template=CHART_TEMPLATE)
        fig.update_layout(height=450, margin=dict(t=20, b=20, l=20, r=20), font=dict(family="Inter"))
        st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
