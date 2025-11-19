import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from .config import (
    PRODUCT_NAMES, PAGEVIEW_URLS, UTM_SOURCE, UTM_CAMPAIGN, UTM_CONTENT,
    DEVICE_TYPE, HTTP_REFERRER, DEFAULT_DATE_DAYS
)

def time_granularity_selector(key: str = "granularity"):
    return st.radio(
        "Time Granularity",
        ["Daily", "Weekly", "Monthly", "Yearly"],  
        index=1,
        key=key,
        horizontal=True
    )

def date_range_selector(key_start="start_date", key_end="end_date"):
    min_date = pd.Timestamp("2012-03-01")
    max_date = pd.Timestamp("2015-04-30")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            min_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date(),
            key=key_start
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            max_date.date(),
            min_value=min_date.date(),
            max_value=max_date.date(),
            key=key_end
        )

    # Return inclusive range
    return pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

def categorical_multiselect(label: str, options: list[str], key: str, default_all=True):
    default = options if default_all else []
    return st.sidebar.multiselect(label, options=options, default=default, key=key)

def sidebar_filters():
    st.sidebar.header("Filters")
    start_ts, end_ts = date_range_selector()
    granularity = time_granularity_selector()

    # Acquisition filters
    src = categorical_multiselect("UTM Source", UTM_SOURCE, "utm_source", default_all=False)
    cmp = categorical_multiselect("UTM Campaign", UTM_CAMPAIGN, "utm_campaign", default_all=False)
    #cnt = categorical_multiselect("UTM Content", UTM_CONTENT, "utm_content", default_all=False)
    dev = categorical_multiselect("Device Type", DEVICE_TYPE, "device_type", default_all=False)
    #ref = categorical_multiselect("HTTP Referrer", HTTP_REFERRER, "http_referer", default_all=False)

    # Product filters
    prod = categorical_multiselect("Products", PRODUCT_NAMES, "product_names", default_all=False)

    # Page filters (optional)
    #purls = categorical_multiselect("Page URLs", PAGEVIEW_URLS, "pageview_urls", default_all=False)
    
# =============================================================================
#     return {
#         "start_ts": start_ts,
#         "end_ts": end_ts,
#         "granularity": granularity,
#         "utm_source": src,
#         "utm_campaign": cmp,
#         "utm_content": cnt,
#         "device_type": dev,
#         "http_referer": ref,
#         "product_names": prod,
#         "pageview_urls": purls,
#     }
# =============================================================================
    return {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "granularity": granularity,
        "utm_source": src,
        "utm_campaign": cmp,
        "device_type": dev,
        "product_names": prod,
        #"pageview_urls": purls
    }