# =============================================================================
# rebalancer.py — The Compliance Rule Engine
# =============================================================================
# This file answers one question: "Do I need to rebalance today?"
#
# The math: if your target weight for TQQQ is 40%, but TQQQ has run up
# and now represents 47% of your portfolio, you've drifted 7%.
# If that's above your REBALANCE_DRIFT_THRESHOLD (default: 5%), it flags it
# and tells you exactly how many dollars to buy/sell to get back on target.
#
# This is the systematic discipline that removes emotion from rebalancing.
# =============================================================================

import pandas as pd
from config import TARGET_WEIGHTS, REBALANCE_DRIFT_THRESHOLD, PORTFOLIO_VALUE


def calculate_current_weights(current_prices: dict) -> dict:
    """
    Given current prices and your target weights, calculate what your
    portfolio weights ACTUALLY are right now.

    This assumes you started with the target weights and prices have moved.
    It approximates current weights based on relative price performance.

    Returns: {"TQQQ": 0.43, "TNA": 0.28, "UDOW": 0.29}
    """
    # Calculate the dollar value of each position at current prices
    # Based on how much of your portfolio was originally allocated
    position_values = {}
    for ticker, weight in TARGET_WEIGHTS.items():
        # Original dollar allocation × (current price / original price ratio)
        # We use the weight directly as a proxy for relative value
        position_values[ticker] = weight * current_prices[ticker]

    # Total portfolio value in relative terms
    total = sum(position_values.values())

    # Convert to percentage weights
    current_weights = {
        ticker: round(val / total, 4)
        for ticker, val in position_values.items()
    }

    return current_weights


def calculate_drift(current_prices: dict) -> dict:
    """
    Drift = current weight minus target weight for each position.

    Positive drift = position has grown ABOVE target (consider trimming)
    Negative drift = position has shrunk BELOW target (consider adding)

    Returns: {"TQQQ": +0.03, "TNA": -0.02, "UDOW": -0.01}
    """
    current_weights = calculate_current_weights(current_prices)

    drift = {}
    for ticker in TARGET_WEIGHTS:
        drift[ticker] = round(current_weights[ticker] - TARGET_WEIGHTS[ticker], 4)

    return drift


def get_rebalance_instructions(current_prices: dict) -> list:
    """
    The main output of this file.
    Returns a list of actions needed to get back to target weights.

    Each action tells you:
    - Which ticker
    - Buy or Sell
    - How many dollars
    - Why (current vs target weight)
    """
    drift = calculate_drift(current_prices)
    current_weights = calculate_current_weights(current_prices)
    instructions = []

    for ticker, d in drift.items():
        abs_drift = abs(d)

        if abs_drift >= REBALANCE_DRIFT_THRESHOLD:
            direction = "SELL" if d > 0 else "BUY "
            dollar_amount = abs(d) * PORTFOLIO_VALUE
            current_w = current_weights[ticker] * 100
            target_w = TARGET_WEIGHTS[ticker] * 100

            instructions.append({
                "ticker": ticker,
                "action": direction,
                "drift_pct": round(d * 100, 2),
                "dollar_amount": round(dollar_amount, 2),
                "current_weight": round(current_w, 1),
                "target_weight": round(target_w, 1),
                "current_price": current_prices[ticker]
            })

    return instructions


def needs_rebalancing(current_prices: dict) -> bool:
    """Simple yes/no: does anything need rebalancing right now?"""
    return len(get_rebalance_instructions(current_prices)) > 0


def print_rebalance_report(current_prices: dict):
    """Pretty-print the rebalancing report to the terminal."""
    instructions = get_rebalance_instructions(current_prices)
    drift = calculate_drift(current_prices)
    current_weights = calculate_current_weights(current_prices)

    print("\n" + "="*60)
    print("📋 REBALANCING REPORT")
    print("="*60)

    print("\nCurrent vs Target Weights:")
    print(f"  {'Ticker':<8} {'Current':>10} {'Target':>10} {'Drift':>10}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10}")

    for ticker in TARGET_WEIGHTS:
        cw = current_weights[ticker] * 100
        tw = TARGET_WEIGHTS[ticker] * 100
        d = drift[ticker] * 100
        flag = " ⚠️" if abs(d) >= REBALANCE_DRIFT_THRESHOLD * 100 else ""
        print(f"  {ticker:<8} {cw:>9.1f}% {tw:>9.1f}% {d:>+9.1f}%{flag}")

    if instructions:
        print(f"\n🔄 ACTIONS REQUIRED (drift > {REBALANCE_DRIFT_THRESHOLD*100:.0f}%):")
        for inst in instructions:
            print(f"\n   {inst['action']} {inst['ticker']}")
            print(f"   Current weight: {inst['current_weight']}% → Target: {inst['target_weight']}%")
            print(f"   Drift: {inst['drift_pct']:+.1f}%  |  Amount: ${inst['dollar_amount']:,.0f}")
            print(f"   At current price ${inst['current_price']:.2f}")
    else:
        print(f"\n✅ All positions within {REBALANCE_DRIFT_THRESHOLD*100:.0f}% drift threshold — no rebalancing needed")

    print("="*60)


# --- TEST: Run this file directly ---
# In your terminal: python rebalancer.py
if __name__ == "__main__":
    from data_fetcher import fetch_current_prices
    prices = fetch_current_prices()
    print_rebalance_report(prices)
