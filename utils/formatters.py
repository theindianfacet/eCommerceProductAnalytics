import pandas as pd

def format_number(n) -> str:
    """Format large numbers with K/M notation."""
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return f"{n:.0f}"

def format_currency(n) -> str:
    """Format currency with commas and $ sign."""
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    return f"${n:,.0f}"

def format_currency_precise(n) -> str:
    """Currency with 2 decimals (for per-session metrics)."""
    if n is None or pd.isna(n):
        return "—"
    n = float(n)
    return f"${n:,.2f}"

def format_percent(p) -> str:
    """
    Format percentage with two decimals.
    Expects proportions (0–1). If a value >1 is passed, assume it's already a percent.
    """
    if p is None or pd.isna(p):
        return "—"
    p = float(p)
    if p > 1:  
        return f"{p:.2f}%"
    return f"{p*100:.2f}%"

def format_km(value) -> str:
    """Format numbers with K/M notation (custom thresholds)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 10_000:   
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:,.0f}"