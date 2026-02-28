"""Predictions & Scenarios — Forecasting and what-if simulation."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Predictions", page_icon="🔮", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata
roles = metadata.get('roles', {})

from src.predictor import forecast_monthly
from src.scenario_engine import simulate_scenario, get_available_scenarios
from src.utils import format_currency, format_number

CHART_TEMPLATE = "plotly_white"
CHART_COLORS = ["#4f46e5", "#7c3aed", "#10b981", "#ef4444", "#f59e0b"]

st.markdown("""
<div class="page-header">
    <h1>🔮 Predictions & Scenarios</h1>
    <div class="page-subtitle">Trend forecasting and what-if simulation — statistical models, not black-box ML</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📈 Forecast", "🎯 Scenario Simulation"])

with tab1:
    st.markdown('<div class="section-label">Monthly Value Forecast</div>', unsafe_allow_html=True)

    forecast_months = st.slider("Forecast horizon (months)", 1, 6, 3)

    with st.spinner("Building forecast model..."):
        result = forecast_monthly(df, metadata, forecast_months=forecast_months)

    if 'error' in result:
        st.error(result['error'])
    else:
        # Metrics
        metrics = result['metrics']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("RMSE", format_currency(metrics['rmse']))
        c2.metric("MAE", format_currency(metrics['mae']))
        c3.metric("Train Size", f"{metrics['train_size']} months")
        c4.metric("Test Size", f"{metrics['test_size']} months")

        # Chart
        hist = result['historical_df']
        fc = result['forecast_df']

        fig = go.Figure()

        # Historical actual
        fig.add_trace(go.Scatter(
            x=hist['Month'], y=hist['Actual'], mode='lines+markers',
            name='Actual', line=dict(color=CHART_COLORS[0], width=2),
            marker=dict(size=5)
        ))

        # Fitted
        fig.add_trace(go.Scatter(
            x=hist['Month'], y=hist['Fitted'], mode='lines',
            name='Fitted', line=dict(color=CHART_COLORS[2], dash='dash', width=1.5)
        ))

        # Forecast
        fig.add_trace(go.Scatter(
            x=fc['Month'], y=fc['Predicted'], mode='lines+markers',
            name='Forecast', line=dict(color=CHART_COLORS[1], width=2),
            marker=dict(size=6, symbol='diamond')
        ))

        # Confidence interval
        fig.add_trace(go.Scatter(
            x=pd.concat([fc['Month'], fc['Month'][::-1]]),
            y=pd.concat([fc['Upper (95%)'], fc['Lower (95%)'][::-1]]),
            fill='toself', fillcolor='rgba(124, 58, 237, 0.08)',
            line=dict(width=0), name='95% CI', showlegend=True
        ))

        fig.update_layout(
            height=420, template=CHART_TEMPLATE,
            margin=dict(t=20, b=20, l=20, r=20), font=dict(family="Inter"),
            xaxis_title="", yaxis_title="Value", legend=dict(orientation='h', y=1.08)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Explanation
        st.markdown(f"""
        <div class="explanation-box">
            <p>{result['explanation']}</p>
        </div>
        """, unsafe_allow_html=True)

        # Forecast table
        with st.expander("📋 Forecast Details"):
            st.dataframe(fc, use_container_width=True, hide_index=True)
            st.markdown("**Model Details:**")
            info = result['model_info']
            st.write(f"- **Method:** {info['method']}")
            st.write(f"- **Trend:** {info['trend_direction']}")
            st.write(f"- **Peak Month:** {info['peak_seasonal_month']}")

with tab2:
    st.markdown('<div class="section-label">What-If Simulation</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="result-box">
        <span style="font-size:0.88rem;">Adjust parameters below to simulate hypothetical scenarios and see their projected impact on key metrics.</span>
    </div>
    """, unsafe_allow_html=True)

    available = get_available_scenarios(metadata)
    if not available:
        st.warning("No scenarios available for this dataset.")
    else:
        scenario = st.selectbox("Scenario", list(available.keys()),
                               format_func=lambda x: available[x]['label'])

        info = available[scenario]
        if info['param'] == 'percentage':
            param_val = st.slider(info['description'], 1, 50, info['default'])
        else:
            param_val = st.slider(info['description'], 0.01, 10.0, float(info['default']), 0.01)

        if st.button("🎯 Run Simulation", type="primary"):
            with st.spinner("Simulating..."):
                sim = simulate_scenario(df, metadata, scenario, param_val)

            if 'error' in sim:
                st.error(sim['error'])
            else:
                st.markdown(f"""
                <div class="explanation-box">
                    <p>{sim['explanation']}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown('<div class="section-label">Before vs After</div>', unsafe_allow_html=True)
                st.dataframe(sim['comparison_df'], use_container_width=True, hide_index=True)

                # Chart
                comp = sim['comparison_df']
                fig = px.bar(comp, x='Metric', y=['Before', 'After'], barmode='group',
                            template=CHART_TEMPLATE, color_discrete_sequence=CHART_COLORS)
                fig.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20),
                                 font=dict(family="Inter"), xaxis_title="", yaxis_title="")
                st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
