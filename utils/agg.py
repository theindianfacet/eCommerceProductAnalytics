import pandas as pd
import numpy as np

def filter_sessions(sessions: pd.DataFrame, F: dict) -> pd.DataFrame:
    df = sessions.copy()
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["website_session_id"])
    df = df[(df["created_at"] >= F["start_ts"]) & (df["created_at"] <= F["end_ts"])]

    for col, key in [
        ("utm_source","utm_source"), ("utm_campaign","utm_campaign"),
        ("utm_content","utm_content"), ("device_type","device_type"),
        ("http_referer","http_referer")
    ]:
        vals = F.get(key, [])
        if vals and col in df.columns:
            df = df[df[col].isin(vals)]

    df = df.drop_duplicates(subset=["website_session_id"])
    return df

def filter_pageviews(pvs: pd.DataFrame, F: dict) -> pd.DataFrame:
    df = pvs.copy()
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["website_session_id"])
    df = df[(df["created_at"] >= F["start_ts"]) & (df["created_at"] <= F["end_ts"])]
    purls = F.get("pageview_urls", [])
    if purls and "pageview_url" in df.columns:
        df = df[df["pageview_url"].isin(purls)]
    return df

def filter_orders(orders: pd.DataFrame, F: dict) -> pd.DataFrame:
    df = orders.copy()
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df[(df["created_at"] >= F["start_ts"]) & (df["created_at"] <= F["end_ts"])]
    return df

def filter_order_items(items: pd.DataFrame, products: pd.DataFrame, F: dict) -> pd.DataFrame:
    df = items.copy()
    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df[(df["created_at"] >= F["start_ts"]) & (df["created_at"] <= F["end_ts"])]
    df = df.merge(products[["product_id","product_name"]], on="product_id", how="left")
    prods = F.get("product_names", [])
    if prods and "product_name" in df.columns:
        df = df[df["product_name"].isin(prods)]
    return df

def rollup(df: pd.DataFrame, ts_col: str, granularity: str) -> pd.DataFrame:
    out = df.copy()
    out[ts_col] = pd.to_datetime(out[ts_col], errors="coerce")
    out = out.dropna(subset=[ts_col])
    out["date"] = out[ts_col].dt.normalize()

    if granularity == "Daily":
        out["bucket"] = out["date"]
    elif granularity == "Weekly":
        out["bucket"] = out["date"] - pd.to_timedelta(out["date"].dt.weekday, unit="d")
    elif granularity == "Monthly":
        out["bucket"] = out["date"].values.astype("datetime64[M]")
        out["bucket"] = pd.to_datetime(out["bucket"])
    elif granularity == "Yearly":
        out["bucket"] = out["date"].dt.year
    else:
        out["bucket"] = out["date"]
    return out

def compute_bounce_rate(sessions: pd.DataFrame, pageviews: pd.DataFrame) -> float:
    pv_counts = (
        pageviews.groupby("website_session_id", dropna=False)
        .size()
        .rename("pv_count")
        .reset_index()
    )
    sess = sessions.merge(pv_counts, on="website_session_id", how="left").fillna({"pv_count": 0})
    total = len(sess)
    if total == 0:
        return np.nan
    single = (sess["pv_count"] == 1).sum()
    return float(single) / total

def compute_conversion_rate(sessions: pd.DataFrame, orders: pd.DataFrame) -> float:
    valid_session_ids = set(sessions["website_session_id"])
    ordered_sessions = set(orders["website_session_id"].dropna())
    conversions = len(valid_session_ids.intersection(ordered_sessions))
    total_sessions = len(valid_session_ids)
    return float(conversions) / total_sessions if total_sessions > 0 else np.nan

def revenue_metrics(orders: pd.DataFrame, refunds: pd.DataFrame, sessions: pd.DataFrame):
    gross_rev = float(orders["price_usd"].sum()) if "price_usd" in orders.columns else 0.0
    refund_amt = float(refunds["refund_amount_usd"].sum()) if "refund_amount_usd" in refunds.columns else 0.0
    net_rev = gross_rev - refund_amt

    if "is_repeat_session" in sessions.columns:
        new_sessions = sessions[sessions["is_repeat_session"] == False]
        repeat_sessions = sessions[sessions["is_repeat_session"] == True]
    else:
        new_sessions = sessions
        repeat_sessions = sessions.iloc[0:0]

    total_sessions = len(sessions)
    new_rev_per_session = net_rev / len(new_sessions) if len(new_sessions) > 0 else np.nan
    repeat_rev_per_session = net_rev / len(repeat_sessions) if len(repeat_sessions) > 0 else np.nan
    rev_per_session = net_rev / total_sessions if total_sessions > 0 else np.nan

    return {
        "gross_revenue": gross_rev,
        "refunds": refund_amt,
        "net_revenue": net_rev,
        "revenue_per_session": rev_per_session,
        "rev_per_session_new": new_rev_per_session,
        "rev_per_session_repeat": repeat_rev_per_session,
    }

def gsearch_metrics(sessions: pd.DataFrame, orders: pd.DataFrame):
    g_sessions = sessions[sessions["utm_source"] == "gsearch"]
    g_ids = set(g_sessions["website_session_id"])
    ordered_ids = set(orders["website_session_id"].dropna())
    g_conv = len(g_ids.intersection(ordered_ids)) / len(g_sessions) if len(g_sessions) > 0 else np.nan
    return {"gsearch_conversion_rate": g_conv, "gsearch_sessions": len(g_sessions)}

def hour_weekday_session_volume(sessions: pd.DataFrame):
    s = sessions.copy()
    s["created_at"] = pd.to_datetime(s["created_at"], errors="coerce")
    s["hour"] = s["created_at"].dt.hour
    s["weekday"] = s["created_at"].dt.day_name()
    by_hour = s.groupby("hour").size().rename("sessions").reset_index()
    by_weekday = s.groupby("weekday").size().rename("sessions").reset_index()
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    by_weekday["weekday"] = pd.Categorical(by_weekday["weekday"], categories=order, ordered=True)
    by_weekday = by_weekday.sort_values("weekday")
    return by_hour, by_weekday