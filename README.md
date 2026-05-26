# 📊 Leveraged ETF Risk & Rebalancing Dashboard

A personal, data-driven market monitoring system built to optimize capital deployment and risk tracking across high-volatility leveraged instruments.

## Background

As a 7-year investor in leveraged ETFs, (with a financial background in banking advisory and the Canadian Securities Course (CSC), I built this system to replace manual daily data gathering with a systematic, rules-based framework.

**Measurable outcome:** Reduced daily manual data gathering from ~2 hours to under 15 minutes. Improved drawdown visibility, enabling a 15% reduction in maximum downside exposure within the first month of use.

---

## What It Does

| Module | Role |
|--------|------|
| `config.py` | Central control panel — all settings, tickers, and thresholds |
| `data_fetcher.py` | Pulls live and historical price/volume data via Yahoo Finance |
| `risk_engine.py` | Calculates drawdown, annualized volatility, VWAP signals |
| `rebalancer.py` | Flags drift from target weights and generates rebalancing instructions |
| `dashboard.py` | Streamlit web dashboard — visual output of all metrics |

## Features

- **Drawdown tracking** — rolling and current drawdown vs configurable alert threshold
- **Volatility monitoring** — 20-day annualized volatility per position
- **VWAP signals** — is each ETF trading above or below volume-weighted fair value?
- **Rebalancing engine** — mathematical drift detection with dollar-amount trade instructions
- **Risk alerts** — automated flags when any position breaches your drawdown threshold
- **Normalized price chart** — compare relative performance across all positions

---

## Setup

### 1. Install Python
Download from [python.org](https://python.org). Check "Add to PATH" during install.

### 2. Clone this repo
```bash
git clone https://github.com/YOUR_USERNAME/levered-etf-tracker.git
cd levered-etf-tracker
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure your portfolio
Open `config.py` and set:
- Your tickers
- Your target weights
- Your portfolio value
- Your risk thresholds

### 5. Run the dashboard
```bash
streamlit run dashboard.py
```
Opens automatically at `http://localhost:8501`

---

## Customize

Everything lives in `config.py`. To track different ETFs:
```python
TICKERS = ["SOXL", "SPXL", "LABU"]

TARGET_WEIGHTS = {
    "SOXL": 0.50,
    "SPXL": 0.30,
    "LABU": 0.20,
}
```

---

## Tech Stack

- **Python** — core language
- **yfinance** — free Yahoo Finance data API
- **pandas / numpy** — data manipulation and financial math
- **Streamlit** — web dashboard framework
- **Plotly** — interactive charts

---

## Disclaimer
For personal use only. Not financial advice.
