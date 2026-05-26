# =============================================================================
# config.py — Your Control Panel
# =============================================================================
# This is the ONLY file you need to edit to customize the system.
# All your personal settings, tickers, and rules live here.
# The other files READ from this file — they never hardcode values themselves.
# =============================================================================

# --- YOUR PORTFOLIO -----------------------------------------------------------
# Add or remove tickers here. The rest of the system updates automatically.
TICKERS = ["TQQQ", "TNA", "UDOW"]

# How much of your portfolio is in each ETF (must add up to 1.0 = 100%)
# Example below: equal weight across all three
TARGET_WEIGHTS = {
    "TQQQ": 0.40,   # 40% — Nasdaq heavy, your core position
    "TNA":  0.30,   # 30% — Small cap exposure
    "UDOW": 0.30,   # 30% — Blue chip stability
}

# --- RISK RULES ---------------------------------------------------------------
# Maximum drawdown you're willing to tolerate before getting an alert
# 0.15 = 15% drop from peak triggers a warning
MAX_DRAWDOWN_THRESHOLD = 0.15

# If any single position drifts this far from its target weight, flag it
# 0.05 = 5% drift (e.g. TQQQ target is 40%, alert if it hits 45% or 35%)
REBALANCE_DRIFT_THRESHOLD = 0.05

# How many days of history to pull for analysis
LOOKBACK_DAYS = 365

# Volatility window: how many days to use when calculating rolling volatility
VOLATILITY_WINDOW = 20  # 20 trading days ≈ 1 month

# --- DISPLAY SETTINGS ---------------------------------------------------------
# Currency symbol for display
CURRENCY = "CAD"

# Your approximate total portfolio value (used for dollar-value calculations)
# Change this to your actual number
PORTFOLIO_VALUE = 50000
