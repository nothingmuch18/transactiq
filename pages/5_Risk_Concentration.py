"""Risk & Concentration — HHI, volatility, market dominance analysis."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Risk & Concentration", page_icon="📈", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})
amount_col = roles.get('amount')

from src.risk_analyzer import compute_risk_summary, compute_concentration_metrics, compute_volatility_index
from src.utils import format_currency, format_number, safe_divide

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#7c3aed", "#0d9488", "#3b82f6", "#ec4899", "#f59e0b"]

st.markdown("""
<div class="page-header">
    <h1>📈 Risk & Concentration</h1>
    <div class="page-subtitle">Market concentration, volatility metrics, and composite risk scoring</div>
</div>
""", unsafe_allow_html=True)

if not amount_col:
    st.error("No amount column detected.")
    st.stop()

risk = compute_risk_summary(df, metadata)

# Risk KPIs
c1, c2, c3, c4 = st.columns(4)
risk_idx = risk.get('risk_index', 0)
color = 'kpi-success' if risk_idx < 30 else ('kpi-warning' if risk_idx < 60 else 'kpi-danger')
c1.metric("Risk Index", f"{risk_idx}/100", risk.get('risk_level', ''))
c2.metric("Concentration (HHI)", f"{risk.get('hhi', 0):.0f}")

status_col = roles.get('status')
fraud_col = roles.get('fraud')
if status_col:
    failed = len(df[df[status_col] == 'FAILED'])
    c3.metric("Failure Rate", f"{safe_divide(failed, len(df)) * 100:.2f}%")
if fraud_col:
    c4.metric("Fraud Rate", f"{safe_divide(int(df[fraud_col].sum()), len(df)) * 100:.4f}%")

st.divider()

# Dimension selector
cat_dims = [roles.get('region'), roles.get('category')]
cat_dims = [d for d in cat_dims if d]
bank_cols = [c for c in df.columns if 'bank' in c.lower()]
cat_dims.extend(bank_cols[:2])
cat_dims = list(dict.fromkeys(cat_dims))  # deduplicate

if cat_dims:
    dimension = st.selectbox("Analyze concentration by:", cat_dims)
else:
    dimension = df.columns[0]

# Concentration Analysis
st.markdown('<div class="section-label">Market Concentration</div>', unsafe_allow_html=True)

group_values = df.groupby(dimension)[amount_col].sum().sort_values(ascending=False).reset_index()
group_values.columns = ['Entity', 'Total Value']
total = group_values['Total Value'].sum()
group_values['Share %'] = (group_values['Total Value'] / total * 100).round(2)
group_values['Cumulative %'] = group_values['Share %'].cumsum().round(2)

hhi_result = compute_concentration_metrics(df, dimension, amount_col)

col1, col2 = st.columns(2)
with col1:
    st.write(f"**HHI Index:** {hhi_result.get('hhi', 0):.0f} ({hhi_result.get('concentration_level', 'N/A')})")
    st.write(f"**Top entity:** {group_values['Entity'].iloc[0]} ({group_values['Share %'].iloc[0]:.1f}%)")
    top3 = group_values['Share %'].head(3).sum()
    st.write(f"**Top 3 share:** {top3:.1f}%")

    st.dataframe(group_values.head(15), use_container_width=True, hide_index=True)

with col2:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=group_values['Entity'].head(15), y=group_values['Share %'].head(15),
                         name='Share %', marker_color=CHART_COLORS[0]))
    fig.add_trace(go.Scatter(x=group_values['Entity'].head(15), y=group_values['Cumulative %'].head(15),
                             name='Cumulative %', line=dict(color=CHART_COLORS[1], width=2),
                             yaxis='y2'))
    fig.update_layout(
        yaxis2=dict(overlaying='y', side='right', range=[0, 105], title='Cumulative %'),
        height=380, template=CHART_TEMPLATE, margin=dict(t=20, b=20, l=20, r=40),
        font=dict(family="Inter"), xaxis_title="", yaxis_title="Share %",
        legend=dict(orientation='h', y=1.1)
    )
    st.plotly_chart(fig, use_container_width=True)

# Volatility Analysis
st.markdown('<div class="section-label">Monthly Volatility</div>', unsafe_allow_html=True)
date_col = roles.get('date')
if date_col:
    vol = compute_volatility_index(df, date_col, amount_col)
    if vol:
        c1, c2, c3 = st.columns(3)
        c1.metric("CV (Coefficient of Variation)", f"{vol.get('volatility_cv', 0):.1f}%")
        c2.metric("Monthly Std Dev", format_currency(vol.get('monthly_std', 0)))
        c3.metric("Monthly Mean", format_currency(vol.get('monthly_mean', 0)))

        monthly = df.set_index(date_col).resample('M')[amount_col].sum().reset_index()
        monthly.columns = ['Month', 'Value']
        fig = px.line(monthly, x='Month', y='Value', markers=True,
                     template=CHART_TEMPLATE, color_discrete_sequence=[CHART_COLORS[0]])
        fig.update_layout(height=300, margin=dict(t=20, b=20, l=20, r=20),
                         font=dict(family="Inter"), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
