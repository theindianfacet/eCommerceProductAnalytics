import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders
from utils.formatters import format_percent


# --- Page config and title ---
#st.set_page_config(page_title="Product Journey Flows", layout="wide")
st.title("📦 Product Journey Flows")


# --- Filters and data load ---
#F = sidebar_filters()
dfs = load_tables(["website_pageviews", "orders"])
#pageviews = filter_sessions(dfs["website_pageviews"], F)
#orders = filter_orders(dfs["orders"], F)
pageviews = dfs["website_pageviews"]
orders = dfs["orders"]
st.markdown("---")

# --- Identify product pages and build session paths ---
product_pages = pageviews[pageviews["pageview_url"].str.contains("/products")]
paths = product_pages.groupby("website_session_id")["pageview_url"].apply(list).reset_index(name="product_path")
paths_orders = paths.merge(orders[["order_id", "website_session_id", "price_usd"]], on="website_session_id", how="left")


# --- Funnel groups definition ---
funnel_groups = {
    "Landers": ["/lander-1", "/lander-2", "/lander-3", "/lander-4", "/lander-5", "/home"],
    "Products": [
        "/products",
        "/the-birthday-sugar-panda",
        "/the-forever-love-bear",
        "/the-hudson-river-mini-bear",
        "/the-original-mr-fuzzy",
    ],
    "Cart": ["/cart"],
    "Shipping": ["/shipping"],
    "Billing": ["/billing", "/billing-2"],
    "Thank You": ["/thank-you-for-your-order"],
}

# --- Product-level funnels (exclude general /products listing) ---
st.header("Product Conversion Funnels")
funnels = []
for prod in funnel_groups["Products"]:
    if prod == "/products":
        continue

    sess_prod = pageviews[pageviews["pageview_url"] == prod]["website_session_id"].unique()
    step_cart = pageviews[(pageviews["website_session_id"].isin(sess_prod)) & (pageviews["pageview_url"].isin(funnel_groups["Cart"]))]["website_session_id"].nunique()
    step_ship = pageviews[(pageviews["website_session_id"].isin(sess_prod)) & (pageviews["pageview_url"].isin(funnel_groups["Shipping"]))]["website_session_id"].nunique()
    step_bill = pageviews[(pageviews["website_session_id"].isin(sess_prod)) & (pageviews["pageview_url"].isin(funnel_groups["Billing"]))]["website_session_id"].nunique()
    step_thank = pageviews[(pageviews["website_session_id"].isin(sess_prod)) & (pageviews["pageview_url"].isin(funnel_groups["Thank You"]))]["website_session_id"].nunique()

    funnels.append({
        "Product": prod,
        "Cart": step_cart,
        "Shipping": step_ship,
        "Billing": step_bill,
        "Thank You": step_thank,
    })

funnels_df = pd.DataFrame(funnels)

# Render funnels
for _, row in funnels_df.iterrows():
    prod = row["Product"]
    prod_df = pd.DataFrame({
        "Stage": ["Cart", "Shipping", "Billing", "Thank You"],
        "Value": [row["Cart"], row["Shipping"], row["Billing"], row["Thank You"]],
    })

    fig_prod_funnel = px.funnel(
        prod_df,
        x="Value",
        y="Stage",
        title=f"Conversion Funnel — {prod}",
    )
    fig_prod_funnel.update_yaxes(title=None)

    # K/M formatted labels (keeps concise numeric display)
    def km_label(v):
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"{v/1_000:.2f}K"
        return str(int(v))

    fig_prod_funnel.update_traces(
        texttemplate=[km_label(v) for v in prod_df["Value"]],
        textposition="inside",
        textfont=dict(size=12, color="black")
    )

    st.plotly_chart(fig_prod_funnel, use_container_width=True)
    st.markdown("---")



# --- KPI: Best converting product funnel (with icon) ---
if not funnels_df.empty:
    funnels_df["conv_rate"] = funnels_df["Thank You"] / funnels_df["Cart"].replace(0, pd.NA)
    top_prod = funnels_df.sort_values("conv_rate", ascending=False).iloc[0]
    st.metric("🏆 Best Converting Product", top_prod["Product"], format_percent(top_prod["conv_rate"]))
else:
    st.info("No funnel data available to compute top converting product.")

st.markdown("---")

# --- Build lookup dict and augment pageview rows for Sankey pathing ---
st.header("Product wise Pathing Sankeys")

url_to_group = {url: group for group, urls in funnel_groups.items() for url in urls}
pageviews = pageviews.copy()
pageviews["next_page"] = pageviews.groupby("website_session_id")["pageview_url"].shift(-1)
pageviews["page_group"] = pageviews["pageview_url"].map(url_to_group)
pageviews["next_group"] = pageviews["next_page"].map(url_to_group)

# --- Sankey per product (only product detail pages, including /products listing if present) ---
product_pages_list = funnel_groups["Products"]

for prod in product_pages_list:
    prod_sessions = pageviews[pageviews["pageview_url"] == prod]["website_session_id"].unique()
    prod_views = pageviews[pageviews["website_session_id"].isin(prod_sessions)]

    flows = (
        prod_views.dropna(subset=["page_group", "next_group"])
        .groupby(["page_group", "next_group"])
        .size()
        .reset_index(name="count")
    )

    if flows.empty:
        st.info(f"No navigation flows captured for {prod}")
        continue

    # Labels and indices for sankey
    labels = list(pd.concat([flows["page_group"], flows["next_group"]]).unique())
    label_index = {label: i for i, label in enumerate(labels)}

    sankey = go.Figure(data=[go.Sankey(
        node=dict(
            pad=12,
            thickness=18,
            line=dict(color="black", width=0.5),
            label=labels
        ),
        link=dict(
            source=flows["page_group"].map(label_index),
            target=flows["next_group"].map(label_index),
            value=flows["count"]
        )
    )])

    sankey.update_layout(
        title_text=f"Pathing Journey — {prod}",
        font_size=11,
        margin=dict(t=50, b=20, l=20, r=20)
    )

    st.plotly_chart(sankey, use_container_width=True)
    st.markdown("---")


