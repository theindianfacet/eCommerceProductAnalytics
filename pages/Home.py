import streamlit as st
import yaml
from yaml.loader import SafeLoader
from utils.auth_state import ensure_session_keys, mark_activity, logout_and_redirect, check_timeout
from utils.db import load_tables
from utils.agg import compute_conversion_rate
from utils.formatters import format_number, format_currency

# Do NOT call st.set_page_config here

# Role → allowed dashboards mapping
ROLE_DASHBOARDS = {
    "admin": [
        "pages/1_Traffic_and_Acquisition.py",
        "pages/2_Channel_Performance_and_Trends.py",
        "pages/3_Channel_Quality_Metrics.py",
        "pages/4_Attribution_Analysis.py",
        "pages/5_Conversion_Journey.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/7_Product_Performance.py",
        "pages/8_User_Engagement.py",
        "pages/9_Customer_Insights.py",
    ],
    "ceo": [
        "pages/1_Traffic_and_Acquisition.py",
        "pages/2_Channel_Performance_and_Trends.py",
        "pages/7_Product_Performance.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/9_Customer_Insights.py",
    ],
    "website_manager": [
        "pages/3_Channel_Quality_Metrics.py",
        "pages/5_Conversion_Journey.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/2_Channel_Performance_and_Trends.py",
    ],
    "marketing_manager": [
        "pages/1_Traffic_and_Acquisition.py",
        "pages/2_Channel_Performance_and_Trends.py",
        "pages/3_Channel_Quality_Metrics.py",
        "pages/4_Attribution_Analysis.py",
        "pages/8_User_Engagement.py",
    ],
}

def render(authenticator=None, config=None):
    """
    Render the Home page (homepage + role-aware navigation).
    """
    ensure_session_keys()
    check_timeout(threshold_minutes=3)
    mark_activity()

    # Load config if not passed
    if config is None:
        with open("config.yaml") as f:
            config = yaml.load(f, Loader=SafeLoader)

    authentication_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")
    name = st.session_state.get("name")

    # Guard: must be logged in
    if not authentication_status:
        st.warning("⚠️ Session expired or not authenticated. Please log in again.")
        logout_and_redirect(authenticator=authenticator, target="Login")
        return

    # Sidebar: welcome + logout
    st.sidebar.success(f"Welcome {name} 👋")

    if st.sidebar.button("Logout"):
        logout_and_redirect(authenticator=authenticator, target="Login")

    # Role lookup
    role = config["credentials"]["usernames"][username]["role"]

    # Data load
    dfs = load_tables(["website_sessions", "orders"])
    sessions = dfs["website_sessions"]
    orders = dfs["orders"]

    # KPIs
    total_sessions = len(sessions)
    total_orders = len(orders)
    total_revenue = orders["price_usd"].sum()
    conv_rate = compute_conversion_rate(sessions, orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    repeat_rate = (orders.groupby("user_id")["order_id"].nunique() >= 2).mean()

    # Homepage content
    st.title("🧸 Analytics Hub")
# =============================================================================
#     st.markdown(
#         """
#         Welcome to your centralized analytics hub.  
#         Gain clarity on acquisition, channel performance, conversion journeys, product paths, and customer insights — all in one place.
#         """
#     )
#     st.markdown("---")
# =============================================================================

    # Role-specific homepage KPIs
    if role == "admin":
        #st.info("Admin: full access to all dashboards and KPIs.")
        k1, k2, k3 = st.columns(3)
        k1.metric("🖥️ Sessions", format_number(total_sessions))
        k2.metric("📦 Orders", format_number(total_orders))
        k3.metric("💵 Revenue", format_currency(total_revenue))
        k4, k5, k6 = st.columns(3)
        k4.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")
        k5.metric("📊 Average Order Value", f"${avg_order_value:,.2f}")
        k6.metric("🔄 Repeat Rate", f"{repeat_rate*100:.2f}%")

    elif role == "ceo":
        #st.info("CEO: strategic KPIs overview.")
        k1, k2, k3 = st.columns(3)
        k1.metric("💵 Revenue", format_currency(total_revenue))
        k2.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")
        k3.metric("📊 Average Order Value", f"${avg_order_value:,.2f}")

    elif role == "website_manager":
        #st.info("Website Manager: operational metrics and funnel optimization.")
        k1, k2 = st.columns(2)
        k1.metric("🖥️ Sessions", format_number(total_sessions))
        k2.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")

    elif role == "marketing_manager":
        #st.info("Marketing Manager: campaign effectiveness and engagement.")
        k1, k2, k3 = st.columns(3)
        k1.metric("🖥️ Sessions", format_number(total_sessions))
        k2.metric("🔄 Repeat Rate", f"{repeat_rate*100:.2f}%")
        k3.metric("💬 Engagement Rate", f"{conv_rate*100:.2f}%")

    else:
        st.error("Your role does not have a configured homepage.")

    st.markdown("---")
    
    #st.subheader("📂 Dashboards")
    # --- Role-aware navigation ---
    PAGES_MAP = {
        "pages/1_Traffic_and_Acquisition.py": st.Page(
            "pages/1_Traffic_and_Acquisition.py", title="Traffic & Acquisition", icon="🌐"
        ),
        "pages/2_Channel_Performance_and_Trends.py": st.Page(
            "pages/2_Channel_Performance_and_Trends.py", title="Channel Performance & Trends", icon="📈"
        ),
        "pages/3_Channel_Quality_Metrics.py": st.Page(
            "pages/3_Channel_Quality_Metrics.py", title="Channel Quality Metrics", icon="🧪"
        ),
        "pages/4_Attribution_Analysis.py": st.Page(
            "pages/4_Attribution_Analysis.py", title="Attribution Analysis", icon="🧭"
        ),
        "pages/5_Conversion_Journey.py": st.Page(
            "pages/5_Conversion_Journey.py", title="Conversion Journey", icon="🛤️"
        ),
        "pages/6_Product_Journey_Flows.py": st.Page(
            "pages/6_Product_Journey_Flows.py", title="Product Journey Flows", icon="📦"
        ),
        "pages/7_Product_Performance.py": st.Page(
            "pages/7_Product_Performance.py", title="Product Performance", icon="💰"
        ),
        "pages/8_User_Engagement.py": st.Page(
            "pages/8_User_Engagement.py", title="User Engagement", icon="👥"
        ),
        "pages/9_Customer_Insights.py": st.Page(
            "pages/9_Customer_Insights.py", title="Customer Insights", icon="🧠"
        ),
    }

    allowed_pages = ROLE_DASHBOARDS.get(role, [])
    role_pages = [PAGES_MAP[p] for p in allowed_pages if p in PAGES_MAP]

    nav = st.navigation({"📂 Dashboards": role_pages})
    nav.run()
    
    st.markdown("---")
    
    st.markdown("**© 2025 digitAL Analytics | Developed by Team 5**")