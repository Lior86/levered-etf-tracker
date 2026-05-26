import pandas as pd
import numpy as np
from config import VOLATILITY_WINDOW, MAX_DRAWDOWN_THRESHOLD


def calculate_drawdown(prices: pd.DataFrame) -> pd.DataFrame:
    rolling_peak = prices.cummax()
    drawdown = (prices - rolling_peak) / rolling_peak
    return drawdown


def get_current_drawdown(prices: pd.DataFrame) -> dict:
    drawdown_df = calculate_drawdown(prices)
    clean = drawdown_df.dropna(how='all')
    if clean.empty:
        return {ticker: 0.0 for ticker in prices.columns}
    latest = clean.iloc[-1]
    result = {}
    for ticker in prices.columns:
        try:
            dd = float(latest[ticker])
        except:
            dd = 0.0
        result[ticker] = round(dd, 4)
    return result


def calculate_volatility(prices: pd.DataFrame) -> pd.DataFrame:
    daily_returns = prices.pct_change().dropna()
    vol = daily_returns.rolling(window=VOLATILITY_WINDOW).std() * np.sqrt(252)
    return vol


def get_current_volatility(prices: pd.DataFrame) -> dict:
    vol_df = calculate_volatility(prices)
    clean = vol_df.dropna(how='all')
    if clean.empty:
        return {ticker: 0.0 for ticker in prices.columns}
    latest = clean.iloc[-1]
    result = {}
    for ticker in prices.columns:
        try:
            v = float(latest[ticker])
        except:
            v = 0.0
        result[ticker] = round(v, 4)
    return result


def calculate_vwap(prices: pd.DataFrame, volume: pd.DataFrame) -> pd.DataFrame:
    dollar_volume = prices * volume
    rolling_dollar_vol = dollar_volume.rolling(window=VOLATILITY_WINDOW).sum()
    rolling_volume = volume.rolling(window=VOLATILITY_WINDOW).sum()
    vwap = rolling_dollar_vol / rolling_volume
    return vwap


def get_vwap_signal(prices: pd.DataFrame, volume: pd.DataFrame) -> dict:
    vwap_df = calculate_vwap(prices, volume)
    result = {}
    for ticker in prices.columns:
        try:
            current_price = float(prices[ticker].dropna().iloc[-1])
            current_vwap = float(vwap_df[ticker].dropna().iloc[-1])
            distance = (current_price - current_vwap) / current_vwap
            signal = "ABOVE ↑" if distance > 0 else "BELOW ↓"
            result[ticker] = {
                "vwap": round(current_vwap, 2),
                "signal": signal,
                "distance_pct": round(distance * 100, 2)
            }
        except:
            result[ticker] = {"vwap": 0.0, "signal": "N/A", "distance_pct": 0.0}
    return result


def calculate_max_drawdown(prices: pd.DataFrame) -> dict:
    drawdown_df = calculate_drawdown(prices)
    result = {}
    for ticker in prices.columns:
        try:
            result[ticker] = round(float(drawdown_df[ticker].min()), 4)
        except:
            result[ticker] = 0.0
    return result


def get_risk_alerts(prices: pd.DataFrame) -> list:
    alerts = []
    current_dd = get_current_drawdown(prices)
    for ticker, dd in current_dd.items():
        if abs(dd) >= MAX_DRAWDOWN_THRESHOLD:
            alerts.append(
                f"⚠️  ALERT: {ticker} is down {abs(dd)*100:.1f}% from peak "
                f"(threshold: {MAX_DRAWDOWN_THRESHOLD*100:.0f}%)"
            )
    return alerts