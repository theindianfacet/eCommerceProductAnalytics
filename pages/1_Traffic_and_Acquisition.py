import streamlit as st
import plotly.express as px
import pandas as pd
import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import (
    filter_sessions, filter_pageviews, rollup,
    compute_bounce_rate, compute_conversion_rate,
    hour_weekday_session_volume
)
from utils.formatters import  format_percent, format_number, format_km

st.title("🌐 Traffic & Acquisition")  


F = sidebar_filters()

dfs = load_tables(["website_sessions", "website_pageviews", "orders"])
sessions = filter_sessions(dfs["website_sessions"], F)
pageviews = filter_pageviews(dfs["website_pageviews"], F)
orders = dfs["orders"]
orders = orders[(orders["created_at"] >= F["start_ts"]) & (orders["created_at"] <= F["end_ts"])]

# KPI
bounce = compute_bounce_rate(sessions, pageviews)
conv = compute_conversion_rate(sessions, orders)
repeat_rate = (sessions["is_repeat_session"] == True).sum() / len(sessions) if len(sessions) > 0 else None


k1, k2, k3, k4 = st.columns(4)
k1.metric("👥 Sessions", format_number(len(sessions)))
k2.metric("↩️ Bounce Rate", format_percent(bounce))
k3.metric("🎯 Conversion Rate", format_percent(conv))
k4.metric("🔁 Repeat Sessions Rate", format_percent(repeat_rate))

st.markdown("---")


st.markdown("### Traffic Trend")
s_roll = rollup(sessions, "created_at", F["granularity"])
trend = s_roll.groupby("bucket").size().rename("sessions").reset_index()
fig_trend = px.line(trend, x="bucket", y="sessions")
fig_trend.update_layout(xaxis_title="Time", yaxis_title="Sessions")
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")  

st.markdown("### Site Traffic Breakdown by Source")
src_break = sessions.groupby("utm_source").size().rename("sessions").reset_index().sort_values("sessions", ascending=False)
src_break["label"] = src_break["sessions"].apply(format_km)
fig_src = px.bar(src_break, x="utm_source", y="sessions", text="label")
fig_src.update_layout(xaxis_title="UTM Source", yaxis_title="Sessions")
fig_src.update_traces(textposition="outside", texttemplate="%{text}")
st.plotly_chart(fig_src, use_container_width=True)

st.markdown("---") 


st.markdown("### Device Mix")
dev_break = sessions.groupby("device_type").size().rename("sessions").reset_index()
legend_map = {"desktop": "Desktop", "mobile": "Mobile"}
dev_break["Device Type"] = dev_break["device_type"].map(legend_map)
fig_dev = px.pie(dev_break, names="Device Type", values="sessions")
fig_dev.update_layout(legend_title_text="Device Type")
st.plotly_chart(fig_dev, use_container_width=True)

st.markdown("---")  

st.markdown("### Average Session Volume")
by_hour, by_weekday = hour_weekday_session_volume(sessions)
c1, c2 = st.columns(2)
with c1:
    by_hour["label"] = by_hour["sessions"].apply(format_km)
    fig_hr = px.bar(by_hour, x="hour", y="sessions", title="Average Session Volume by Hour of Day", text="label")
    fig_hr.update_layout(xaxis_title="Hour", yaxis_title="Sessions")
    fig_hr.update_traces(textposition="outside", texttemplate="%{text}")
    st.plotly_chart(fig_hr, use_container_width=True)
with c2:
    by_weekday["label"] = by_weekday["sessions"].apply(format_km)
    fig_wd = px.bar(by_weekday, x="weekday", y="sessions", title="Average Session Volume by Day of Week", text="label")
    fig_wd.update_layout(xaxis_title="Day of Week", yaxis_title="Sessions")
    fig_wd.update_traces(textposition="outside", texttemplate="%{text}")
    st.plotly_chart(fig_wd, use_container_width=True)

st.markdown("---")  

st.markdown("### Traffic Seasonality")

s_roll_month = rollup(sessions, "created_at", "Monthly")
s_roll_month["year"] = pd.to_datetime(s_roll_month["bucket"]).dt.year
monthly_sessions = s_roll_month.groupby(["year","bucket"]).size().reset_index(name="sessions")
monthly_sessions["row_num"] = monthly_sessions.groupby("year").cumcount()
monthly_sessions["label"] = monthly_sessions["sessions"].apply(format_km)
monthly_sessions["label"] = monthly_sessions["label"].where(monthly_sessions["row_num"] % 3 == 0, None)
fig_monthly = px.line(monthly_sessions, x="bucket", y="sessions", color="year", title="Monthly Sessions by Year", text="label", markers=True)
fig_monthly.update_traces(textposition="top center")
fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Sessions", legend_title_text="Year")
st.plotly_chart(fig_monthly, use_container_width=True)

