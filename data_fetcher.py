# =============================================================================
# data_fetcher.py — The Analyst
# =============================================================================
# This file's ONE job: go get data.
# It connects to Yahoo Finance (free, no API key needed) and pulls:
#   - Daily closing prices
#   - Volume data
#   - Current price
# It returns clean pandas DataFrames — think of these like Excel tables in Python.
# =============================================================================

import yfinance as yf          # connects to Yahoo Finance
import pandas as pd            # pandas = Excel for Python
from datetime import datetime, timedelta
from config import TICKERS, LOOKBACK_DAYS


def fetch_price_history():
    """
    Pull historical daily closing prices for all tickers.
    Returns a DataFrame where:
        - Each ROW is a date
        - Each COLUMN is a ticker (TQQQ, TNA, UDOW)
        - Each CELL is the closing price that day
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    print(f"📡 Fetching {LOOKBACK_DAYS} days of price history for: {', '.join(TICKERS)}")

    # Download all tickers at once — yfinance handles the API calls
    raw = yf.download(
        tickers=TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,       # adjusts for splits and dividends automatically
        progress=False          # suppresses the download progress bar
    )

    # Extract just the closing prices
    prices = raw["Close"]

    # Drop any days where data is missing (holidays, weekends already excluded)
    prices = prices.dropna()

    print(f"✅ Got {len(prices)} trading days of data")
    return prices


def fetch_volume_history():
    """
    Pull historical daily volume for all tickers.
    Volume tells you how 'serious' a price move is.
    High volume + big move = conviction. Low volume + big move = suspect.
    """
    end_date = datetime.today()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    raw = yf.download(
        tickers=TICKERS,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False
    )

    volume = raw["Volume"].dropna()
    return volume


def fetch_current_prices():
    """
    Pull today's current price for each ticker.
    Returns a simple dictionary: {"TQQQ": 52.34, "TNA": 28.11, "UDOW": 74.20}
    """
    print("📡 Fetching current prices...")
    current = {}

    for ticker in TICKERS:
        data = yf.Ticker(ticker)
        # 'fast_info' is the quickest way to get today's price
        price = data.fast_info["last_price"]
        current[ticker] = round(price, 2)
        print(f"   {ticker}: ${price:.2f}")

    return current


def fetch_all():
    """
    Convenience function: fetch everything at once.
    Returns a tuple: (prices_df, volume_df, current_prices_dict)
    Call this from other files instead of calling each function separately.
    """
    prices = fetch_price_history()
    volume = fetch_volume_history()
    current = fetch_current_prices()
    return prices, volume, current


# --- TEST: Run this file directly to make sure data is coming in correctly ---
# In your terminal: python data_fetcher.py
if __name__ == "__main__":
    prices, volume, current = fetch_all()
    print("\n📊 Last 5 days of closing prices:")
    print(prices.tail())
    print("\n📦 Current prices:")
    for ticker, price in current.items():
        print(f"   {ticker}: ${price:.2f}")
