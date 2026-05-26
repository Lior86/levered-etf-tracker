# =============================================================================
# risk_engine.py — The Risk Manager
# =============================================================================
# This is the brain of the system.
# It takes raw price/volume data and produces the metrics you actually care about:
#
#   - Drawdown: How far are you from your peak? (your "pain number")
#   - Volatility: How wildly is each ETF moving right now?
#   - VWAP: Volume-Weighted Average Price — are you above or below fair value?
#   - Sharpe-like score: Are you being compensated for the risk you're taking?
#
# Everything here is math on DataFrames — no external APIs needed.
# =============================================================================

import pandas as pd
import numpy as np
from config import VOLATILITY_WINDOW, MAX_DRAWDOWN_THRESHOLD


def calculate_drawdown(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Drawdown = how far each ETF has fallen from its highest point.

    Example: TQQQ peaked at $80. It's now at $68.
             Drawdown = (68 - 80) / 80 = -15%

    Returns a DataFrame of the same shape as prices, but with drawdown %
    instead of dollar values. Negative numbers = below peak.
    """
    # Rolling maximum: for each day, what was the highest price up to that day?
    rolling_peak = prices.cummax()

    # Drawdown = (current price - peak) / peak
    drawdown = (prices - rolling_peak) / rolling_peak

    return drawdown


def get_current_drawdown(prices: pd.DataFrame) -> dict:
    """
    Returns TODAY's drawdown for each ticker as a clean dictionary.
    Example: {"TQQQ": -0.08, "TNA": -0.13, "UDOW": -0.04}
    Negative = below peak. 0.0 = at all-time high.
    """
    drawdown_df = calculate_drawdown(prices)
    latest = drawdown_df.iloc[-1]  # last row = today

    result = {}
    for ticker in prices.columns:
        dd = latest[ticker]
        result[ticker] = round(dd, 4)

    return result


def calculate_volatility(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Volatility = how much does this ETF move day-to-day?
    We use 'annualized volatility' — the standard on trading desks.

    Steps:
    1. Calculate daily % returns (today's price vs yesterday's)
    2. Take the rolling standard deviation over VOLATILITY_WINDOW days
    3. Annualize it (multiply by sqrt(252) — there are 252 trading days/year)

    Higher number = wilder swings = more risk (and potential reward).
    TQQQ will always be higher than a normal ETF. That's expected.
    """
    # Daily returns: (today - yesterday) / yesterday
    daily_returns = prices.pct_change().dropna()

    # Rolling std dev, annualized
    vol = daily_returns.rolling(window=VOLATILITY_WINDOW).std() * np.sqrt(252)

    return vol


def get_current_volatility(prices: pd.DataFrame) -> dict:
    """Returns today's annualized volatility for each ticker."""
    vol_df = calculate_volatility(prices)
    latest = vol_df.iloc[-1]

    result = {}
    for ticker in prices.columns:
        result[ticker] = round(latest[ticker], 4)

    return result


def calculate_vwap(prices: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    """
    VWAP = Volume-Weighted Average Price
    The 'true' average price weighted by how much was traded at each price.

    Trading insight:
    - Price ABOVE VWAP = buying pressure, bullish signal
    - Price BELOW VWAP = selling pressure, bearish signal
    - We calculate a rolling 20-day VWAP for trend context
    """
    # Dollar volume = price × volume traded
    dollar_volume = prices * volume

    # Rolling VWAP = sum(dollar volume) / sum(volume) over the window
    rolling_dollar_vol = dollar_volume.rolling(window=VOLATILITY_WINDOW).sum()
    rolling_volume = volume.rolling(window=VOLATILITY_WINDOW).sum()

    vwap = rolling_dollar_vol / rolling_volume

    return vwap


def get_vwap_signal(prices: pd.DataFrame, volume: pd.DataFrame) -> dict:
    """
    Returns a signal for each ticker: are we above or below VWAP?
    Also returns the % distance from VWAP.
    Example: {"TQQQ": {"signal": "ABOVE", "distance_pct": 2.3}}
    """
    vwap_df = calculate_vwap(prices, volume)

    result = {}
    for ticker in prices.columns:
        current_price = prices[ticker].iloc[-1]
        current_vwap = vwap_df[ticker].iloc[-1]

        distance = (current_price - current_vwap) / current_vwap
        signal = "ABOVE ↑" if distance > 0 else "BELOW ↓"

        result[ticker] = {
            "vwap": round(current_vwap, 2),
            "signal": signal,
            "distance_pct": round(distance * 100, 2)
        }

    return result


def calculate_max_drawdown(prices: pd.DataFrame) -> dict:
    """
    The worst single peak-to-trough drop over the entire history.
    This is the number that should keep you humble about leverage.
    """
    drawdown_df = calculate_drawdown(prices)
    result = {}
    for ticker in prices.columns:
        result[ticker] = round(drawdown_df[ticker].min(), 4)  # min = worst drop
    return result


def get_risk_alerts(prices: pd.DataFrame) -> list:
    """
    Checks your current drawdown against MAX_DRAWDOWN_THRESHOLD from config.py
    Returns a list of alert strings — empty list means you're in the clear.
    """
    alerts = []
    current_dd = get_current_drawdown(prices)

    for ticker, dd in current_dd.items():
        if abs(dd) >= MAX_DRAWDOWN_THRESHOLD:
            alerts.append(
                f"⚠️  ALERT: {ticker} is down {abs(dd)*100:.1f}% from peak "
                f"(threshold: {MAX_DRAWDOWN_THRESHOLD*100:.0f}%)"
            )

    return alerts


# --- TEST: Run this file directly ---
# In your terminal: python risk_engine.py
if __name__ == "__main__":
    from data_fetcher import fetch_all

    prices, volume, current = fetch_all()

    print("\n📉 Current Drawdowns:")
    for ticker, dd in get_current_drawdown(prices).items():
        print(f"   {ticker}: {dd*100:.2f}%")

    print("\n📊 Current Volatility (annualized):")
    for ticker, vol in get_current_volatility(prices).items():
        print(f"   {ticker}: {vol*100:.1f}%")

    print("\n📈 VWAP Signals:")
    for ticker, data in get_vwap_signal(prices, volume).items():
        print(f"   {ticker}: {data['signal']} VWAP by {data['distance_pct']}%")

    print("\n🔴 Worst Historical Drawdowns:")
    for ticker, dd in calculate_max_drawdown(prices).items():
        print(f"   {ticker}: {dd*100:.1f}%")

    alerts = get_risk_alerts(prices)
    if alerts:
        print("\n⚠️  RISK ALERTS:")
        for alert in alerts:
            print(f"   {alert}")
    else:
        print("\n✅ No risk alerts — all positions within threshold")
