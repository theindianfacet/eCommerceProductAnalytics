import streamlit as st
import plotly.express as px
import pandas as pd
import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_order_items, filter_orders, rollup
from utils.formatters import format_currency, format_number, format_km

st.title("💰 Product Performance")


F = sidebar_filters()


dfs = load_tables(["order_items", "products", "orders", "order_item_refunds"])
items = filter_order_items(dfs["order_items"], dfs["products"], F)
orders = filter_orders(dfs["orders"], F)
refunds = dfs["order_item_refunds"]
refunds = refunds[(refunds["created_at"] >= F["start_ts"]) & (refunds["created_at"] <= F["end_ts"])]


if "created_at" in orders.columns:
    orders["created_at"] = pd.to_datetime(orders["created_at"], errors="coerce")
if "created_at" in items.columns:
    items["created_at"] = pd.to_datetime(items["created_at"], errors="coerce")
refunds["created_at"] = pd.to_datetime(refunds["created_at"], errors="coerce")


orders["order_date"] = orders["created_at"].dt.normalize()
items["item_date"] = items["created_at"].dt.normalize()
refunds["refund_date"] = refunds["created_at"].dt.normalize()


gross_rev_total = float(orders["price_usd"].sum()) if "price_usd" in orders.columns else 0.0
gross_by_date = orders.groupby("order_date")["price_usd"].sum(min_count=1).reset_index(name="revenue_usd").sort_values("order_date")
refunds_by_date = refunds.groupby("refund_date")["refund_amount_usd"].sum(min_count=1).reset_index(name="refunds_usd").sort_values("refund_date")

rev_merged = gross_by_date.merge(refunds_by_date, left_on="order_date", right_on="refund_date", how="left")
rev_merged["refunds_usd"] = rev_merged["refunds_usd"].fillna(0.0)
rev_merged["net_revenue"] = rev_merged["revenue_usd"] - rev_merged["refunds_usd"]

refunds_total = float(refunds["refund_amount_usd"].sum()) if "refund_amount_usd" in refunds.columns else 0.0
net_rev_total = gross_rev_total - refunds_total



k1, k2, k3 = st.columns(3)
k1.metric("💵 Gross Revenue", format_currency(gross_rev_total))
k2.metric("💸 Refunds", format_currency(refunds_total))
k3.metric("✅ Net Revenue", format_currency(net_rev_total))

st.markdown("---")


st.subheader("Sales Trends")
if not rev_merged.empty:
    rev_merged = rev_merged.rename(columns={"revenue_usd":"Gross Revenue", "net_revenue":"Net Revenue"})
    fig_rev = px.line(
        rev_merged,
        x="order_date",
        y=["Gross Revenue", "Net Revenue"],
        markers=True,
        color_discrete_map={"Gross Revenue": "#1f77b4", "Net Revenue": "#00FFFF"},
    )
    fig_rev.update_layout(yaxis_title="Revenue ($)", xaxis_title="Date", legend_title_text="Revenue Type")
    st.plotly_chart(fig_rev, use_container_width=True)
else:
    st.info("No revenue/refund data available for the selected filters.")

st.markdown("---")

# --- Product revenue bar ---
st.subheader("Product Revenue Distribution")
if "product_name" in items.columns and "price_usd" in items.columns:
    prod_rev = items.groupby("product_name")["price_usd"].sum(min_count=1).reset_index(name="revenue_usd").sort_values("revenue_usd", ascending=False)
    if not prod_rev.empty:
        prod_rev["label"] = prod_rev["revenue_usd"].apply(format_km)
        fig_prod = px.bar(
            prod_rev,
            x="product_name",
            y="revenue_usd",
            text="label"
        )
        fig_prod.update_traces(textposition="outside")
        fig_prod.update_layout(xaxis_title="Product", yaxis_title="Revenue ($)")
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("No product revenue data available for the selected filters.")
else:
    st.warning("Order items are missing required columns: product_name or price_usd.")

st.markdown("---")


st.subheader("Refund Rate by Product")
if "order_id" in refunds.columns and "order_id" in items.columns:
    ref_by_order = refunds[["order_id", "refund_amount_usd"]].groupby("order_id").sum().reset_index()
    items_with_ref = items.merge(ref_by_order, on="order_id", how="left").fillna({"refund_amount_usd": 0.0})
    if not items_with_ref.empty:
        ref_rate = items_with_ref.groupby("product_name").agg(
            revenue_usd=("price_usd", "sum"),
            refunds_usd=("refund_amount_usd", "sum"),
        ).reset_index()
        ref_rate["refund_rate"] = ref_rate["refunds_usd"] / ref_rate["revenue_usd"]
        ref_rate = ref_rate.replace([pd.NA, pd.NaT, float("inf")], 0.0)
        df_sorted = ref_rate.sort_values("refund_rate", ascending=False)

        fig_ref = px.bar(
            df_sorted,
            x="product_name",
            y="refund_rate",
            text="refund_rate"
        )
        fig_ref.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        fig_ref.update_yaxes(tickformat=".0%")
        fig_ref.update_layout(xaxis_title="Product", yaxis_title="Refund Rate")
        st.plotly_chart(fig_ref, use_container_width=True)
    else:
        st.info("No items/refunds data available to compute refund rate.")
