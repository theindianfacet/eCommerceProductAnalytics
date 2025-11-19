import streamlit as st
import plotly.express as px
#import pandas as pd
import plotly.graph_objects as go
#import os
from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_pageviews
from utils.formatters import  format_percent, format_number, format_km
#from utils.auth import enforce_access
#from app import ROLE_DASHBOARDS

# =============================================================================
# # --- Role-based access enforcement ---
# role = st.session_state.get("role", "guest")
# allowed_pages = ROLE_DASHBOARDS.get(role, [])
# enforce_access(role, allowed_pages, __file__)
# =============================================================================

#st.set_page_config(page_title="User Engagement", layout="wide")
st.title("👥 User Engagement")

F = sidebar_filters()

dfs = load_tables(["website_sessions", "website_pageviews"])
sessions = filter_sessions(dfs["website_sessions"], F)
pageviews = filter_pageviews(dfs["website_pageviews"], F)

# --- KPI Cards ---
total_views = len(pageviews)
total_sessions = len(sessions)

# Bounce rate
pv_counts = pageviews.groupby("website_session_id").size().rename("pv_count").reset_index()
sess_with_pv = sessions.merge(pv_counts, on="website_session_id", how="left").fillna({"pv_count": 0})
bounce_rate = (sess_with_pv["pv_count"] == 1).sum() / len(sess_with_pv) if len(sess_with_pv) > 0 else None


k1, k2, k3 = st.columns(3)
k1.metric("👁️ Total Pageviews", format_number(total_views))
k2.metric("🖥️ Total Sessions", format_number(total_sessions))
k3.metric("↩️ Bounce Rate", format_percent(bounce_rate))

st.markdown("---")

# --- Top website pages ---
st.subheader("Top Website Pages")
top_pages = pageviews.groupby("pageview_url").size().rename("views").reset_index().sort_values("views", ascending=False)
top_pages["label"] = top_pages["views"].apply(format_km)
fig_pages = px.bar(top_pages, x="pageview_url", y="views", text="label")
fig_pages.update_traces(textposition="outside", texttemplate="%{text}")
fig_pages.update_layout(xaxis_title="Page URL", yaxis_title="Views")
st.plotly_chart(fig_pages, use_container_width=True)

st.markdown("---")

# --- Top entry pages ---
st.subheader(" Top Entry Pages")
first_pv = pageviews.sort_values("created_at").groupby("website_session_id").first().reset_index()
entry_pages = first_pv.groupby("pageview_url").size().rename("entries").reset_index().sort_values("entries", ascending=False)
entry_pages["label"] = entry_pages["entries"].apply(format_km)
fig_entry = px.bar(entry_pages, x="pageview_url", y="entries", text="label")
fig_entry.update_traces(textposition="outside", texttemplate="%{text}")
fig_entry.update_layout(xaxis_title="Page URL", yaxis_title="Entries")
st.plotly_chart(fig_entry, use_container_width=True)

st.markdown("---")

# --- Bounce rate deep dive ---
st.subheader("Bounce Rate by Entry Page")
pv_counts = pageviews.groupby("website_session_id").size().rename("pv_count").reset_index()
sess_with_pv = sessions.merge(pv_counts, on="website_session_id", how="left").fillna({"pv_count":0})
first_pv = pageviews.sort_values("created_at").groupby("website_session_id").first().reset_index()
sess_with_entry = sess_with_pv.merge(first_pv[["website_session_id","pageview_url"]], on="website_session_id", how="left")

bounce_by_entry = sess_with_entry.groupby("pageview_url").apply(
    lambda g: (g["pv_count"]==1).sum()/len(g) if len(g)>0 else None
).reset_index().rename(columns={0:"bounce_rate"}).sort_values("bounce_rate", ascending=False)
bounce_by_entry["label"] = bounce_by_entry["bounce_rate"].apply(lambda x: f"{x:.1%}")
fig_bounce = px.bar(bounce_by_entry, x="pageview_url", y="bounce_rate", text="label")
fig_bounce.update_traces(textposition="outside", texttemplate="%{text}")
fig_bounce.update_yaxes(tickformat=".0%")
fig_bounce.update_layout(xaxis_title="Page URL", yaxis_title="Bounce Rate")
st.plotly_chart(fig_bounce, use_container_width=True)

