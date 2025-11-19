import streamlit as st
import pandas as pd
import plotly.express as px
#import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders
from utils.formatters import format_currency, format_percent, format_km
#from utils.auth import enforce_access
#from app import ROLE_DASHBOARDS

# =============================================================================
# # --- Role-based access enforcement ---
# role = st.session_state.get("role", "guest")
# allowed_pages = ROLE_DASHBOARDS.get(role, [])
# enforce_access(role, allowed_pages, __file__)
# =============================================================================

#st.set_page_config(page_title="Channel Performance & Trends", layout="wide")
st.title("📈 Channel Performance & Trends")   

# =============================================================================
# # --- Role-based access enforcement ---
# role = st.session_state.get("role", "guest")
# allowed_pages = ROLE_DASHBOARDS.get(role, [])
# current_page = os.path.join("pages", os.path.basename(__file__))
# enforce_access(role, allowed_pages, current_page)
# =============================================================================


F = sidebar_filters()
dfs = load_tables(["website_sessions","orders"])
sessions = filter_sessions(dfs["website_sessions"], F)
orders = filter_orders(dfs["orders"], F)


sess_summary = sessions.groupby("utm_source").agg(
    sessions=("website_session_id","nunique"),
    bounce_rate=("is_bounce","mean") if "is_bounce" in sessions.columns else ("website_session_id","count")
).reset_index()

ord_summary = orders.merge(sessions[["website_session_id","utm_source"]], on="website_session_id", how="left")
ord_summary = ord_summary.groupby("utm_source").agg(
    orders=("order_id","nunique"),
    revenue=("price_usd","sum"),
    avg_order_value=("price_usd","mean")
).reset_index()

portfolio = sess_summary.merge(ord_summary, on="utm_source", how="outer").fillna(0)
portfolio["conversion_rate"] = portfolio["orders"] / portfolio["sessions"]


st.markdown("### Sessions Distribution by Channel")
fig_sessions = px.pie(portfolio, names="utm_source", values="sessions", hole=0.4)
fig_sessions.update_layout(legend_title_text="UTM Source")
fig_sessions.update_traces(textinfo="label+percent", textfont=dict(color="white", size=14), textposition="outside")
st.plotly_chart(fig_sessions, use_container_width=True)

st.markdown("---")  

st.markdown("### Orders by Channel")
portfolio["label"] = portfolio["orders"].apply(format_km)
fig_orders = px.bar(portfolio, x="utm_source", y="orders", text="label")
fig_orders.update_traces(textposition="outside", textfont=dict(color="white", size=14))
fig_orders.update_layout(xaxis_title="UTM Source", yaxis_title="Orders")
st.plotly_chart(fig_orders, use_container_width=True)

st.markdown("---")  

st.markdown("### Revenue by Channel")
portfolio["label"] = portfolio["revenue"].apply(format_km)
fig_revenue = px.bar(portfolio, x="utm_source", y="revenue", text="label")
fig_revenue.update_traces(textposition="outside", textfont=dict(color="white", size=14))
fig_revenue.update_layout(xaxis=dict(title="UTM Source"), yaxis=dict(title="Revenue ($)"))
fig_revenue.update_yaxes(tickprefix="$")
st.plotly_chart(fig_revenue, use_container_width=True)

st.markdown("---")  

st.markdown("### Revenue Share by Channel")
fig_pie = px.pie(portfolio, names="utm_source", values="revenue")
fig_pie.update_traces(textposition="outside", textinfo="label+percent", textfont=dict(color="white", size=14))
fig_pie.update_layout(legend_title_text="UTM Source")
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")  

st.markdown("### Conversion Rate by Channel")
fig_conv = px.bar(portfolio, x="utm_source", y="conversion_rate", text="conversion_rate")
fig_conv.update_layout(xaxis=dict(title="UTM Source"), yaxis=dict(title="Conversion Rate"))
fig_conv.update_traces(texttemplate="%{text:.2%}", textposition="outside", textfont=dict(color="white", size=14))
fig_conv.update_yaxes(tickformat=".0%")
st.plotly_chart(fig_conv, use_container_width=True)