else:
    st.warning("Refunds/items are missing required column: order_id.")

st.markdown("---")

st.subheader("Product Seasonality")
if not items.empty:
    items_roll = rollup(items, "created_at", "Monthly")
    items_roll["year"] = pd.to_datetime(items_roll["bucket"], errors="coerce").dt.year

    monthly_prod_rev = (
        items_roll.groupby(["year", "bucket", "product_name"])["price_usd"]
        .sum(min_count=1)
        .reset_index()
    )

    if not monthly_prod_rev.empty:
        fig_monthly_prod = px.line(
            monthly_prod_rev,
            x="bucket",
            y="price_usd",
            color="product_name",
            facet_row="year",
            title="Monthly Product Revenue by Year",
            markers=True,
        )
        fig_monthly_prod.update_layout(
            xaxis_title="Month",
            legend_title_text="Product"
        )

        # --- Custom y-axis labels per facet row ---
        for i, year in enumerate(sorted(monthly_prod_rev["year"].unique()), start=1):
            fig_monthly_prod.layout[f"yaxis{i}"].title.text = f"Revenue ($)"

        for anno in fig_monthly_prod.layout.annotations:
            if anno.text.startswith("year="):
                anno.text = anno.text.replace("year=", "Year=")

        st.plotly_chart(fig_monthly_prod, use_container_width=True)
    else:
        st.info("No monthly product revenue available for the selected filters.")

    # Yearly totals
    items_roll_year = rollup(items, "created_at", "Yearly")
    yearly_prod_rev = items_roll_year.groupby(["bucket", "product_name"])["price_usd"].sum(min_count=1).reset_index().rename(columns={"bucket": "year"})
    if not yearly_prod_rev.empty:
        yearly_prod_rev["label"] = yearly_prod_rev["price_usd"].apply(format_km)
        fig_yearly_prod = px.bar(
            yearly_prod_rev,
            x="year",
            y="price_usd",
            color="product_name",
            barmode="group",
            title="Yearly Product Revenue",
            text="label",
        )
        fig_yearly_prod.update_traces(textposition="outside")
        fig_yearly_prod.update_layout(xaxis_title="Year", yaxis_title="Product Revenue ($)", legend_title_text="Product")
        st.plotly_chart(fig_yearly_prod, use_container_width=True)
    else:
        st.info("No yearly product revenue available for the selected filters.")
else:
    st.info("No items available for seasonality analysis with current filters.")


st.subheader("Cross-Sell Analysis")

if "order_id" in items.columns and "product_name" in items.columns:
    pairs = (
        items.groupby("order_id")["product_name"]
        .apply(lambda x: sorted(set(x)))
        .reset_index()
    )


    pair_list = []
    for _, row in pairs.iterrows():
        prods = row["product_name"]
        if isinstance(prods, list) and len(prods) > 1:
            for i in range(len(prods)):
                for j in range(i + 1, len(prods)):
                    pair_list.append((prods[i], prods[j]))

    pair_df = pd.DataFrame(pair_list, columns=["product_a", "product_b"])

    if not pair_df.empty:
        pair_counts = (
            pair_df.value_counts()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )


        top_pair_str = "—"
        top_pair_count = 0
        if not pair_counts.empty:
            top_pair = pair_counts.iloc[0]
            top_pair_str = f"{top_pair['product_a']} + {top_pair['product_b']}"
            top_pair_count = int(top_pair["count"])
        st.metric("🤝 Top Cross-Sell Pair", top_pair_str, f"{format_number(top_pair_count)} orders")

        st.markdown("---")

        # Bar chart of top pairs
        st.subheader("Top 10 Cross-Sell Product Pairs")
        top10 = pair_counts.head(10).copy()
        top10["pair_label"] = top10.apply(lambda r: f"{r['product_a']} + {r['product_b']}", axis=1)

        fig_pairs = px.bar(
            top10,
            x="count",
            y="pair_label",
            orientation="h",
            text="count"
        )
        fig_pairs.update_traces(texttemplate="%{text}", textposition="outside")
        fig_pairs.update_layout(xaxis_title="Orders", yaxis_title="Product Pair")
        st.plotly_chart(fig_pairs, use_container_width=True)

        st.markdown("---")

        # Heatmap of product co-purchases
        st.subheader("Cross-Sell Heatmap")
        heatmap_data = pair_df.groupby(["product_a", "product_b"]).size().reset_index(name="count")
        heatmap_pivot = heatmap_data.pivot(index="product_a", columns="product_b", values="count").fillna(0)

        fig_heat = px.imshow(
            heatmap_pivot,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Blues",
        )
        fig_heat.update_layout(xaxis_title="Product A", yaxis_title="Product B")
        st.plotly_chart(fig_heat, use_container_width=True)

    else:
        st.info("No cross-sell pairs found for the selected filters.")
else:
    st.warning("Items are missing required columns: order_id, product_name.")