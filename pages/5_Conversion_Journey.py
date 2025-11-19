import streamlit as st
import plotly.express as px
import pandas as pd
#import numpy as np
#import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import (
    filter_sessions, filter_pageviews, filter_orders,
    revenue_metrics, gsearch_metrics, rollup
)
from utils.formatters import format_currency, format_currency_precise, format_percent, format_number, format_km
#from utils.auth import enforce_access
#from app import ROLE_DASHBOARDS

# =============================================================================
# # --- Role-based access enforcement ---
# role = st.session_state.get("role", "guest")
# allowed_pages = ROLE_DASHBOARDS.get(role, [])
# enforce_access(role, allowed_pages, __file__)
# =============================================================================

#st.set_page_config(page_title="Conversion Journey", layout="wide")
st.title("🛤️ Conversion Journey")   


F = sidebar_filters()
dfs = load_tables(["website_sessions", "website_pageviews", "orders", "order_item_refunds"])
sessions = filter_sessions(dfs["website_sessions"], F)
pageviews = filter_pageviews(dfs["website_pageviews"], F)
orders = filter_orders(dfs["orders"], F)
refunds = dfs["order_item_refunds"]
refunds = refunds[(refunds["created_at"] >= F["start_ts"]) & (refunds["created_at"] <= F["end_ts"])]


rev = revenue_metrics(orders, refunds, sessions)
gsearch = gsearch_metrics(sessions, orders)

k1, k2, k3, k4 = st.columns(4)
k1.metric("💵 Gross Revenue", format_currency(rev['gross_revenue']))
k2.metric("💸 Refunds", format_currency(rev['refunds']))
k3.metric("✅ Net Revenue", format_currency(rev['net_revenue']))
k4.metric("📈 Revenue per Session", format_currency_precise(rev['revenue_per_session']))

k5, k6 = st.columns(2)
k5.metric("🆕 Revenue/Session (New)", format_currency_precise(rev['rev_per_session_new']))
k6.metric("🔁 Revenue/Session (Repeat)", format_currency_precise(rev['rev_per_session_repeat']))

g1, g2 = st.columns(2)
g1.metric("🎯 Gsearch Conversion Rate", format_percent(gsearch['gsearch_conversion_rate']))
g2.metric("👥 Gsearch Sessions", format_number(gsearch['gsearch_sessions']))

st.markdown("---") 


# --- Gsearch volume trend ---
st.markdown("### Gsearch Volume Trend")
g_sess = sessions[sessions["utm_source"] == "gsearch"]
g_roll = rollup(g_sess, "created_at", F["granularity"])
g_trend = g_roll.groupby("bucket").size().rename("sessions").reset_index()
fig_g = px.line(g_trend, x="bucket", y="sessions")
fig_g.update_layout(xaxis_title="Date", yaxis_title="Number of Sessions", showlegend=False)

# =============================================================================
# # Annotate crests & troughs
# import numpy as np
# y = g_trend["sessions"].values
# x = g_trend["bucket"].values
# count = 0
# for i in range(1, len(y)-1):
#     if y[i] > y[i-1] and y[i] > y[i+1]:  # crest
#         count += 1
#         if count % 3 == 0:
#             fig_g.add_annotation(x=x[i], y=y[i], text=f"{y[i]:,}", showarrow=True,
#                                  arrowhead=2, ay=-30, font=dict(color="green"))
#     elif y[i] < y[i-1] and y[i] < y[i+1]:  # trough
#         count += 1
#         if count % 4 == 0:
#             fig_g.add_annotation(x=x[i], y=y[i], text=f"{y[i]:,}", showarrow=True,
#                                  arrowhead=2, ay=30, font=dict(color="red"))
# 
# =============================================================================
st.plotly_chart(fig_g, use_container_width=True)

st.markdown("---")  # Divider

# --- Funnel Analysis ---



st.subheader("G-Search Non-brand Funnel: /lander-1 → /thank-you-for-your-order")
f_sess = g_sess[g_sess["utm_campaign"] == "nonbrand"]
f_pv = pageviews[pageviews["website_session_id"].isin(f_sess["website_session_id"])]

lander_sessions = set(f_pv[f_pv["pageview_url"] == "/lander-1"]["website_session_id"])
product_sessions = set(f_pv[f_pv["pageview_url"].str.startswith("/the-")]["website_session_id"])
cart_sessions = set(f_pv[f_pv["pageview_url"] == "/cart"]["website_session_id"])
billing_sessions = set(f_pv[f_pv["pageview_url"].isin(["/billing","/billing-2"])]["website_session_id"])
thankyou_sessions = set(f_pv[f_pv["pageview_url"] == "/thank-you-for-your-order"]["website_session_id"])

