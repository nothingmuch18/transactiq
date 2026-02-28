"""
UPI Data Intelligence Platform — Main Streamlit Application
Premium AI-powered analytics engine for UPI financial transaction data.
"""
import streamlit as st
import pandas as pd
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_profiler import load_and_profile

# --- Page Config ---
st.set_page_config(
    page_title="UPI Intelligence Platform",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# PREMIUM DESIGN SYSTEM — Fintech SaaS Grade CSS
# =====================================================
PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== GLOBAL RESET ===== */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    .main .block-container {
        padding: 2rem 2.5rem 3rem;
        max-width: 1280px;
    }

    /* ===== COLOR TOKENS ===== */
    :root {
        --bg-primary: #fafbfd;
        --bg-card: #ffffff;
        --bg-sidebar: #0c0f1a;
        --bg-sidebar-hover: #161b2e;
        --bg-code: #f4f5f7;
        --bg-accent-subtle: #f0f2ff;
        --bg-success-subtle: #ecfdf5;
        --bg-warning-subtle: #fffbeb;
        --bg-danger-subtle: #fef2f2;

        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #94a3b8;
        --text-inverse: #f8fafc;

        --border-default: #e2e8f0;
        --border-subtle: #f1f5f9;

        --accent-primary: #4f46e5;
        --accent-primary-hover: #4338ca;
        --accent-secondary: #7c3aed;
        --accent-teal: #0d9488;
        --accent-blue: #3b82f6;

        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --danger-soft: #f87171;

        --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 2px 8px rgba(0,0,0,0.06);
        --shadow-lg: 0 4px 16px rgba(0,0,0,0.08);
        --shadow-xl: 0 8px 32px rgba(0,0,0,0.10);

        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --radius-xl: 20px;
    }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0c0f1a 0%, #111827 100%);
        border-right: 1px solid #1e293b;
    }
    [data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stFileUploader label {
        color: #94a3b8 !important;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1e293b;
    }

    /* ===== TYPOGRAPHY ===== */
    h1 {
        font-weight: 800 !important;
        font-size: 1.75rem !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.5px;
        line-height: 1.2 !important;
    }
    h2 {
        font-weight: 700 !important;
        font-size: 1.35rem !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.3px;
        line-height: 1.3 !important;
    }
    h3 {
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        color: var(--text-secondary) !important;
        letter-spacing: -0.2px;
    }
    p, li, span, div {
        color: var(--text-secondary);
        line-height: 1.6;
    }

    /* ===== METRIC CARDS (Streamlit native) ===== */
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        padding: 1rem 1.25rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    [data-testid="stMetric"] label {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-muted) !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        color: var(--text-primary) !important;
    }

    /* ===== DATAFRAME ===== */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        overflow: hidden;
    }

    /* ===== BUTTONS ===== */
    .stButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.15s ease !important;
        border: 1px solid var(--border-default) !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }
    .stButton > button:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent-primary) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-primary-hover) !important;
        color: white !important;
    }

    /* ===== INPUTS ===== */
    .stTextInput > div > div > input {
        border-radius: var(--radius-sm) !important;
        border: 1.5px solid var(--border-default) !important;
        padding: 0.65rem 1rem !important;
        font-size: 0.9rem !important;
        transition: border-color 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-primary) !important;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
    }
    .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
    }

    /* ===== EXPANDER ===== */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        color: var(--text-primary) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-default) !important;
        border-radius: var(--radius-md) !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 2px solid var(--border-subtle);
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.75rem 1.25rem;
        color: var(--text-muted);
        border-bottom: 2px solid transparent;
        margin-bottom: -2px;
    }
    .stTabs [aria-selected="true"] {
        color: var(--accent-primary) !important;
        border-bottom-color: var(--accent-primary) !important;
    }

    /* ===== INFO/WARNING/SUCCESS/ERROR ===== */
    .stAlert {
        border-radius: var(--radius-md) !important;
        border: none !important;
    }

    /* ===== DIVIDER ===== */
    hr {
        border: none;
        border-top: 1px solid var(--border-subtle);
        margin: 1.5rem 0;
    }

    /* ===== DOWNLOAD BUTTON ===== */
    .stDownloadButton > button {
        border-radius: var(--radius-sm) !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        background: var(--bg-accent-subtle) !important;
        color: var(--accent-primary) !important;
        border: 1px solid rgba(79, 70, 229, 0.2) !important;
    }

    /* ===== CUSTOM COMPONENT CLASSES ===== */

    /* Page Header */
    .page-header {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-subtle);
    }
    .page-header h1 {
        margin: 0 !important;
        padding: 0 !important;
    }
    .page-subtitle {
        font-size: 0.9rem;
        color: var(--text-muted);
        margin-top: 0.25rem;
        font-weight: 400;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0c0f1a 0%, #1e1b4b 50%, #312e81 100%);
        padding: 2rem 2.5rem;
        border-radius: var(--radius-xl);
        color: white;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-banner h1 {
        color: white !important;
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .hero-banner p {
        color: #a5b4fc !important;
        font-size: 0.95rem;
        margin: 0.4rem 0 0 0;
        font-weight: 400;
    }

    /* KPI Card (custom) */
    .kpi-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        padding: 1.25rem 1.5rem;
        border-radius: var(--radius-md);
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    .kpi-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: var(--text-muted);
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--text-primary);
        line-height: 1.1;
    }
    .kpi-accent { color: var(--accent-primary); }
    .kpi-success { color: var(--success); }
    .kpi-warning { color: var(--warning); }
    .kpi-danger { color: var(--danger); }

    /* Insight Card */
    .insight-card {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        border-left: 3px solid var(--accent-primary);
        padding: 1.1rem 1.4rem;
        border-radius: var(--radius-md);
        margin-bottom: 0.75rem;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    .insight-card:hover {
        box-shadow: var(--shadow-md);
    }
    .insight-card-title {
        font-weight: 700;
        font-size: 0.95rem;
        color: var(--text-primary);
        margin-bottom: 0.35rem;
    }
    .insight-card-body {
        font-size: 0.88rem;
        color: var(--text-secondary);
        line-height: 1.65;
    }
    .insight-card-badge {
        display: inline-block;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 2px 8px;
        border-radius: 4px;
        margin-left: 8px;
        vertical-align: middle;
    }

    /* Result Box */
    .result-box {
        background: var(--bg-accent-subtle);
        border: 1px solid rgba(79, 70, 229, 0.12);
        padding: 1rem 1.3rem;
        border-radius: var(--radius-md);
        margin: 0.75rem 0;
    }

    /* Explanation Box */
    .explanation-box {
        background: linear-gradient(135deg, #f0f2ff 0%, #faf5ff 100%);
        border: 1px solid rgba(79, 70, 229, 0.1);
        border-left: 3px solid var(--accent-primary);
        padding: 1rem 1.3rem;
        border-radius: var(--radius-md);
        margin: 0.75rem 0;
    }
    .explanation-box p {
        color: var(--text-secondary) !important;
        font-size: 0.9rem;
        line-height: 1.7;
    }

    /* Warning Alert */
    .risk-alert {
        background: var(--bg-danger-subtle);
        border: 1px solid rgba(239, 68, 68, 0.15);
        border-left: 3px solid var(--danger);
        padding: 0.9rem 1.2rem;
        border-radius: var(--radius-md);
        margin: 0.6rem 0;
    }

    /* Success Alert */
    .success-alert {
        background: var(--bg-success-subtle);
        border: 1px solid rgba(16, 185, 129, 0.15);
        border-left: 3px solid var(--success);
        padding: 0.9rem 1.2rem;
        border-radius: var(--radius-md);
    }

    /* Execution Meta */
    .exec-meta {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--bg-code);
        padding: 0.3rem 0.8rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted);
        font-family: 'SF Mono', 'Fira Code', monospace;
    }

    /* Plan Box */
    .plan-box {
        background: #0f172a;
        color: #a5f3fc;
        padding: 1.1rem 1.3rem;
        border-radius: var(--radius-md);
        font-family: 'SF Mono', 'Fira Code', monospace;
        font-size: 0.82rem;
        line-height: 1.7;
        overflow-x: auto;
    }

    /* Nav Grid */
    .nav-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .nav-item {
        background: var(--bg-card);
        border: 1px solid var(--border-default);
        padding: 1.1rem;
        border-radius: var(--radius-md);
        text-align: center;
        transition: all 0.2s ease;
        cursor: default;
    }
    .nav-item:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--accent-primary);
    }
    .nav-item-icon {
        font-size: 1.5rem;
        margin-bottom: 0.3rem;
    }
    .nav-item-title {
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--text-primary);
    }
    .nav-item-desc {
        font-size: 0.7rem;
        color: var(--text-muted);
        margin-top: 0.15rem;
    }

    /* Section Label */
    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted);
        margin-bottom: 0.75rem;
        margin-top: 1.5rem;
    }

    /* Footer */
    .data-footer {
        font-size: 0.72rem;
        color: var(--text-muted);
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-subtle);
    }

    /* Plotly chart container override */
    .js-plotly-plot {
        border: 1px solid var(--border-default);
        border-radius: var(--radius-md);
        overflow: hidden;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
"""

st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def render_kpi(label, value, color_class=""):
    """Render a premium KPI card."""
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {color_class}">{value}</div>
    </div>
    """


def render_page_header(title, subtitle=""):
    """Render a standard page header."""
    sub = f'<div class="page-subtitle">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="page-header">
        <h1>{title}</h1>
        {sub}
    </div>
    """


def render_explanation(text):
    """Render an explanation box."""
    return f"""
    <div class="explanation-box">
        <p>{text}</p>
    </div>
    """


def render_insight(icon, title, body, category="", border_color="#4f46e5"):
    """Render a premium insight card."""
    badge = f'<span class="insight-card-badge" style="background:{border_color}15; color:{border_color};">{category}</span>' if category else ""
    return f"""
    <div class="insight-card" style="border-left-color: {border_color};">
        <div class="insight-card-title">{icon} {title}{badge}</div>
        <div class="insight-card-body">{body}</div>
    </div>
    """


def render_footer():
    """Render standard data footer."""
    return '<div class="data-footer">Data Source: UPI Transactions 2024 (Synthetic) · Built with Streamlit · Zero Hallucination Engine</div>'


def auto_load_data():
    """Auto-load dataset on startup."""
    if 'df' in st.session_state and st.session_state.df is not None:
        return st.session_state.df, st.session_state.metadata

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if csv_files:
            filepath = os.path.join(data_dir, csv_files[0])
            load_start = time.time()
            df, metadata = load_and_profile(filepath)
            load_time = round((time.time() - load_start) * 1000, 0)
            st.session_state.df = df
            st.session_state.metadata = metadata
            st.session_state.load_time_ms = load_time
            return df, metadata
    return None, None


# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0 0.8rem;">
        <div style="font-size:1.3rem; font-weight:800; color:#e2e8f0 !important; letter-spacing:-0.5px;">🧠 UPI Intelligence</div>
        <div style="font-size:0.7rem; color:#64748b !important; font-weight:500; letter-spacing:0.5px; text-transform:uppercase; margin-top:2px;">AI Analytics Engine</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # Data source controls
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if csv_files:
            st.selectbox("Dataset", csv_files, key="sidebar_dataset")
            if st.button("↻ Reload", use_container_width=True):
                filepath = os.path.join(data_dir, csv_files[0])
                with st.spinner("Loading..."):
                    load_start = time.time()
                    df, metadata = load_and_profile(filepath)
                    st.session_state.df = df
                    st.session_state.metadata = metadata
                    st.session_state.load_time_ms = round((time.time() - load_start) * 1000, 0)
                    st.rerun()

    uploaded = st.file_uploader("Upload CSV", type=['csv'])
    if uploaded:
        with st.spinner("Profiling..."):
            df_up = pd.read_csv(uploaded)
            load_start = time.time()
            df_up, meta = load_and_profile(df_up)
            st.session_state.df = df_up
            st.session_state.metadata = meta
            st.session_state.load_time_ms = round((time.time() - load_start) * 1000, 0)
            st.rerun()

    if 'load_time_ms' in st.session_state:
        st.caption(f"⚡ Loaded in {st.session_state.load_time_ms:.0f}ms")


# =====================================================
# AUTO LOAD DATA
# =====================================================
df, metadata = auto_load_data()


# =====================================================
# MAIN PAGE CONTENT
# =====================================================
st.markdown("""
<div class="hero-banner">
    <h1>🧠 UPI Data Intelligence Platform</h1>
    <p>AI-powered analytics engine — Ask anything about your UPI transaction data</p>
</div>
""", unsafe_allow_html=True)

if df is None:
    st.info("👈 **Upload a CSV** or place a file in the `data/` folder to get started.")
    st.markdown("""
    ### Capabilities
    | Feature | Description |
    |---------|-------------|
    | 🧠 Ask AI | Natural language → structured analytics |
    | 📊 Overview | Executive KPIs and growth metrics |
    | 🔍 Explore | Multi-condition filter & search |
    | 💡 Insights | Auto-generated financial intelligence |
    | ⚠️ Anomalies | IQR, Z-score, percentile detection |
    | 📈 Risk | Concentration, volatility, HHI index |
    | ⚖️ Compare | Side-by-side group analysis |
    | 🔮 Predict | Trend forecasting & what-if simulation |
    """)
else:
    from src.utils import format_currency, format_number
    roles = metadata.get('roles', {})
    amount_col = roles.get('amount')

    # KPI Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(render_kpi("Total Transactions", format_number(len(df))), unsafe_allow_html=True)
    with c2:
        if amount_col:
            st.markdown(render_kpi("Total Value", format_currency(df[amount_col].sum()), "kpi-accent"), unsafe_allow_html=True)
    with c3:
        if amount_col:
            st.markdown(render_kpi("Avg Transaction", format_currency(df[amount_col].mean())), unsafe_allow_html=True)
    with c4:
        date_range = metadata.get('date_range', {})
        months = date_range.get('months', len(df.columns))
        st.markdown(render_kpi("Data Span", f"{months} months"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Dataset Info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-label">Column Roles Detected</div>', unsafe_allow_html=True)
        for role, col_name in roles.items():
            st.write(f"**{role}** → `{col_name}`")
    with col2:
        st.markdown('<div class="section-label">Dataset Profile</div>', unsafe_allow_html=True)
        date_col = roles.get('date')
        if date_col:
            dr = metadata.get('date_range', {})
            st.write(f"📅 **Range:** {dr.get('start', 'N/A')} → {dr.get('end', 'N/A')}")
        st.write(f"📊 **Shape:** {len(df):,} rows × {len(df.columns)} columns")
        st.write(f"🔄 **Duplicates:** {metadata.get('duplicate_rows', 0)}")
        st.write(f"⚠️ **Missing:** {sum(df.isnull().sum())} cells")

    st.divider()

    # Navigation Grid
    st.markdown('<div class="section-label">Quick Navigation</div>', unsafe_allow_html=True)

    nav = [
        ("📊", "Executive Overview", "KPIs & trends"),
        ("🧠", "Ask AI", "Natural language queries"),
        ("🔍", "Explore Data", "Filter & aggregate"),
        ("💡", "Insights", "Auto-generated intelligence"),
        ("📈", "Risk Analysis", "Concentration & volatility"),
        ("⚠️", "Anomalies", "Multi-method detection"),
        ("⚖️", "Compare", "Side-by-side analysis"),
        ("🧹", "Data Quality", "Quality assessment"),
        ("🔮", "Predictions", "Forecasting & scenarios"),
        ("📖", "Documentation", "Architecture & docs"),
    ]

    nav_html = '<div class="nav-grid">'
    for icon, title, desc in nav:
        nav_html += f'''
        <div class="nav-item">
            <div class="nav-item-icon">{icon}</div>
            <div class="nav-item-title">{title}</div>
            <div class="nav-item-desc">{desc}</div>
        </div>'''
    nav_html += '</div>'
    st.markdown(nav_html, unsafe_allow_html=True)

    st.markdown(render_footer(), unsafe_allow_html=True)
