"""Executive Overview — KPIs, growth metrics, comprehensive summary."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})
amount_col = roles.get('amount')
date_col = roles.get('date')
region_col = roles.get('region')

from src.utils import format_currency, format_number, safe_divide
from src.risk_analyzer import compute_risk_summary
from src.data_profiler import get_descriptive_stats

# Page Header
st.markdown("""
<div class="page-header">
    <h1>📊 Executive Overview</h1>
    <div class="page-subtitle">Key performance indicators, growth trends, and dataset summary</div>
</div>
""", unsafe_allow_html=True)

if not amount_col:
    st.error("No amount column detected.")
    st.stop()

risk = compute_risk_summary(df, metadata)
status_col = roles.get('status')
fraud_col = roles.get('fraud')

# Row 1: Primary KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Transactions", format_number(len(df)))
c2.metric("Total Value", format_currency(df[amount_col].sum()))
c3.metric("Avg Transaction", format_currency(df[amount_col].mean()))

if date_col:
    monthly = df.set_index(date_col).resample('M')[amount_col].sum()
    if len(monthly) >= 2:
        last_growth = ((monthly.iloc[-1] / monthly.iloc[-2]) - 1) * 100
        c4.metric("Last Month Growth", f"{last_growth:+.1f}%")
    else:
        c4.metric("Months of Data", str(len(monthly)))

c5.metric("Risk Index", f"{risk.get('risk_index', 0)}/100", risk.get('risk_level', ''))

# Row 2: Secondary KPIs
c6, c7, c8, c9 = st.columns(4)
if status_col:
    total = len(df)
    failed = len(df[df[status_col] == 'FAILED'])
    c6.metric("Success Rate", f"{safe_divide(total - failed, total) * 100:.1f}%")
    c7.metric("Failed Txns", format_number(failed))
if fraud_col:
    fraud_count = int(df[fraud_col].sum())
    c8.metric("Fraud Flagged", format_number(fraud_count))
    c9.metric("Fraud Rate", f"{safe_divide(fraud_count, len(df)) * 100:.4f}%")

if date_col:
    dr = metadata.get('date_range', {})
    st.caption(f"📅 {dr.get('start', 'N/A')} → {dr.get('end', 'N/A')} · {dr.get('months', '?')} months of data")

st.divider()

# Charts Row 1
st.markdown('<div class="section-label">Trends & Distribution</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#7c3aed", "#0d9488", "#3b82f6", "#ec4899", "#f59e0b", "#10b981", "#ef4444"]

with col1:
    if date_col:
        monthly_data = df.set_index(date_col).resample('M').agg({amount_col: ['sum', 'count']}).reset_index()
        monthly_data.columns = ['Month', 'Total Value', 'Volume']
        fig = px.line(monthly_data, x='Month', y='Total Value',
                     title="Monthly Transaction Value",
                     markers=True, template=CHART_TEMPLATE,
                     color_discrete_sequence=[CHART_COLORS[0]])
        fig.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20),
                         font=dict(family="Inter"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if region_col:
        top_states = df.groupby(region_col)[amount_col].sum().nlargest(10).reset_index()
        top_states.columns = ['State', 'Total Value']
        fig = px.bar(top_states, x='Total Value', y='State', orientation='h',
                    title="Top 10 States",
                    template=CHART_TEMPLATE, color_discrete_sequence=[CHART_COLORS[0]])
        fig.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20),
                         font=dict(family="Inter"), yaxis={'categoryorder': 'total ascending'},
                         xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

# Charts Row 2
col3, col4 = st.columns(2)

with col3:
    cat_col = roles.get('category')
    if cat_col:
        cat_data = df.groupby(cat_col)[amount_col].sum().reset_index()
        cat_data.columns = ['Category', 'Total Value']
        fig = px.pie(cat_data, values='Total Value', names='Category',
                    title="Value by Category", hole=0.45,
                    template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
        fig.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20),
                         font=dict(family="Inter"))
        st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.histogram(df, x=amount_col, nbins=30,
                      title="Value Distribution",
                      template=CHART_TEMPLATE, color_discrete_sequence=[CHART_COLORS[2]])
    fig.update_layout(height=340, margin=dict(t=40, b=20, l=20, r=20),
                     font=dict(family="Inter"), xaxis_title="", yaxis_title="Count")
    st.plotly_chart(fig, use_container_width=True)

# Descriptive Statistics
st.markdown('<div class="section-label">Descriptive Statistics</div>', unsafe_allow_html=True)
stats_df = get_descriptive_stats(df, metadata)
if len(stats_df) > 0:
    st.dataframe(stats_df, use_container_width=True)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