funnel_counts = pd.DataFrame({
    "step": ["Lander-1","Product","Cart","Billing","Thank You"],
    "sessions": [
        len(lander_sessions),
        len(lander_sessions & product_sessions),
        len(lander_sessions & product_sessions & cart_sessions),
        len(lander_sessions & product_sessions & cart_sessions & billing_sessions),
        len(lander_sessions & product_sessions & cart_sessions & billing_sessions & thankyou_sessions),
    ]
})
funnel_counts["label"] = funnel_counts["sessions"].apply(format_km)

fig_fun = px.funnel(funnel_counts, x="sessions", y="step", title="Conversion Funnel", text="label")
fig_fun.update_traces(texttemplate="%{text}", textfont=dict(color="black", size=14))
fig_fun.update_layout(xaxis_title="Number of Sessions", yaxis_title="Funnel Step")
st.plotly_chart(fig_fun, use_container_width=True)

st.markdown("---") 


st.markdown("### Billing Test: /billing vs /billing-2")
bill_df = f_pv[f_pv["pageview_url"].isin(["/billing","/billing-2"])]
bill_df = bill_df.rename(columns={"pageview_url":"variant"})

by_variant = bill_df.groupby("variant")["website_session_id"].nunique().rename("billing_sessions").reset_index()
ty_after_billing = f_pv[f_pv["website_session_id"].isin(bill_df["website_session_id"]) & (f_pv["pageview_url"] == "/thank-you-for-your-order")]

conv_by_variant = ty_after_billing.merge(bill_df[["website_session_id","variant"]].drop_duplicates(), on="website_session_id", how="left")
conv_rate = conv_by_variant.groupby("variant")["website_session_id"].nunique() / by_variant.set_index("variant")["billing_sessions"]

rate_df = conv_rate.reset_index().rename(columns={0:"conversion_rate"})
rate_df["label"] = rate_df["conversion_rate"].apply(lambda x: f"{x:.1%}")

fig_bill = px.bar(rate_df, x="variant", y="conversion_rate", title="Conversion Rate by Billing Variant", text="label")
fig_bill.update_yaxes(tickformat=".0%")
fig_bill.update_traces(textfont=dict(color="black", size=14))
fig_bill.update_layout(xaxis_title="Billing Page Variant", yaxis_title="Conversion Rate")
st.plotly_chart(fig_bill, use_container_width=True)

st.markdown("---")  


st.markdown("### Advanced Funnel Drop-off Analysis")
funnel_groups = {
    "Landers": ["/lander-1","/lander-2","/lander-3","/lander-4","/lander-5","/home"],
    "Products": ["/products",
                 "/the-birthday-sugar-panda",
                 "/the-forever-love-bear",
                 "/the-hudson-river-mini-bear",
                 "/the-original-mr-fuzzy"],
    "Cart": ["/cart"],
    "Shipping": ["/shipping"],
    "Billing": ["/billing","/billing-2"],
    "Thank You": ["/thank-you-for-your-order"]
}

funnel_counts = []
for step_name, urls in funnel_groups.items():
    reached = pageviews[pageviews["pageview_url"].isin(urls)]["website_session_id"].nunique()
    funnel_counts.append({"step": step_name, "sessions": reached})

funnel_df = pd.DataFrame(funnel_counts)
funnel_df["conversion_rate"] = funnel_df["sessions"] / funnel_df["sessions"].iloc[0]
funnel_df["label"] = funnel_df["sessions"].apply(format_km)

fig_funnel = px.funnel(funnel_df, x="sessions", y="step", title="Sessions Funnel", text="label")
fig_funnel.update_traces(texttemplate="%{text}", textposition="inside", textfont=dict(color="black", size=14))
fig_funnel.update_layout(xaxis_title="Sessions", yaxis_title="Funnel Step")
st.plotly_chart(fig_funnel, use_container_width=True)


funnel_df["drop_off"] = funnel_df["sessions"].shift(1) - funnel_df["sessions"]
funnel_df.loc[0,"drop_off"] = 0
funnel_df["label"] = funnel_df["drop_off"].apply(format_km)


fig_drop = px.bar(
    funnel_df,
    x="step", y="drop_off",
    title="Drop-off Counts per Funnel Step",
    text="label"
)
fig_drop.update_traces(texttemplate="%{text}", textposition="outside", textfont=dict(color="white", size=14))
fig_drop.update_layout(xaxis_title="Funnel Step", yaxis_title="Drop-offs")
st.plotly_chart(fig_drop, use_container_width=True)


overall_conv = funnel_df.iloc[-1]["sessions"] / funnel_df.iloc[0]["sessions"] if funnel_df.iloc[0]["sessions"] > 0 else None
st.metric("📉 Overall Funnel Conversion Rate", format_percent(overall_conv))