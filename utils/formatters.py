import math

def format_number(n: float) -> str:
    """Format large numbers with K/M notation."""
    if n is None or math.isnan(n):
        return "—"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    else:
        return f"{n:.0f}"

def format_currency(n: float) -> str:
    """Format currency with commas and $ sign."""
    if n is None or math.isnan(n):
        return "—"
    return f"${n:,.0f}"

def format_currency_precise(n: float) -> str:
    """Currency with 2 decimals (for per-session metrics)."""
    if n is None or math.isnan(n):
        return "—"
    return f"${n:,.2f}"

def format_percent(p: float) -> str:
    """
    Format percentage with one decimal place.
    Expects proportions (0–1). If a value >1 is passed, assume it's already a percent
    and scale accordingly.
    """
    if p is None or math.isnan(p):
        return "—"
    if p > 1:  # safeguard: treat as already a percent
        return f"{p:.2f}%"
    return f"{p*100:.2f}%"

def format_km(value):
    """Format numbers with K/M notation (custom thresholds)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "0"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 10_000:   # your intentional threshold
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:,.0f}"