import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders, compute_conversion_rate
from utils.formatters import format_number, format_currency, format_percent, format_km

st.title("🧠 Customer Insights")



F = sidebar_filters()
dfs = load_tables(["website_sessions","orders"])
sessions = filter_sessions(dfs["website_sessions"], F)
orders = filter_orders(dfs["orders"], F)

st.markdown("---")

total_sessions = len(sessions)
conv_rate = compute_conversion_rate(sessions, orders)

k1, k2 = st.columns(2)
k1.metric("🖥️ Total Sessions", format_number(total_sessions))
k2.metric("✅ Overall Conversion Rate", format_percent(conv_rate))

st.markdown("---")

st.subheader("Device Mix")
device_mix = sessions.groupby("device_type").size().reset_index(name="sessions")
legend_map = {"desktop": "Desktop", "mobile": "Mobile"}
device_mix["Device Type"] = device_mix["device_type"].map(legend_map)

fig_device = px.pie(device_mix, names="Device Type", values="sessions")
fig_device.update_layout(legend_title_text="Device Type")
fig_device.update_traces(textposition="outside", textinfo="label+percent", textfont=dict(color="white", size=14))
st.plotly_chart(fig_device, use_container_width=True)

st.markdown("---")

st.subheader("Traffic Sources")
src_break = sessions.groupby("utm_source").size().reset_index(name="sessions").sort_values("sessions", ascending=False)
src_break["label"] = src_break["sessions"].apply(format_km)
fig_src = px.bar(src_break, x="utm_source", y="sessions", text="label")
fig_src.update_traces(texttemplate="%{text}", textposition="outside", textfont=dict(color="white", size=14))
fig_src.update_layout(xaxis_title="UTM Source", yaxis_title="Sessions")
st.plotly_chart(fig_src, use_container_width=True)

st.markdown("---")

st.subheader("Campaign Breakdown")
camp_break = sessions.groupby("utm_campaign").size().reset_index(name="sessions").sort_values("sessions", ascending=False)
camp_break["label"] = camp_break["sessions"].apply(format_km)
fig_camp = px.bar(camp_break, x="utm_campaign", y="sessions", text="label")
fig_camp.update_traces(texttemplate="%{text}", textposition="outside", textfont=dict(color="white", size=14))
fig_camp.update_layout(xaxis_title="UTM Campaign", yaxis_title="Sessions")
st.plotly_chart(fig_camp, use_container_width=True)

st.markdown("---")

st.subheader("Conversion Rate by Source & Device")
sess_orders = sessions.merge(orders[["website_session_id","order_id"]], on="website_session_id", how="left")
sess_orders["converted"] = sess_orders["order_id"].notna()
conv_matrix = sess_orders.groupby(["utm_source","device_type"])["converted"].mean().reset_index()

fig_conv_matrix = px.density_heatmap(
    conv_matrix, x="utm_source", y="device_type", z="converted",
    color_continuous_scale="Blues", text_auto=".2%"
)
fig_conv_matrix.update_layout(
    xaxis_title="UTM Source", yaxis_title="Device Type",
    coloraxis_colorbar=dict(title="Conversion Rate", tickformat=".0%")
)
st.plotly_chart(fig_conv_matrix, use_container_width=True)

st.markdown("---")


st.subheader("Customer Segmentation (Revenue vs Sessions)")
user_sessions = sessions.groupby("user_id")["website_session_id"].nunique().reset_index(name="sessions")
user_orders = orders.groupby("user_id").agg(
    orders=("order_id","nunique"),
    revenue=("price_usd","sum"),
    avg_order_value=("price_usd","mean")
).reset_index()

users = user_sessions.merge(user_orders, on="user_id", how="left").fillna(0)
users["conversion_rate"] = users["orders"] / users["sessions"]
users["repeat_purchase"] = (users["orders"] >= 2).astype(int)

features = users[["sessions","conversion_rate","revenue","avg_order_value","repeat_purchase"]]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

kmeans = KMeans(n_clusters=4, random_state=42)
users["segment"] = kmeans.fit_predict(X_scaled)

segment_map = {0: "Low Spender", 1: "Medium Spender", 2: "High Spender", 3: "VIP Spender"}
users["Segment"] = users["segment"].map(segment_map)

fig_seg = px.scatter(
    users, x="sessions", y="revenue", color="Segment",
    hover_data=["conversion_rate","avg_order_value","repeat_purchase"]
)
fig_seg.update_layout(xaxis_title="Sessions", yaxis_title="Revenue ($)", legend_title_text="Segment")
fig_seg.update_xaxes(tickmode="linear", dtick=1)
st.plotly_chart(fig_seg, use_container_width=True)

st.markdown("---")

st.subheader("Segment Characteristics")
seg_summary = users.groupby("segment").agg(
    Users=("user_id","count"),
    Average_Sessions=("sessions","mean"),
    Average_Conversion_Rate=("conversion_rate","mean"),
    Average_Revenue=("revenue","mean"),
    Average_Order_Value=("avg_order_value","mean"),
    Repeat_Rate=("repeat_purchase","mean")
).reset_index()

seg_summary["Segment"] = seg_summary["segment"].map(segment_map)
seg_summary = seg_summary.drop(columns=["segment"])
seg_summary = seg_summary[[
    "Segment","Users","Average_Sessions","Average_Revenue","Average_Order_Value","Average_Conversion_Rate","Repeat_Rate"
]]

seg_summary["Average_Conversion_Rate"] = seg_summary["Average_Conversion_Rate"].apply(format_percent)
seg_summary["Repeat_Rate"] = seg_summary["Repeat_Rate"].apply(format_percent)
seg_summary["Average_Revenue"] = seg_summary["Average_Revenue"].apply(format_currency)
seg_summary["Average_Order_Value"] = seg_summary["Average_Order_Value"].apply(format_currency)

seg_summary = seg_summary.rename(columns={
    "Average_Sessions": "Average Sessions",
    "Average_Revenue": "Average Revenue",
    "Average_Order_Value": "Average Order Value",
    "Average_Conversion_Rate": "Average Conversion Rate",
    "Repeat_Rate": "Repeat Rate"
})

st.dataframe(seg_summary.style.hide(axis="index"))