st.markdown("---")  

portfolio["avg_order_value"] = portfolio["revenue"] / portfolio["orders"]

st.markdown("### Average Order Value by Channel")
fig_aov = px.bar(portfolio, x="utm_source", y="avg_order_value", text="avg_order_value")
fig_aov.update_layout(xaxis=dict(title="UTM Source"), yaxis=dict(title="Average Order Value ($)"))
fig_aov.update_traces(texttemplate="$%{text:.2f}", textposition="outside", textfont=dict(color="white", size=14))
fig_aov.update_yaxes(tickprefix="$")
st.plotly_chart(fig_aov, use_container_width=True)

st.markdown("---")  

st.markdown("### Channel Characteristics")
comp_table = portfolio[["utm_source","sessions","orders","conversion_rate","revenue","avg_order_value"]].copy()
comp_table = comp_table.rename(columns={
    "utm_source": "UTM Source",
    "sessions": "Sessions",
    "orders": "Orders",
    "conversion_rate": "Conversion Rate",
    "revenue": "Revenue",
    "avg_order_value": "Average Order Value"
})
total_row = {
    "UTM Source": "",
    "Sessions": comp_table["Sessions"].sum(),
    "Orders": comp_table["Orders"].sum(),
    "Conversion Rate": comp_table["Conversion Rate"].mean(),
    "Revenue": comp_table["Revenue"].sum(),
    "Average Order Value": comp_table["Average Order Value"].mean()
}
comp_table = pd.concat([comp_table, pd.DataFrame([total_row])], ignore_index=True)
comp_table["Conversion Rate"] = comp_table["Conversion Rate"].apply(format_percent)
comp_table["Revenue"] = comp_table["Revenue"].apply(format_currency)
comp_table["Average Order Value"] = comp_table["Average Order Value"].apply(format_currency)
st.dataframe(comp_table.set_index("UTM Source"))

st.markdown("---")  

st.markdown("### Trends Over Time")
sessions["month"] = pd.to_datetime(sessions["created_at"]).dt.to_period("M").dt.to_timestamp()
orders["month"] = pd.to_datetime(orders["created_at"]).dt.to_period("M").dt.to_timestamp()

sess_trend = sessions.groupby(["utm_source","month"]).size().reset_index(name="sessions")
ord_trend = orders.merge(sessions[["website_session_id","utm_source"]], on="website_session_id", how="left")
ord_trend = ord_trend.groupby(["utm_source","month"]).size().reset_index(name="orders")
rev_trend = orders.merge(sessions[["website_session_id","utm_source"]], on="website_session_id", how="left")
rev_trend = rev_trend.groupby(["utm_source","month"])["price_usd"].sum().reset_index(name="revenue")

st.markdown("#### Sessions Trend by Channel")
fig_sess = px.line(sess_trend, x="month", y="sessions", color="utm_source",
                   labels={"month": "Month", "sessions": "Sessions", "utm_source": "UTM Source"})
st.plotly_chart(fig_sess, use_container_width=True)

st.markdown("#### Orders Trend by Channel")
fig_ord = px.line(ord_trend, x="month", y="orders", color="utm_source",
                  labels={"month": "Month", "orders": "Orders", "utm_source": "UTM Source"})
st.plotly_chart(fig_ord, use_container_width=True)

st.markdown("#### Revenue Trend by Channel")
fig_rev = px.line(rev_trend, x="month", y="revenue", color="utm_source",
                  labels={"month": "Month", "revenue": "Revenue ($)", "utm_source": "UTM Source"})
fig_rev.update_yaxes(title="Revenue ($)")
st.plotly_chart(fig_rev, use_container_width=True)

