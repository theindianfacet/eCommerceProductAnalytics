import urllib.parse
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

# -----------------------
# CONFIG - values from st.secrets
# -----------------------
db = st.secrets["database"]

SERVER = st.secrets["SERVER"]
PORT = st.secrets["PORT"]
DATABASE = st.secrets["DATABASE"]
USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
SCHEMA = st.secrets.get("SCHEMA", "dbo")   # default to dbo if not set

TABLE_NAMES = {
    "products": "Products",
    "website_sessions": "WebsiteSessions",
    "website_pageviews": "WebsitePageViews",
    "orders": "Orders",
    "order_items": "OrderItems",
    "order_item_refunds": "OrderItemRefunds"
}

PARSE_DATES = {
    "products": ["created_at"],
    "website_sessions": ["created_at"],
    "website_pageviews": ["created_at"],
    "orders": ["created_at"],
    "order_items": ["created_at"],
    "order_item_refunds": ["created_at"]
}

DTYPES_HINTS = {
    "products": {"product_id": "string", "product_name": "string"},
    "website_pageviews": {
        "website_pageview_id": "string",
        "website_session_id": "string",
        "pageview_url": "string"
    },
    "order_item_refunds": {
        "order_item_refund_id": "string",
        "order_item_id": "string",
        "order_id": "string",
        "refund_amount_usd": "float"
    },
    "website_sessions": {
        "website_session_id": "string",
        "user_id": "string",
        "is_repeat_session": "boolean",
        "utm_source": "string",
        "utm_campaign": "string",
        "utm_content": "string",
        "device_type": "string",
        "http_referrer": "string"
    },
    "orders": {
        "order_id": "string",
        "website_session_id": "string",
        "user_id": "string",
        "primary_product_id": "string",
        "items_purchased": "Int64",
        "price_usd": "float",
        "cogs_usd": "float"
    },
    "order_items": {
        "order_item_id": "string",
        "order_id": "string",
        "product_id": "string",
        "is_primary_item": "boolean",
        "price_usd": "float",
        "cogs_usd": "float"
    }
}

# -----------------------
# Build connection engine
# -----------------------

@st.cache_resource
def get_engine():
    """
    Create SQLAlchemy engine.
    Uncomment ONE of the two options below depending on deployment target.
    """

    # --- Option 1: Streamlit Cloud (pymssql, no ODBC dependency) ---
    connection_url = f"mssql+pymssql://{USERNAME}:{PASSWORD}@{SERVER}:{PORT}/{DATABASE}"
    return create_engine(connection_url)

    # --- Option 2: Render/Railway (pyodbc, requires ODBC Driver 17 installed) ---
    # if "," in SERVER or "\\" in SERVER:
    #     server_fragment = SERVER
    # else:
    #     server_fragment = f"{SERVER},{PORT}"
    # odbc_str = (
    #     f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    #     f"SERVER={server_fragment};"
    #     f"DATABASE={DATABASE};"
    #     f"UID={USERNAME};PWD={PASSWORD};"
    #     "Encrypt=no;"
    # )
    # quoted = urllib.parse.quote_plus(odbc_str)
    # connection_url = f"mssql+pyodbc:///?odbc_connect={quoted}"
    # return create_engine(connection_url, fast_executemany=True)


def _apply_hints(df: pd.DataFrame, table_key: str) -> pd.DataFrame:
    """Apply dtype and parsing hints to a DataFrame."""
    date_cols = PARSE_DATES.get(table_key, [])
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")

    hints = DTYPES_HINTS.get(table_key, {})
    for col, hint in hints.items():
        if col not in df.columns:
            continue
        try:
            if hint in ("string", "str"):
                df[col] = df[col].astype("string")
            elif hint == "Int64":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            elif hint in ("float", "numeric"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif hint in ("boolean", "bool"):
                df[col] = df[col].map(
                    lambda v: True if str(v).strip().lower() in ("1", "true", "t", "yes", "y")
                    else (False if str(v).strip().lower() in ("0", "false", "f", "no", "n") else pd.NA)
                ).astype("boolean")
        except Exception:
            pass

    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = (
            df[c].astype("string")
                 .str.strip()
                 .replace({"": pd.NA, "NA": pd.NA, "NULL": pd.NA})
        )
    return df


@st.cache_data(show_spinner=False)
def load_table(table_key: str, where_clause: str = None, chunksize: int = None) -> pd.DataFrame:
    """Load a single table into a DataFrame."""
    engine = get_engine()
    table = TABLE_NAMES[table_key]
    q = f"SELECT * FROM {SCHEMA}.{table}"
    if where_clause:
        q += f" WHERE {where_clause}"

    if chunksize:
        parts = []
        for chunk in pd.read_sql_query(q, engine, chunksize=chunksize):
            parts.append(_apply_hints(chunk, table_key))
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    else:
        df = pd.read_sql_query(q, engine)
        return _apply_hints(df, table_key)


@st.cache_data(show_spinner=False)
def load_tables(keys: list[str], where_clause: str = None):
    """Load multiple tables into a dict of DataFrames."""
    dfs = {}
    for k in keys:
        dfs[k] = load_table(k, where_clause=where_clause)
    return dfs