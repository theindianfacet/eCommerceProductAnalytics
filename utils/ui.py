import streamlit as st

def safe_rerun():
    """
    Call Streamlit's rerun API safely across versions.
    """
    # Newer versions
    if hasattr(st, "rerun"):
        st.rerun()
        return
    # Older versions
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
        return
    # Fallback: reload browser
    st.markdown("<script>window.location.reload()</script>", unsafe_allow_html=True)
    st.stop()