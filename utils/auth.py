import os
import streamlit as st

def enforce_access(role: str, allowed_pages: list[str], current_file: str):
    """Block access if current page not allowed for this role."""
    # Normalize both sides to just the filename
    allowed_files = [os.path.basename(p) for p in allowed_pages]
    current_file = os.path.basename(current_file)

    if current_file not in allowed_files:
        st.subheader("🔒 Restricted Access")
        st.error("🚫 You do not have permission to view this dashboard.")
        st.stop()