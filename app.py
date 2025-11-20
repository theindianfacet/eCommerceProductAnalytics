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

st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide",
                   initial_sidebar_state="collapsed")
st.sidebar.empty()

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

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

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