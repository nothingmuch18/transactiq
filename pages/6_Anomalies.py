"""Anomalies — Multi-method detection with adjustable thresholds."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Anomalies", page_icon="⚠️", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})
amount_col = roles.get('amount')

from src.anomaly_detector import (
    run_full_anomaly_detection, detect_iqr_anomalies,
    detect_zscore_anomalies, detect_percentile_anomalies
)

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#ef4444", "#10b981", "#f59e0b"]

st.markdown("""
<div class="page-header">
    <h1>⚠️ Anomaly Detection</h1>
    <div class="page-subtitle">Multi-method statistical anomaly detection with adjustable sensitivity</div>
</div>
""", unsafe_allow_html=True)

if not amount_col:
    st.error("No amount column detected.")
    st.stop()

# Controls
c_method, c_thresh = st.columns([1, 2])
with c_method:
    method = st.selectbox("Method", ['all', 'iqr', 'zscore', 'percentile', 'rolling', 'growth', 'concentration'])
with c_thresh:
    iqr_mult = st.slider("IQR Multiplier", 1.0, 3.0, 1.5, 0.1) if method in ('iqr', 'all') else 1.5
    zscore_thresh = st.slider("Z-Score Threshold", 1.5, 5.0, 3.0, 0.1) if method in ('zscore', 'all') else 3.0

with st.spinner("Detecting anomalies..."):
    if method == 'iqr':
        anomalies, stats = detect_iqr_anomalies(df, amount_col, multiplier=iqr_mult)
        results = {'IQR Method': {'anomalies': anomalies, 'stats': stats, 'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies using IQR ({iqr_mult}x). Bounds: [{stats['lower']:.0f}, {stats['upper']:.0f}]"}}
    elif method == 'zscore':
        anomalies, stats = detect_zscore_anomalies(df, amount_col, threshold=zscore_thresh)
        results = {'Z-Score Method': {'anomalies': anomalies, 'stats': stats, 'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies with |Z| > {zscore_thresh}"}}
    elif method == 'percentile':
        anomalies, stats = detect_percentile_anomalies(df, amount_col)
        results = {'Percentile': {'anomalies': anomalies, 'stats': stats, 'count': len(anomalies),
            'description': f"Found {len(anomalies)} anomalies outside 1st-99th percentile"}}
    else:
        results = run_full_anomaly_detection(df, metadata, method=method)

if not results:
    st.info("No results for selected method.")
    st.stop()

total_anom = sum(r['count'] for r in results.values())
c1, c2, c3 = st.columns(3)
c1.metric("Total Anomalies", f"{total_anom:,}")
c2.metric("Methods Run", str(len(results)))
c3.metric("Anomaly Rate", f"{total_anom / len(df) * 100:.2f}%")

st.divider()

for name, result in results.items():
    with st.expander(f"**{name}** — {result['count']} detected", expanded=True):
        st.markdown(f"""
        <div class="result-box">
            <span style="font-size:0.88rem; color:var(--text-secondary);">📝 {result['description']}</span>
        </div>
        """, unsafe_allow_html=True)

        anom_df = result.get('anomalies', pd.DataFrame())
        if len(anom_df) > 0:
            display_cols = [c for c in anom_df.columns if c != 'anomaly_reason'][:8]
            if 'anomaly_reason' in anom_df.columns:
                display_cols.append('anomaly_reason')
            st.dataframe(anom_df[display_cols].head(50), use_container_width=True, hide_index=True)

            if 'daily_data' in result:
                daily = result['daily_data']
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Value'], mode='lines', name='Value',
                                        line=dict(color=CHART_COLORS[0])))
                fig.add_trace(go.Scatter(x=daily['Date'], y=daily['Rolling_Mean'], mode='lines',
                                        name='Rolling Mean', line=dict(dash='dash', color=CHART_COLORS[2])))
                if 'Date' in anom_df.columns:
                    fig.add_trace(go.Scatter(x=anom_df['Date'], y=anom_df['Value'], mode='markers',
                                            name='Anomalies', marker=dict(color=CHART_COLORS[1], size=8)))
                fig.update_layout(height=350, template=CHART_TEMPLATE, margin=dict(t=20, b=20, l=20, r=20),
                                 font=dict(family="Inter"))
                st.plotly_chart(fig, use_container_width=True)

            csv = anom_df.to_csv(index=False)
            st.download_button(f"📥 Download", csv, f"anomalies_{name.lower().replace(' ', '_')}.csv",
                             "text/csv", key=f"dl_{name}")
        else:
            st.markdown('<div class="success-alert">✅ No anomalies detected.</div>', unsafe_allow_html=True)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