st.markdown("---")

# --- Repeat visitor behavior ---
st.subheader("Repeat Visitor Timing")
repeat_sessions = sessions[sessions["is_repeat_session"]==True]
if not repeat_sessions.empty:
    repeat_sessions = repeat_sessions.sort_values(["user_id","created_at"])
    diffs = repeat_sessions.groupby("user_id")["created_at"].diff().dropna().dt.total_seconds()/3600  # hours
    if not diffs.empty:
        stats = {
            "min_hours": diffs.min(),
            "max_hours": diffs.max(),
            "avg_hours": diffs.mean()
        }
        k1,k2,k3 = st.columns(3)
        k1.metric("⏱️ Minimum Gap (hours)", f"{stats['min_hours']:.1f}")
        k2.metric("⏳ Maximum Gap (hours)", f"{stats['max_hours']:.1f}")
        k3.metric("📏 Average Gap (hours)", f"{stats['avg_hours']:.1f}")

        fig_gap = px.histogram(
            diffs, nbins=30,
            title="Distribution of Time Between Repeat Sessions (hours)",
            text_auto=True
        )
        fig_gap.update_layout(
            xaxis_title="Gap between sessions (hours)",
            yaxis_title="Number of Users",
            showlegend=False
        )
        st.plotly_chart(fig_gap, use_container_width=True)
    else:
        st.info("Not enough repeat sessions to compute timing gaps.")
else:
    st.info("No repeat sessions in current filter window.")

st.markdown("---")

# --- Pathing Analysis ---
st.subheader("Pathing Analysis")
pv_sorted = pageviews.sort_values(["website_session_id","created_at"])
paths = (
    pv_sorted.groupby("website_session_id")["pageview_url"]
    .apply(lambda x: " → ".join(x.tolist()))
    .reset_index()
)

path_counts = paths["pageview_url"].value_counts().reset_index()
path_counts.columns = ["path","count"]

if not path_counts.empty:
    top_path = path_counts.iloc[0]
    st.metric("⭐ Top Path", top_path["path"], f"{top_path['count']} Sessions")

top_paths = path_counts.head(10).copy()
top_paths["label"] = top_paths["count"].apply(format_km)
fig_paths = px.bar(
    top_paths,
    x="count", y="path",
    orientation="h",
    title="Top 10 Navigation Paths",
    text="label"
)
fig_paths.update_traces(textposition="outside", texttemplate="%{text}")
fig_paths.update_layout(xaxis_title="Sessions", yaxis_title="Path")
st.plotly_chart(fig_paths, use_container_width=True)

st.markdown("---")

# Sankey diagram for first 3 steps
pv_first3 = (
    pv_sorted.groupby("website_session_id")["pageview_url"]
    .apply(lambda x: x.tolist()[:3])
    .reset_index()
)

links = []
for steps in pv_first3["pageview_url"]:
    for i in range(len(steps) - 1):
        links.append((steps[i], steps[i+1]))

nodes = sorted(set([src for src, tgt in links] + [tgt for src, tgt in links]))
node_index = {name: i for i, name in enumerate(nodes)}

import collections
link_counts = collections.Counter(links)

sources = [node_index[src] for src, tgt in link_counts.keys()]
targets = [node_index[tgt] for src, tgt in link_counts.keys()]
values  = list(link_counts.values())
labels  = [f"{src} → {tgt}: {val}" for (src, tgt), val in link_counts.items()]

fig_sankey = go.Figure(go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=nodes,
        color="lightblue"
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values,
        label=labels,
        color="rgba(150,150,200,0.4)"
    )
))

fig_sankey.update_layout(title_text="Sankey Diagram (First 3 Steps)", font_size=12, hovermode="x")
st.plotly_chart(fig_sankey, use_container_width=True)