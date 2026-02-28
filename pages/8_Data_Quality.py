"""Data Quality — Comprehensive quality assessment."""
import streamlit as st
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Data Quality", page_icon="🧹", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata

from src.data_quality import run_quality_checks

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#ef4444", "#f59e0b", "#10b981"]

st.markdown("""
<div class="page-header">
    <h1>🧹 Data Quality</h1>
    <div class="page-subtitle">Comprehensive quality assessment — missing values, duplicates, outliers, and consistency</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Running quality checks..."):
    results = run_quality_checks(df, metadata)

score = results.get('quality_score', 0)
grade = results.get('quality_grade', 'N/A')
color = '#10b981' if score >= 90 else '#f59e0b' if score >= 75 else '#ef4444'

# Quality Score Card
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f"""
<div class="kpi-card" style="border-top: 3px solid {color};">
    <div class="kpi-label">Quality Score</div>
    <div class="kpi-value" style="color:{color};">{score}/100</div>
</div>
""", unsafe_allow_html=True)
c2.metric("Grade", grade)
c3.metric("Total Records", f"{len(df):,}")
c4.metric("Total Columns", str(len(df.columns)))

st.divider()

# Missing Values
st.markdown('<div class="section-label">Missing Values</div>', unsafe_allow_html=True)
missing = results['missing_values']
if len(missing['df']) > 0:
    st.dataframe(missing['df'], use_container_width=True, hide_index=True)
    fig = px.bar(missing['df'], x='Column', y='Missing Count', template=CHART_TEMPLATE,
                color='Missing %', color_continuous_scale='Reds')
    fig.update_layout(height=280, margin=dict(t=20, b=20, l=20, r=20), font=dict(family="Inter"))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.markdown('<div class="success-alert">✅ No missing values found.</div>', unsafe_allow_html=True)

# Duplicates
st.markdown('<div class="section-label">Duplicates</div>', unsafe_allow_html=True)
dups = results['duplicates']
st.metric("Exact Duplicate Rows", dups['exact_duplicates'])

# Negative Values
st.markdown('<div class="section-label">Negative Values</div>', unsafe_allow_html=True)
neg = results['negative_values']
if neg['found']:
    st.dataframe(neg['df'], use_container_width=True, hide_index=True)
else:
    st.markdown('<div class="success-alert">✅ No negative values detected.</div>', unsafe_allow_html=True)

# Extreme Outliers
st.markdown('<div class="section-label">Extreme Outliers (>4σ)</div>', unsafe_allow_html=True)
outliers = results['extreme_outliers']
if outliers['found']:
    st.dataframe(outliers['df'], use_container_width=True, hide_index=True)
else:
    st.markdown('<div class="success-alert">✅ No extreme outliers detected.</div>', unsafe_allow_html=True)

# Consistency
st.markdown('<div class="section-label">Consistency Checks</div>', unsafe_allow_html=True)
consistency = results['consistency']
if consistency['found']:
    st.dataframe(consistency['df'], use_container_width=True, hide_index=True)
else:
    st.markdown('<div class="success-alert">✅ No consistency issues found.</div>', unsafe_allow_html=True)

# Download Report
st.divider()
lines = [
    f"Data Quality Report",
    f"Score: {score}/100 ({grade})",
    f"Records: {len(df):,}",
    f"Missing cells: {missing['total_missing']} ({missing['overall_pct']}%)",
    f"Duplicate rows: {dups['exact_duplicates']}",
    f"Negative columns: {len(results['negative_values']['df'])}",
    f"Outlier columns: {len(results['extreme_outliers']['df'])}",
    f"Consistency issues: {len(results['consistency']['df'])}",
]
st.download_button("📥 Download Quality Report", "\n".join(lines), "quality_report.txt", "text/plain")

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
