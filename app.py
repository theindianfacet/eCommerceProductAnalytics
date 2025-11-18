
# =============================================================================
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# 
# from utils.db import load_tables
# from utils.filters import sidebar_filters
# from utils.agg import filter_sessions, filter_orders, compute_conversion_rate
# from utils.formatters import format_number, format_currency, format_percent
# 
# # --- Page setup ---
# st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide")
# st.title("📊 e-Commerce Product Analytics")
# st.markdown("Welcome to the analytics hub. Explore acquisition, channel performance, funnels, product paths, and customer insights.")
# 
# # --- Filters & Data ---
# F = sidebar_filters()
# dfs = load_tables(["website_sessions","orders"])
# sessions = filter_sessions(dfs["website_sessions"], F)
# orders = filter_orders(dfs["orders"], F)
# 
# # --- Global KPIs ---
# total_sessions = len(sessions)
# total_orders = len(orders)
# total_revenue = orders["price_usd"].sum()
# conv_rate = compute_conversion_rate(sessions, orders)
# avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
# repeat_rate = (orders.groupby("user_id")["order_id"].nunique() >= 2).mean()
# 
# k1, k2, k3, k4 = st.columns(4)
# k1.metric("Total Sessions", format_number(total_sessions))
# k2.metric("Total Orders", format_number(total_orders))
# k3.metric("Total Revenue", format_currency(total_revenue))
# k4.metric("Conversion Rate", f"{conv_rate*100:.2f}%")   
# 
# k5, k6 = st.columns(2)
# k5.metric("Average Order Value", f"${avg_order_value:,.2f}")   
# k6.metric("Repeat Purchase Rate", f"{repeat_rate*100:.2f}%")   
# 
# # --- Navigation Hub ---
# st.subheader("Explore Dashboards")
# st.page_link("pages/1_Traffic_&_Acquisition.py", label="Traffic Acquisition", icon="🌐")
# st.page_link("pages/2_Channel_Performance_&_Trends.py", label="Channel Performance & Trends", icon="📈")
# st.page_link("pages/3_Channel_Quality_Metrics.py", label="Channel Quality Metrics", icon="⚙️")
# st.page_link("pages/4_Attribution_Analysis.py", label="Attribution Analysis", icon="🔗")
# st.page_link("pages/5_Conversion_Journey.py", label="Conversion Journey", icon="➡️")
# st.page_link("pages/6_Product_Journey_Flows.py", label="Product Journey Flows", icon="🛒")
# st.page_link("pages/7_Product_Performance.py", label="Product Performance & Revenue", icon="📦")
# st.page_link("pages/8_User_Engagement.py", label="User Engagement", icon="💬")
# st.page_link("pages/9_Customer_Insights.py", label="Customer Insights", icon="👥")
# 
# st.markdown("---")
# st.markdown("**Developed by: Divyansh Sharma**")
# =============================================================================

