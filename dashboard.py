# =============================================================================
# dashboard.py — The Terminal Screen
# =============================================================================
# This is what you actually LOOK at every morning.
# Built with Streamlit — a Python library that turns Python scripts into
# web dashboards without writing any HTML/CSS/JavaScript.
#
# To run this: streamlit run dashboard.py
# It opens automatically in your browser at http://localhost:8501
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Import our own modules
from data_fetcher import fetch_all
from risk_engine import (
    get_current_drawdown,
    get_current_volatility,
    get_vwap_signal,
    calculate_drawdown,
    calculate_max_drawdown,
    get_risk_alerts
)
from rebalancer import (
    calculate_current_weights,
    calculate_drift,
    get_rebalance_instructions,
    needs_rebalancing
)
from config import TARGET_WEIGHTS, PORTFOLIO_VALUE, MAX_DRAWDOWN_THRESHOLD, TICKERS

# =============================================================================
# PAGE SETUP
# =============================================================================
st.set_page_config(
    page_title="Leveraged ETF Tracker",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for a cleaner dark theme
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 16px;
        border-left: 3px solid #7c3aed;
    }
    .alert-box {
        background-color: #450a0a;
        border: 1px solid #dc2626;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .ok-box {
        background-color: #052e16;
        border: 1px solid #16a34a;
        border-radius: 8px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================
st.title("📊 Leveraged ETF Risk Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%A, %B %d %Y — %I:%M %p')}")

# =============================================================================
# DATA LOADING
# =============================================================================
# st.cache_data means: don't re-fetch data on every click, cache it for 15 min
@st.cache_data(ttl=900)
def load_data():
    return fetch_all()

with st.spinner("Fetching market data..."):
    prices, volume, current_prices = load_data()

# Calculate all metrics
current_drawdowns = get_current_drawdown(prices)
current_vol = get_current_volatility(prices)
vwap_signals = get_vwap_signal(prices, volume)
max_drawdowns = calculate_max_drawdown(prices)
alerts = get_risk_alerts(prices)
rebalance_needed = needs_rebalancing(current_prices)
rebalance_instructions = get_rebalance_instructions(current_prices)
current_weights = calculate_current_weights(current_prices)

# =============================================================================
# RISK ALERTS BANNER
# =============================================================================
if alerts:
    for alert in alerts:
        st.markdown(f'<div class="alert-box">🚨 {alert}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="ok-box">✅ All positions within risk thresholds</div>', unsafe_allow_html=True)

if rebalance_needed:
    st.warning(f"🔄 Rebalancing required — drift threshold exceeded on one or more positions")

st.divider()

# =============================================================================
# TOP METRICS ROW — Current Prices
# =============================================================================
st.subheader("Current Prices")
cols = st.columns(len(TICKERS))

for i, ticker in enumerate(TICKERS):
    price = current_prices[ticker]
    dd = current_drawdowns[ticker]
    dd_color = "normal" if abs(dd) < MAX_DRAWDOWN_THRESHOLD else "inverse"

    with cols[i]:
        st.metric(
            label=ticker,
            value=f"${price:.2f}",
            delta=f"{dd*100:.1f}% from peak",
            delta_color=dd_color
        )

st.divider()

# =============================================================================
# MAIN CHARTS ROW
# =============================================================================
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Price History (Normalized)")
    # Normalize prices to 100 at start — shows relative performance
    normalized = (prices / prices.iloc[0]) * 100

    fig = go.Figure()
    colors = ["#7c3aed", "#0ea5e9", "#f59e0b"]

    for i, ticker in enumerate(TICKERS):
        fig.add_trace(go.Scatter(
            x=normalized.index,
            y=normalized[ticker],
            name=ticker,
            line=dict(color=colors[i], width=2)
        ))

    fig.update_layout(
        template="plotly_dark",
        yaxis_title="Indexed Value (Start = 100)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=0, r=0, t=30, b=0),
        height=350
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Portfolio Weights")
    labels = list(current_weights.keys())
    values = [current_weights[t] * 100 for t in labels]
    targets = [TARGET_WEIGHTS[t] * 100 for t in labels]

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(name="Current", x=labels, y=values, marker_color="#7c3aed"))
    fig2.add_trace(go.Bar(name="Target", x=labels, y=targets, marker_color="#374151"))

    fig2.update_layout(
        template="plotly_dark",
        barmode="group",
        yaxis_title="Weight (%)",
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02)
    )
    st.plotly_chart(fig2, use_container_width=True)

# =============================================================================
# DRAWDOWN CHART
# =============================================================================
st.subheader("Rolling Drawdown")
drawdown_df = calculate_drawdown(prices) * 100  # convert to percentage

fig3 = go.Figure()
for i, ticker in enumerate(TICKERS):
    fig3.add_trace(go.Scatter(
        x=drawdown_df.index,
        y=drawdown_df[ticker],
        name=ticker,
        line=dict(color=colors[i], width=1.5),
        fill="tozeroy",
        fillcolor=colors[i].replace(")", ", 0.1)").replace("rgb", "rgba") if "rgb" in colors[i] else colors[i]
    ))

# Add threshold line
fig3.add_hline(
    y=-MAX_DRAWDOWN_THRESHOLD * 100,
    line_dash="dash",
    line_color="red",
    annotation_text=f"Alert threshold (-{MAX_DRAWDOWN_THRESHOLD*100:.0f}%)"
)

fig3.update_layout(
    template="plotly_dark",
    yaxis_title="Drawdown (%)",
    margin=dict(l=0, r=0, t=30, b=0),
    height=300
)
st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# RISK METRICS TABLE
# =============================================================================
st.subheader("Risk Metrics")

risk_data = []
for ticker in TICKERS:
    vwap = vwap_signals[ticker]
    risk_data.append({
        "Ticker": ticker,
        "Current Price": f"${current_prices[ticker]:.2f}",
        "Current Drawdown": f"{current_drawdowns[ticker]*100:.1f}%",
        "Max Drawdown (1Y)": f"{max_drawdowns[ticker]*100:.1f}%",
        "Volatility (Ann.)": f"{current_vol[ticker]*100:.1f}%",
        "VWAP": f"${vwap['vwap']:.2f}",
        "vs VWAP": f"{vwap['distance_pct']:+.1f}% {vwap['signal']}",
    })

risk_df = pd.DataFrame(risk_data)
st.dataframe(risk_df, use_container_width=True, hide_index=True)

# =============================================================================
# REBALANCING SECTION
# =============================================================================
st.subheader("Rebalancing")

if rebalance_instructions:
    st.warning("The following trades would restore your target allocation:")
    for inst in rebalance_instructions:
        action_color = "🔴" if inst["action"].strip() == "SELL" else "🟢"
        st.markdown(
            f"{action_color} **{inst['action'].strip()} {inst['ticker']}** — "
            f"${inst['dollar_amount']:,.0f} "
            f"(current: {inst['current_weight']}% → target: {inst['target_weight']}%, "
            f"drift: {inst['drift_pct']:+.1f}%)"
        )
else:
    st.success("✅ All positions within drift threshold — no rebalancing needed today")

# =============================================================================
# FOOTER
# =============================================================================
st.divider()
st.caption("Data via Yahoo Finance · Built with Python + Streamlit · For personal use only — not financial advice")
