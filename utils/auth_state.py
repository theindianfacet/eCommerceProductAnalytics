import streamlit as st
import time
import streamlit.components.v1 as components

def ensure_session_keys():
    defaults = {
        "authentication_status": None,
        "username": None,
        "name": None,
        "email": None,
        "last_activity_ts": time.time(),  # only set once if missing
        "nav_active": False,
        "nav": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def mark_activity():
    st.session_state["last_activity_ts"] = time.time()
        
# --- Unified timeout check ---
def check_timeout(threshold_minutes: int = 3):
    if is_session_expired(threshold_minutes * 60):
        logout_and_redirect(target="Login")


def is_session_expired(timeout_seconds: int) -> bool:
    ts = st.session_state.get("last_activity_ts")
    if ts is None:
        st.session_state["last_activity_ts"] = time.time()
        return False
    return (time.time() - ts) > timeout_seconds

def logout_and_redirect(authenticator=None, target: str = "Login"):
    """
    Logs out the user by clearing cookies and session state,
    then redirects to the given page (default: Login).
    """
    # Clear authenticator cookie if available
    try:
        if authenticator is not None:
            #authenticator.logout("Logout", "sidebar")
            authenticator.logout("Logout", "main")
    except Exception:
        pass

    # Wipe ALL session state
    st.session_state.clear()

    # Clear sidebar content explicitly
    st.sidebar.empty()
    
    # Reset nav flags so router knows to go back to Login
    st.session_state["nav_active"] = False
    st.session_state["nav"] = target
    
    # Force rerun so app.py router starts fresh (Login page)
    st.rerun()