# =============================================================================
# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import yaml
# from yaml.loader import SafeLoader
# import streamlit_authenticator as stauth
# 
# from utils.db import load_tables
# from utils.filters import sidebar_filters
# from utils.agg import filter_sessions, filter_orders, compute_conversion_rate
# from utils.formatters import format_number, format_currency, format_percent
# 
# # --- Page setup (must be first Streamlit command) ---
# st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide")
# 
# # --- Load config.yaml securely ---
# with open('config.yaml') as file:
#     config = yaml.load(file, Loader=SafeLoader)
# 
# # --- Authenticator setup ---
# authenticator = stauth.Authenticate(
#     config['credentials'],
#     config['cookie']['name'],
#     config['cookie']['key'],
#     config['cookie']['expiry_days']
# )
# 
# # --- Login widget (new API style) ---
# authenticator.login(location="main")
# authenticator.logout("Logout", "sidebar")
# 
# # --- Role-based dashboard mapping ---
# ROLE_DASHBOARDS = {
#     "admin": [
#         "pages/1_Traffic_&_Acquisition.py",
#         "pages/2_Channel_Performance_&_Trends.py",
#         "pages/3_Channel_Quality_Metrics.py",
#         "pages/4_Attribution_Analysis.py",
#         "pages/5_Conversion_Journey.py",
#         "pages/6_Product_Journey_Flows.py",
#         "pages/7_Product_Performance.py",
#         "pages/8_User_Engagement.py",
#         "pages/9_Customer_Insights.py"
#     ],
#     "ceo": [
#         "pages/1_Traffic_&_Acquisition.py",
#         "pages/2_Channel_Performance_&_Trends.py",
#         "pages/7_Product_Performance.py",
#         "pages/6_Product_Journey_Flows.py",
#         "pages/9_Customer_Insights.py"
#     ],
#     "website_manager": [
#         "pages/3_Channel_Quality_Metrics.py",
#         "pages/5_Conversion_Journey.py",
#         "pages/6_Product_Journey_Flows.py",
#         "pages/2_Channel_Performance_&_Trends.py"
#     ],
#     "marketing_manager": [
#         "pages/1_Traffic_&_Acquisition.py",
#         "pages/2_Channel_Performance_&_Trends.py",
#         "pages/3_Channel_Quality_Metrics.py",
#         "pages/4_Attribution_Analysis.py",
#         "pages/8_User_Engagement.py"
#     ]
# }
# 
# # --- Authentication status handling (use st.session_state) ---
# authentication_status = st.session_state.get("authentication_status")
# name = st.session_state.get("name")
# username = st.session_state.get("username")
# 
# if authentication_status:
#     st.sidebar.success(f"Welcome {name} 👋")
#     authenticator.logout("Logout", "sidebar")
# 
#     # --- Homepage ---
#     st.title("📊 e-Commerce Product Analytics")
#     st.markdown("Welcome to the analytics hub. Explore acquisition, channel performance, funnels, product paths, and customer insights.")
# 
#     # --- Filters & Data ---
#     F = sidebar_filters()
#     dfs = load_tables(["website_sessions", "orders"])
#     sessions = filter_sessions(dfs["website_sessions"], F)
#     orders = filter_orders(dfs["orders"], F)
# 
#     # --- Global KPIs ---
#     total_sessions = len(sessions)
#     total_orders = len(orders)
#     total_revenue = orders["price_usd"].sum()
#     conv_rate = compute_conversion_rate(sessions, orders)
#     avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
#     repeat_rate = (orders.groupby("user_id")["order_id"].nunique() >= 2).mean()
# 
#     k1, k2, k3, k4 = st.columns(4)
#     k1.metric("Total Sessions", format_number(total_sessions))
#     k2.metric("Total Orders", format_number(total_orders))
#     k3.metric("Total Revenue", format_currency(total_revenue))
#     k4.metric("Conversion Rate", f"{conv_rate*100:.2f}%")
# 
#     k5, k6 = st.columns(2)
#     k5.metric("Average Order Value", f"${avg_order_value:,.2f}")
#     k6.metric("Repeat Purchase Rate", f"{repeat_rate*100:.2f}%")
# 
#     # --- Navigation Hub ---
#     st.subheader("Explore Dashboards")
# 
#     role = config['credentials']['usernames'][username]['role']
#     allowed_pages = ROLE_DASHBOARDS.get(role, [])
# 
#     for page in allowed_pages:
#         if "1_Traffic_&_Acquisition" in page:
#             st.page_link(page, label="Traffic & Acquisition", icon="🌐")
#         elif "2_Channel_Performance_&_Trends" in page:
#             st.page_link(page, label="Channel Performance & Trends", icon="📈")
#         elif "3_Channel_Quality_Metrics" in page:
#             st.page_link(page, label="Channel Quality Metrics", icon="⚙️")
#         elif "4_Attribution_Analysis" in page:
#             st.page_link(page, label="Attribution Analysis", icon="🔗")
#         elif "5_Conversion_Journey" in page:
#             st.page_link(page, label="Conversion Journey", icon="➡️")
#         elif "6_Product_Journey_Flows" in page:
#             st.page_link(page, label="Product Journey Flows", icon="🛒")
#         elif "7_Product_Performance" in page:
#             st.page_link(page, label="Product Performance & Revenue", icon="📦")
#         elif "8_User_Engagement" in page:
#             st.page_link(page, label="User Engagement", icon="💬")
#         elif "9_Customer_Insights" in page:
#             st.page_link(page, label="Customer Insights", icon="👥")
# 
#     st.markdown("---")
#     st.markdown("**Developed by: Team 5**")
# 
# elif authentication_status is False:
#     st.error("Username/password is incorrect")
# 
# elif authentication_status is None:
#     st.warning("Please enter your username and password")
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from utils.db import load_tables
from utils.filters import sidebar_filters
from utils.agg import filter_sessions, filter_orders, compute_conversion_rate
from utils.formatters import format_number, format_currency, format_percent

