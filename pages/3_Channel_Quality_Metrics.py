import streamlit as st
import pandas as pd
import os
import plotly.express as px
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders

st.title("🧪 Channel Quality Metrics")

F = sidebar_filters()
dfs = load_tables(["website_sessions", "orders", "website_pageviews"])
sessions = filter_sessions(dfs["website_sessions"], F)
orders = filter_orders(dfs["orders"], F)
pageviews = dfs["website_pageviews"]

sessions["month"] = pd.to_datetime(sessions["created_at"]).dt.to_period("M").dt.to_timestamp()
orders["month"]   = pd.to_datetime(orders["created_at"]).dt.to_period("M").dt.to_timestamp()
pageviews["month"] = pd.to_datetime(pageviews["created_at"]).dt.to_period("M").dt.to_timestamp()


pv_counts = (
    pageviews.groupby("website_session_id")
    .size().rename("pageviews_per_session")
    .reset_index()
)
pv_counts["is_bounce"] = (pv_counts["pageviews_per_session"] == 1).astype(int)

sess_min = sessions[["website_session_id", "utm_source", "month"]].copy()
sess_with_bounce = sess_min.merge(pv_counts[["website_session_id", "is_bounce"]], on="website_session_id", how="left")
sess_with_bounce["is_bounce"] = sess_with_bounce["is_bounce"].fillna(0).astype(int)


sess_month = sess_with_bounce.groupby(["utm_source", "month"]).agg(
    sessions=("website_session_id", "nunique"),
    bounces=("is_bounce", "sum")
).reset_index()
sess_month = sess_month[sess_month["sessions"] > 0].copy()
sess_month["bounce_rate"] = (sess_month["bounces"] / sess_month["sessions"]).clip(0, 1)


ord_month = orders.merge(
    sessions[["website_session_id", "utm_source"]],
    on="website_session_id", how="left"
).groupby(["utm_source", "month"]).agg(
    orders=("order_id", "nunique"),
    revenue=("price_usd", "sum"),
    avg_order_value=("price_usd", "mean")
).reset_index()


char_trends = sess_month.merge(ord_month, on=["utm_source", "month"], how="left")
char_trends[["orders", "revenue", "avg_order_value"]] = char_trends[["orders", "revenue", "avg_order_value"]].fillna(0)
char_trends["conversion_rate"] = (
    (char_trends["orders"] / char_trends["sessions"]).replace([float("inf")], 0).clip(0, 1)
)


st.markdown("### Bounce Rate Trend by Channel")
fig_bounce = px.line(
    char_trends, x="month", y="bounce_rate", color="utm_source",
    labels={"month": "Month", "bounce_rate": "Bounce Rate", "utm_source": "UTM Source"}
)
fig_bounce.update_yaxes(range=[0, 1], tickformat=".0%")
st.plotly_chart(fig_bounce, use_container_width=True)

st.markdown("---")  


st.markdown("### Conversion Rate Trend by Channel")
fig_conv = px.line(
    char_trends, x="month", y="conversion_rate", color="utm_source",
    labels={"month": "Month", "conversion_rate": "Conversion Rate", "utm_source": "UTM Source"}
)
fig_conv.update_yaxes(tickformat=".0%")
st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---") 


st.markdown("### Average Order Value Trend by Channel")
fig_aov = px.line(
    char_trends, x="month", y="avg_order_value", color="utm_source",
    labels={"month": "Month", "avg_order_value": "Average Order Value ($)", "utm_source": "UTM Source"}
)
fig_aov.update_yaxes(title="Average Order Value ($)")
st.plotly_chart(fig_aov, use_container_width=True)