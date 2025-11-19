import time
import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from utils.auth_state import (
    ensure_session_keys,
    mark_activity,
    is_session_expired,
    logout_and_redirect,
    check_timeout
)
from pages import Login, Home   # pages/__init__.py must exist

# Decide initial sidebar state based on session (if session not initialized, assume collapsed)
#auth = False
if "authentication_status" in st.session_state:
    auth = bool(st.session_state.get("authentication_status"))

# --- Page setup (only once, first Streamlit command) ---
# =============================================================================
# st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide",
#                    initial_sidebar_state="expanded" if auth else "collapsed")
# =============================================================================
st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide",
                   initial_sidebar_state="collapsed")
st.sidebar.empty()

# =============================================================================
# # Add a flag check so that after logout the sidebar is guaranteed collapsed.
# force_collapsed = st.session_state.get("force_sidebar_collapsed", False)
# if force_collapsed:
#     # Reset flag after use
#     del st.session_state["force_sidebar_collapsed"]
#     # Sidebar will remain collapsed on rerun because of global page_config above.
# 
# =============================================================================

# =============================================================================
# # --- Suggestion: hide sidebar via CSS when logged out or explicitly flagged ---
# hide_sidebar = (
#     not bool(st.session_state.get("authentication_status")) or
#     bool(st.session_state.get("force_hide_sidebar"))
# )
# if hide_sidebar:
#     st.markdown(
#         """
#         <style>
#         [data-testid="stSidebar"] { display: none !important; }
#         /* Optional: adjust main padding when sidebar is hidden */
#         [data-testid="stSidebarNav"] { display: none !important; }
#         .block-container { padding-left: 1rem; }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )
#     # Consume flag so it doesn't persist after login
#     if "force_hide_sidebar" in st.session_state:
#         del st.session_state["force_hide_sidebar"]
# =============================================================================

# --- Hide sidebar when not authenticated ---
if not st.session_state.get("authentication_status"):
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
        .block-container {padding-left: 1rem;}
        </style>
        """,
        unsafe_allow_html=True
    )


# --- Load config.yaml ---
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- Authenticator setup ---
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# --- Session and inactivity handling ---
ensure_session_keys()
INACTIVITY_TIMEOUT = 180  # 3 minutes


if is_session_expired(INACTIVITY_TIMEOUT):
    # Unified logout: clears cookie + session + redirects
    logout_and_redirect(authenticator=authenticator, target="Login")
else:
    mark_activity()
    check_timeout(threshold_minutes=3)

# --- Router ---
authentication_status = st.session_state.get("authentication_status")

if authentication_status:
    Home.render(authenticator=authenticator, config=config)
else:
    Login.render(authenticator=authenticator, config=config)