# --- Page setup (must be first Streamlit command) ---
st.set_page_config(page_title="e-Commerce Product Analytics", layout="wide")

# --- Load config.yaml securely ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# --- Authenticator setup ---
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# --- Login widget (new API style) ---
authenticator.login(location="main")
#authenticator.logout("Logout", "sidebar")

# --- Role-based dashboard mapping ---
ROLE_DASHBOARDS = {
    "admin": [
        "pages/1_Traffic_&_Acquisition.py",
        "pages/2_Channel_Performance_&_Trends.py",
        "pages/3_Channel_Quality_Metrics.py",
        "pages/4_Attribution_Analysis.py",
        "pages/5_Conversion_Journey.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/7_Product_Performance.py",
        "pages/8_User_Engagement.py",
        "pages/9_Customer_Insights.py"
    ],
    "ceo": [
        "pages/1_Traffic_&_Acquisition.py",
        "pages/2_Channel_Performance_&_Trends.py",
        "pages/7_Product_Performance.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/9_Customer_Insights.py"
    ],
    "website_manager": [
        "pages/3_Channel_Quality_Metrics.py",
        "pages/5_Conversion_Journey.py",
        "pages/6_Product_Journey_Flows.py",
        "pages/2_Channel_Performance_&_Trends.py"
    ],
    "marketing_manager": [
        "pages/1_Traffic_&_Acquisition.py",
        "pages/2_Channel_Performance_&_Trends.py",
        "pages/3_Channel_Quality_Metrics.py",
        "pages/4_Attribution_Analysis.py",
        "pages/8_User_Engagement.py"
    ]
}

# --- Authentication status handling (use st.session_state) ---
authentication_status = st.session_state.get("authentication_status")
name = st.session_state.get("name")
username = st.session_state.get("username")

