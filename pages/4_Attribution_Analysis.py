import streamlit as st
import pandas as pd
import os
import plotly.express as px
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders
from utils.formatters import format_currency, format_km
from utils.auth import enforce_access
from app import ROLE_DASHBOARDS

# =============================================================================
# # --- Role-based access enforcement ---
# role = st.session_state.get("role", "guest")
# allowed_pages = ROLE_DASHBOARDS.get(role, [])
# enforce_access(role, allowed_pages, __file__)
# =============================================================================

st.set_page_config(page_title="Attribution Analysis", layout="wide")
st.title("🎯 Attribution Analysis")  



F = sidebar_filters()
dfs = load_tables(["website_sessions","orders"])
sessions = filter_sessions(dfs["website_sessions"], F)
orders = filter_orders(dfs["orders"], F)


sess_orders = sessions.merge(
    orders[["order_id","created_at","price_usd","website_session_id","user_id"]],
    on="website_session_id", how="right"
)

# First-touch attribution
first_touch = sessions.sort_values("created_at").groupby("user_id").first().reset_index()
orders_first = orders.merge(first_touch[["user_id","utm_source","utm_campaign"]], on="user_id", how="left")
ft_rev = orders_first.groupby("utm_source")["price_usd"].sum().reset_index(name="first_touch_revenue")

# Last-touch attribution
last_touch = sessions.sort_values("created_at").groupby("user_id").last().reset_index()
orders_last = orders.merge(last_touch[["user_id","utm_source","utm_campaign"]], on="user_id", how="left")
lt_rev = orders_last.groupby("utm_source")["price_usd"].sum().reset_index(name="last_touch_revenue")

# Linear attribution
linear_pairs = sessions.merge(orders[["order_id","user_id","price_usd"]], on="user_id", how="inner")
linear_pairs["share"] = linear_pairs.groupby("order_id")["user_id"].transform("count")
linear_pairs["rev_share"] = linear_pairs["price_usd"] / linear_pairs["share"]
lin_rev = linear_pairs.groupby("utm_source")["rev_share"].sum().reset_index(name="linear_revenue")

attrib = ft_rev.merge(lt_rev, on="utm_source", how="outer").merge(lin_rev, on="utm_source", how="outer").fillna(0)

# --- KPI: Top source by each model ---
st.markdown("### Top Sources by Attribution Model")
col1, col2, col3 = st.columns(3)
if not attrib.empty:
    top_ft = attrib.sort_values("first_touch_revenue", ascending=False).iloc[0]
    top_lt = attrib.sort_values("last_touch_revenue", ascending=False).iloc[0]
    top_lin = attrib.sort_values("linear_revenue", ascending=False).iloc[0]
    col1.metric("👆 Top First-Touch Source", top_ft["utm_source"], format_currency(top_ft["first_touch_revenue"]))
    col2.metric("👇 Top Last-Touch Source", top_lt["utm_source"], format_currency(top_lt["last_touch_revenue"]))
    col3.metric("➗ Top Linear Source", top_lin["utm_source"], format_currency(top_lin["linear_revenue"]))

st.markdown("---")  


st.markdown("### Revenue Attribution Comparison")
attrib_melt = attrib.melt(id_vars="utm_source", var_name="model", value_name="revenue")

legend_map = {
    "first_touch_revenue": "First Touch Revenue",
    "last_touch_revenue": "Last Touch Revenue",
    "linear_revenue": "Linear Revenue"
}
attrib_melt["model"] = attrib_melt["model"].map(legend_map)
attrib_melt["label"] = attrib_melt["revenue"].apply(format_km)

fig_attrib = px.bar(
    attrib_melt,
    x="utm_source", y="revenue", color="model", barmode="group", text="label"
)
fig_attrib.update_traces(textposition="outside", textfont=dict(color="white", size=14))
fig_attrib.update_layout(legend_title_text="Model:", xaxis_title="Source", yaxis_title="Revenue ($)")
st.plotly_chart(fig_attrib, use_container_width=True)

st.markdown("---")  


st.markdown("### Attribution Comparison Table")
attrib_friendly = attrib.rename(columns={
    "utm_source": "UTM Source",
    "first_touch_revenue": "First Touch Revenue",
    "last_touch_revenue": "Last Touch Revenue",
    "linear_revenue": "Linear Revenue"
})

attrib_friendly["Total Revenue"] = (
    attrib_friendly["First Touch Revenue"]
    + attrib_friendly["Last Touch Revenue"]
    + attrib_friendly["Linear Revenue"]
)

revenue_cols = ["First Touch Revenue","Last Touch Revenue","Linear Revenue","Total Revenue"]
attrib_friendly[revenue_cols] = attrib_friendly[revenue_cols].applymap(format_currency)

attrib_friendly = attrib_friendly.set_index("UTM Source")
st.dataframe(attrib_friendly)