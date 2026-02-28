"""Insights — Auto-generated financial intelligence with explainability."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="Insights", page_icon="💡", layout="wide")

if 'df' not in st.session_state or st.session_state.df is None:
    st.warning("Please load a dataset from the main page first.")
    st.stop()

df = st.session_state.df
metadata = st.session_state.metadata

from src.insight_engine import generate_insights

st.markdown("""
<div class="page-header">
    <h1>💡 Financial Insights</h1>
    <div class="page-subtitle">Auto-generated intelligence from your data — each insight includes a "Why?" explanation</div>
</div>
""", unsafe_allow_html=True)

with st.spinner("Analyzing data..."):
    insights = generate_insights(df, metadata)

# Category filter
categories = sorted(set(i.get('category', 'other') for i in insights))
selected = st.selectbox("Filter by category", ['All'] + categories)

if selected != 'All':
    insights = [i for i in insights if i.get('category') == selected]

CATEGORY_COLORS = {
    'overview': '#4f46e5', 'growth': '#10b981', 'timing': '#f59e0b',
    'concentration': '#7c3aed', 'category': '#ec4899', 'distribution': '#0d9488',
    'risk': '#ef4444', 'fraud': '#dc2626', 'pattern': '#3b82f6',
}

for idx, ins in enumerate(insights):
    color = CATEGORY_COLORS.get(ins.get('category', ''), '#4f46e5')
    badge_html = f'<span class="insight-card-badge" style="background:{color}12; color:{color};">{ins.get("category", "general")}</span>'

    st.markdown(f"""
    <div class="insight-card" style="border-left-color: {color};">
        <div class="insight-card-title">{ins.get('icon', '📊')} {ins['title']}{badge_html}</div>
        <div class="insight-card-body">{ins['description']}</div>
    </div>
    """, unsafe_allow_html=True)

    why = ins.get('why', '')
    if why:
        with st.expander(f"🤔 Why? — {ins['title']}", expanded=False):
            st.markdown(f"**Reasoning:** {why}")

st.markdown("---")
st.caption(f"✅ {len(insights)} insights · {len(df):,} records analyzed")

# Download
lines = []
for i, ins in enumerate(insights):
    lines.append(f"{i+1}. {ins.get('icon', '')} {ins['title']}")
    lines.append(f"   {ins['description']}")
    if ins.get('why'): lines.append(f"   Why: {ins['why']}")
    lines.append("")
st.download_button("📥 Download Report", "\n".join(lines), "insights.txt", "text/plain")

st.markdown('<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Zero Hallucination Engine</div>', unsafe_allow_html=True)
