import urllib.parse
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

from .config import SERVER, PORT, DATABASE, DRIVER, SCHEMA, TABLE_NAMES, PARSE_DATES, DTYPES_HINTS

def _apply_hints(df: pd.DataFrame, table_key: str) -> pd.DataFrame:
    date_cols = PARSE_DATES.get(table_key, [])
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    hints = DTYPES_HINTS.get(table_key, {})
    for col, hint in hints.items():
        if col not in df.columns:
            continue
        try:
            if hint in ("string","str"):
                df[col] = df[col].astype("string")
            elif hint == "Int64":
                df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            elif hint in ("float","numeric"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif hint in ("boolean","bool"):
                df[col] = df[col].map(
                    lambda v: True if str(v).strip().lower() in ("1","true","t","yes","y")
                    else (False if str(v).strip().lower() in ("0","false","f","no","n") else pd.NA)
                ).astype("boolean")
        except Exception:
            pass
    for c in df.select_dtypes(include=["object","string"]).columns:
        df[c] = (
            df[c].astype("string")
                 .str.strip()
                 .replace({"": pd.NA, "NA": pd.NA, "NULL": pd.NA})
        )
    return df

@st.cache_resource
def get_engine():
    if "," in SERVER or "\\" in SERVER:
        server_fragment = SERVER
    else:
        server_fragment = f"{SERVER},{PORT}"
    odbc_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={server_fragment};"
        f"DATABASE={DATABASE};"
        "Trusted_Connection=yes;"
        "Encrypt=no;"
    )
    quoted = urllib.parse.quote_plus(odbc_str)
    connection_url = f"mssql+pyodbc:///?odbc_connect={quoted}"
    return create_engine(connection_url, fast_executemany=True)

@st.cache_data(show_spinner=False)
def load_table(table_key: str, where_clause: str = None, chunksize: int = None) -> pd.DataFrame:
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
    dfs = {}
    for k in keys:
        dfs[k] = load_table(k, where_clause=where_clause)
    return dfs