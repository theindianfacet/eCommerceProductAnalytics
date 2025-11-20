import streamlit as st
import yaml
from yaml.loader import SafeLoader
from utils.auth_state import ensure_session_keys, mark_activity, check_timeout

def render(authenticator=None, config=None):
    # Render the Login page
    ensure_session_keys()
    check_timeout(threshold_minutes=3)
    mark_activity()
    
    # Clear any sidebar content so Login page is clean
    st.sidebar.empty()
    if "nav" in st.session_state:
        del st.session_state["nav"]
    
    st.title("digitAL Analytics")

    # If authenticator not passed, build one from config
    if authenticator is None and config is not None:
        import streamlit_authenticator as stauth
        authenticator = stauth.Authenticate(
            config["credentials"],
            config["cookie"]["name"],
            config["cookie"]["key"],
            config["cookie"]["expiry_days"],
        )

    if authenticator is None:
        st.error("Authenticator not available. Check app.py wiring.")
        return

    # Render login widget
    authenticator.login(location="main")

    authentication_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")

    if authentication_status:
        st.success(f"Welcome {name} 👋")
        # Reset nav_active so Home can activate navigation
        st.session_state["nav_active"] = False
        # Trigger rerun so app.py router will render Home next
        st.rerun()
    elif authentication_status is False:
        st.error("Username/password is incorrect")
    else:
        st.info("Please enter your username and password")