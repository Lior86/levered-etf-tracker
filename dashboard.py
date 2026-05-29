import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

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

st.set_page_config(
    page_title="Leveraged ETF Tracker",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 16px;
        border-left: 3px solid #7c3aed;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Leveraged ETF Risk Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%A, %B %d %Y — %I:%M %p')}")

@st.cache_data(ttl=900)
def load_data():
    return fetch_all()

with st.spinner("Fetching market data..."):
    prices, volume, current_prices = load_data()

# Flatten MultiIndex columns if present
if isinstance(prices.columns, pd.MultiIndex):
    prices.columns = prices.columns.get_level_values(0)
if isinstance(volume.columns, pd.MultiIndex):
    volume.columns = volume.columns.get_level_values(0)

# Keep only our tickers
prices = prices[[t for t in TICKERS if t in prices.columns]].dropna(how='all')
volume = volume[[t for t in TICKERS if t in volume.columns]].dropna(how='all')

current_drawdowns = get_current_drawdown(prices)
current_vol = get_current_volatility(prices)
vwap_signals = get_vwap_signal(prices, volume)
max_drawdowns = calculate_max_drawdown(prices)
alerts = get_risk_alerts(prices)
rebalance_needed = needs_rebalancing(current_prices)
rebalance_instructions = get_rebalance_instructions(current_prices)
current_weights = calculate_current_weights(current_prices)

if alerts:
    for alert in alerts:
        st.markdown(f'<div style="background-color:#450a0a;border:1px solid #dc2626;border-radius:8px;padding:12px;margin:8px 0;">🚨 {alert}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="background-color:#052e16;border:1px solid #16a34a;border-radius:8px;padding:12px;">✅ All positions within risk thresholds</div>', unsafe_allow_html=True)

if rebalance_needed:
    st.warning("🔄 Rebalancing required — drift threshold exceeded on one or more positions")

st.divider()

st.subheader("Current Prices")
cols = st.columns(len(TICKERS))

for i, ticker in enumerate(TICKERS):
    price = current_prices.get(ticker, 0)
    dd = current_drawdowns.get(ticker, 0)
    with cols[i]:
        st.metric(
            label=ticker,
            value=f"${price:.2f}",
            delta=f"{dd*100:.1f}% from peak",
            delta_color="normal" if abs(dd) < MAX_DRAWDOWN_THRESHOLD else "inverse"
        )

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Price History (Normalized)")
    try:
        first_valid = prices.dropna().iloc[0]
        normalized = (prices / first_valid) * 100
        fig = go.Figure()
        colors = ["#7c3aed", "#0ea5e9", "#f59e0b"]
        for i, ticker in enumerate(TICKERS):
            if ticker in normalized.columns:
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
    except Exception as e:
        st.error(f"Chart error: {e}")

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

st.subheader("Rolling Drawdown")
try:
    drawdown_df = calculate_drawdown(prices) * 100
    fig3 = go.Figure()
    colors = ["#7c3aed", "#0ea5e9", "#f59e0b"]
    for i, ticker in enumerate(TICKERS):
        if ticker in drawdown_df.columns:
            fig3.add_trace(go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df[ticker],
                name=ticker,
                line=dict(color=colors[i], width=1.5)
            ))
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
except Exception as e:
    st.error(f"Drawdown chart error: {e}")

st.subheader("Risk Metrics")
risk_data = []
for ticker in TICKERS:
    vwap = vwap_signals.get(ticker, {"vwap": 0, "signal": "N/A", "distance_pct": 0})
    risk_data.append({
        "Ticker": ticker,
        "Current Price": f"${current_prices.get(ticker, 0):.2f}",
        "Current Drawdown": f"{current_drawdowns.get(ticker, 0)*100:.1f}%",
        "Max Drawdown (1Y)": f"{max_drawdowns.get(ticker, 0)*100:.1f}%",
        "Volatility (Ann.)": f"{current_vol.get(ticker, 0)*100:.1f}%",
        "VWAP": f"${vwap['vwap']:.2f}",
        "vs VWAP": f"{vwap['distance_pct']:+.1f}% {vwap['signal']}",
    })
risk_df = pd.DataFrame(risk_data)
st.dataframe(risk_df, use_container_width=True, hide_index=True)

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

st.divider()
st.caption("Data via Yahoo Finance · Built with Python + Streamlit · For personal use only — not financial advice")