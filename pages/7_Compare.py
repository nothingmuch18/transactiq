"""Compare — Side-by-side analysis of groups and time periods."""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Compare", page_icon="⚖️", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})
amount_col = roles.get('amount')
date_col = roles.get('date')

from src.comparator import compare_groups, compare_time_periods, get_available_comparisons
from src.utils import format_currency

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#ec4899"]

st.markdown("""
<div class="page-header">
    <h1>⚖️ Comparative Analysis</h1>
    <div class="page-subtitle">Compare two groups, periods, or categories side by side</div>
</div>
""", unsafe_allow_html=True)

if not amount_col:
    st.error("No amount column detected.")
    st.stop()

comparisons = get_available_comparisons(df, metadata)
if not comparisons:
    st.warning("No comparable dimensions found.")
    st.stop()

dim_name = st.selectbox("Dimension", list(comparisons.keys()))
dim_info = comparisons[dim_name]
values = dim_info['values']

c1, c2 = st.columns(2)
with c1:
    group_a = st.selectbox(f"Group A ({dim_name})", values, index=0)
with c2:
    group_b = st.selectbox(f"Group B ({dim_name})", values, index=min(1, len(values) - 1))

if group_a == group_b:
    st.warning("Select two different groups.")
    st.stop()

if st.button("🔍 Compare", type="primary"):
    with st.spinner("Computing..."):
        if dim_name in ('Months', 'Quarters'):
            result = compare_time_periods(df, date_col, amount_col, group_a, group_b)
        else:
            result = compare_groups(df, dim_info['column'], group_a, group_b, amount_col, metadata)

    if result is None:
        st.error(f"No data for '{group_a}' or '{group_b}'.")
        st.stop()

    st.divider()

    # Explanation
    st.markdown(f"""
    <div class="explanation-box">
        <p>{result['explanation']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Comparison Table
    st.markdown('<div class="section-label">Detailed Comparison</div>', unsafe_allow_html=True)
    st.dataframe(result['comparison_df'], use_container_width=True, hide_index=True)

    # Chart
    chart_data = result.get('chart_data')
    if chart_data is not None and len(chart_data) > 0:
        st.markdown('<div class="section-label">Visual Comparison</div>', unsafe_allow_html=True)
        value_cols = [c for c in chart_data.columns if c != 'Metric']
        melt = chart_data.melt(id_vars='Metric', value_vars=value_cols,
                              var_name='Group', value_name='Value')
        fig = px.bar(melt, x='Metric', y='Value', color='Group', barmode='group',
                    template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
        fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20),
                         font=dict(family="Inter"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    csv = result['comparison_df'].to_csv(index=False)
    st.download_button("📥 Download Comparison", csv, "comparison.csv", "text/csv")

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
