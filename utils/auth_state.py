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

# =============================================================================
# def check_timeout(threshold_minutes=3):
#     """
#     Check if user has been idle longer than threshold.
#     If so, clear auth state and force rerun to Login.
#     """
#     now = time.time()
#     last = st.session_state.get("last_activity_ts", now)
#     if now - last > threshold_minutes * 60:
#         # Expired → clear auth state
#         st.session_state["authentication_status"] = None
#         st.session_state["username"] = None
#         st.session_state["name"] = None
#         st.session_state["email"] = None
#         st.sidebar.empty()
#         st.warning("⚠️ Session timed out due to inactivity. Please log in again.")
#         st.rerun()
# =============================================================================
        
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

# =============================================================================
#     # Clear session state keys
#     for k in ["authentication_status", "username", "name", "last_activity_ts", "nav_active","username_input",
#         "password_input",
#         "login"]:
#         if k in st.session_state:
#             del st.session_state[k]
# =============================================================================
# =============================================================================
#     # Wipe ALL session state
#     for k in list(st.session_state.keys()):
#         del st.session_state[k]
# 
#     # Explicitly clear login form autofill keys
#     for k in ["username_input", "password_input", "login"]:
#         if k in st.session_state:
#             del st.session_state[k]
# =============================================================================

    # Wipe ALL session state
    st.session_state.clear()

     # Clear sidebar content explicitly
    st.sidebar.empty()
    


# =============================================================================
#     if "nav_active" in st.session_state:
#         st.session_state["nav_active"] = False
#     if "nav" in st.session_state:
#         del st.session_state["nav"]
# =============================================================================

# =============================================================================
#     # Redirect to target page
#     try:
#         st.switch_page(target)
#     except Exception:
#         # Fallback: rerun app.py router
#         st.rerun()
# 
#     st.stop()
# =============================================================================
    
    
    # --- My additions ---
    # Reset nav flags so router knows to go back to Login
    st.session_state["nav_active"] = False
    st.session_state["nav"] = target

    #force_reload()
    #components.html("<script>window.location.reload()</script>", height=0)
    #st.session_state["force_sidebar_collapsed"] = True
    
    # --- Add this: force-hide sidebar on next run ---
    #st.session_state["force_hide_sidebar"] = True
    
    # Force rerun so app.py router starts fresh (Login page)
    st.rerun()