# Yearly totals
s_roll_year = rollup(sessions, "created_at", "Yearly")
yearly_sessions = s_roll_year.groupby("bucket").size().reset_index(name="sessions")
yearly_sessions["year"] = pd.to_datetime(yearly_sessions["bucket"]).dt.year
yearly_sessions["label"] = yearly_sessions["sessions"].apply(format_km)
fig_yearly = px.bar(yearly_sessions, x="bucket", y="sessions", title="Yearly Sessions", text="label")
fig_yearly.update_layout(xaxis_title="Year", yaxis_title="Sessions", xaxis=dict(tickmode="linear"))
fig_yearly.update_traces(textposition="outside", texttemplate="%{text}")
st.plotly_chart(fig_yearly, use_container_width=True)

# Orders vs Sessions
o_roll_month = rollup(orders, "created_at", "Monthly")
o_roll_month["year"] = pd.to_datetime(o_roll_month["bucket"]).dt.year
monthly_orders = o_roll_month.groupby(["year","bucket"]).size().reset_index(name="orders")
monthly_orders["row_num"] = monthly_orders.groupby("year").cumcount()
monthly_orders["label"] = monthly_orders["orders"].apply(format_km)
monthly_orders["label"] = monthly_orders["label"].where(monthly_orders["row_num"] % 3 == 0, None)
fig_orders = px.line(monthly_orders, x="bucket", y="orders", color="year", title="Monthly Orders by Year", text="label", markers=True)
fig_orders.update_traces(textposition="top center")
fig_orders.update_layout(xaxis_title="Month", yaxis_title="Orders", legend_title_text="Year")
st.plotly_chart(fig_orders, use_container_width=True)

st.markdown("---") 


st.markdown("### Direct vs Broad-Driven Traffic")
def classify_campaign(camp):
    if pd.isna(camp):
        return "Other"
    camp = camp.lower()
    if "brand" in camp or "direct" in camp:
        return "Direct/Brand"
    elif "nonbrand" in camp or "broad" in camp:
        return "Broad/Nonbrand"
    else:
        return "Other"

sessions["traffic_type"] = sessions["utm_campaign"].apply(classify_campaign)

traffic_summary = sessions.groupby("traffic_type")["website_session_id"].nunique().reset_index(name="sessions")

orders_type = orders.merge(sessions[["website_session_id", "traffic_type"]], on="website_session_id", how="left")
orders_summary = orders_type.groupby("traffic_type").agg(
    orders=("order_id", "nunique"),
    revenue=("price_usd", "sum")
).reset_index()

traffic_summary = traffic_summary.merge(orders_summary, on="traffic_type", how="left").fillna(0)
traffic_summary["conversion_rate"] = traffic_summary["orders"] / traffic_summary["sessions"]

def safe_value(df, traffic_type, col, default=0.0):
    vals = df.loc[df["traffic_type"] == traffic_type, col]
    return vals.values[0] if not vals.empty else default

direct_conv = safe_value(traffic_summary, "Direct/Brand", "conversion_rate") * 100
broad_conv = safe_value(traffic_summary, "Broad/Nonbrand", "conversion_rate") * 100
direct_rev = safe_value(traffic_summary, "Direct/Brand", "revenue")
broad_rev = safe_value(traffic_summary, "Broad/Nonbrand", "revenue")
rev_gap = direct_rev - broad_rev

c1, c2, c3 = st.columns(3)
c1.metric("Direct/Brand Conversion Rate", f"{direct_conv:.1f}%")
c2.metric("Broad/Nonbrand Conversion Rate", f"{broad_conv:.1f}%")
c3.metric("Revenue Gap (Direct vs Broad)", f"${rev_gap:,.0f}")

st.markdown("---")  

# Conversion rate
traffic_summary["conv_label"] = traffic_summary["conversion_rate"].apply(lambda x: f"{x:.1%}")
fig_conv = px.bar(
    traffic_summary,
    x="traffic_type", y="conversion_rate",
    title="Conversion Rate by Traffic Type",
    text="conv_label"
)
fig_conv.update_traces(textposition="outside")
fig_conv.update_yaxes(tickformat=".0%")
fig_conv.update_layout(yaxis_title="Conversion Rate", xaxis_title="Traffic Type")
st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---")

# Revenue 
traffic_summary["rev_label"] = traffic_summary["revenue"].apply(format_km)
fig_rev = px.bar(
    traffic_summary,
    x="traffic_type", y="revenue",
    title="Revenue by Traffic Type",
    text="rev_label"
)
fig_rev.update_traces(textposition="outside", texttemplate="%{text}")
fig_rev.update_layout(yaxis_title="Revenue ($)", xaxis_title="Traffic Type")
st.plotly_chart(fig_rev, use_container_width=True)