if authentication_status:
    # Clear default sidebar navigation
    st.sidebar.empty()
    st.sidebar.success(f"Welcome {name} 👋")
    authenticator.logout("Logout", "sidebar")

    # --- Homepage ---
    st.title("📊 e-Commerce Analytics Hub")
    st.markdown("""
                Welcome to your centralized analytics hub.  
                Gain clarity on acquisition, channel performance, conversion journeys, product paths, and customer insights — all in one place.
                """)

    st.markdown("---") 
    
    # --- Filters & Data ---
    #F = sidebar_filters()
    dfs = load_tables(["website_sessions", "orders"])
    #sessions = filter_sessions(dfs["website_sessions"], F)
    #orders = filter_orders(dfs["orders"], F)
    sessions = dfs["website_sessions"]
    orders = dfs["orders"]

    # --- Global KPIs ---
    total_sessions = len(sessions)
    total_orders = len(orders)
    total_revenue = orders["price_usd"].sum()
    conv_rate = compute_conversion_rate(sessions, orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    repeat_rate = (orders.groupby("user_id")["order_id"].nunique() >= 2).mean()

    # --- Role-specific homepage ---
    role = config['credentials']['usernames'][username]['role']
    
    if role == "admin":
        #st.subheader("👨‍💼 Admin Homepage")
        st.info("Welcome Team Member! As admin, you have full access to all dashboards and KPIs.")
    
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🖥️ Total Sessions", format_number(total_sessions))
        k2.metric("📦 Total Orders", format_number(total_orders))
        k3.metric("💵 Total Revenue", format_currency(total_revenue))
        k4.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")
        
        k5, k6 = st.columns(2)
        k5.metric("📊 Average Order Value", f"${avg_order_value:,.2f}")
        k6.metric("🔄 Repeat Purchase Rate", f"{repeat_rate*100:.2f}%")
        
        st.markdown("---") 
        
        st.subheader("🔮 What to Expect")
        st.info("""
        - Traffic Acquisition trends
        - Channel performance & attribution
        - Conversion funnels
        - Product paths & performance
        - Engagement & customer insights
        """)
    
    elif role == "ceo":
        # st.subheader("👔 Homepage")
        st.info("Welcome Cindy! Your homepage highlights **strategic KPIs**.")
    
        k1, k2, k3 = st.columns(3)
        k1.metric("💵 Total Revenue", format_currency(total_revenue))
        k2.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")
        k3.metric("📊 Average Order Value", f"${avg_order_value:,.2f}")
    
        st.markdown("---") 
        
        st.subheader("🔮 What to Expect")
        st.info("""
        - High-level traffic & acquisition
        - Channel performance trends
        - Product performance & revenue
        - Customer insights
        """)
    
    elif role == "website_manager":
        # st.subheader("🌐 Website Manager Homepage")
        st.info("Welcome Morgan! Your homepage emphasizes **operational metrics and funnel optimization**.")
    
        k1, k2 = st.columns(2)
        k1.metric("🖥️ Total Sessions", format_number(total_sessions))
        k2.metric("✅ Conversion Rate", f"{conv_rate*100:.2f}%")
    
        st.markdown("---") 
        
        st.subheader("🔮 What to Expect")
        st.info("""
        - Channel quality metrics
        - Conversion funnels
        - Product path flows
        - Channel performance trends
        """)
    
    elif role == "marketing_manager":
        # st.subheader("📣 Marketing Manager Homepage")
        st.info("Welcome Tom! Your homepage highlights **campaign effectiveness and engagement**.")
    
        k1, k2, k3 = st.columns(3)
        k1.metric("🖥️ Total Sessions", format_number(total_sessions))
        k2.metric("🔄 Repeat Purchase Rate", f"{repeat_rate*100:.2f}%")
        k3.metric("💬 Engagement Rate", f"{conv_rate*100:.2f}%")
    
        st.markdown("---") 
        st.subheader("🔮 What to Expect")
        st.info("""
        - Traffic acquisition & campaign reach
        - Channel performance & characteristics
        - Attribution analysis
        - Engagement behavior
        """)
    
    else:
        st.subheader("🔒 Restricted Access")
        st.error("Your role does not have a configured homepage.")
    
    
    # --- Navigation Hub (links remain intact on homepage) ---
    st.markdown("---") 
    st.subheader("Explore Dashboards")
    
    allowed_pages = ROLE_DASHBOARDS.get(role, [])
    for page in allowed_pages:
        if "1_Traffic_&_Acquisition" in page:
            st.page_link(page, label="Traffic & Acquisition", icon="🌐")
        elif "2_Channel_Performance_&_Trends" in page:
            st.page_link(page, label="Channel Performance & Trends", icon="📈")
        elif "3_Channel_Quality_Metrics" in page:
            st.page_link(page, label="Channel Quality Metrics", icon="⚙️")
        elif "4_Attribution_Analysis" in page:
            st.page_link(page, label="Attribution Analysis", icon="🔗")
        elif "5_Conversion_Journey" in page:
            st.page_link(page, label="Conversion Journey", icon="➡️")
        elif "6_Product_Journey_Flows" in page:
            st.page_link(page, label="Product Journey Flows", icon="🛒")
        elif "7_Product_Performance" in page:
            st.page_link(page, label="Product Performance & Revenue", icon="📦")
        elif "8_User_Engagement" in page:
            st.page_link(page, label="User Engagement", icon="💬")
        elif "9_Customer_Insights" in page:
            st.page_link(page, label="Customer Insights", icon="👥")
    
    # --- Sidebar Role-Based Navigation ---
    st.sidebar.subheader("📂 Dashboards")
    for page in allowed_pages:
        if "1_Traffic_&_Acquisition" in page:
            st.sidebar.page_link(page, label="Traffic & Acquisition", icon="🌐")
        elif "2_Channel_Performance_&_Trends" in page:
            st.sidebar.page_link(page, label="Channel Performance & Trends", icon="📈")
        elif "3_Channel_Quality_Metrics" in page:
            st.sidebar.page_link(page, label="Channel Quality Metrics", icon="⚙️")
        elif "4_Attribution_Analysis" in page:
            st.sidebar.page_link(page, label="Attribution Analysis", icon="🔗")
        elif "5_Conversion_Journey" in page:
            st.sidebar.page_link(page, label="Conversion Journey", icon="➡️")
        elif "6_Product_Journey_Flows" in page:
            st.sidebar.page_link(page, label="Product Journey Flows", icon="🛒")
        elif "7_Product_Performance" in page:
            st.sidebar.page_link(page, label="Product Performance & Revenue", icon="📦")
        elif "8_User_Engagement" in page:
            st.sidebar.page_link(page, label="User Engagement", icon="💬")
        elif "9_Customer_Insights" in page:
            st.sidebar.page_link(page, label="Customer Insights", icon="👥")
    
    st.markdown("---")
    st.markdown("**© 2025 digitAL Analytics | Developed by Team 5**")

elif authentication_status is False:
    st.error("Username/password is incorrect")

elif authentication_status is None:
    st.warning("Please enter your username and password")