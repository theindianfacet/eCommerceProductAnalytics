# -----------------------
# CONFIG - edit as needed
# -----------------------
SERVER = "DIVYANSH\\DIVYANSH_36"
PORT = 1433
DATABASE = "DigitAL"
DRIVER = "ODBC Driver 17 for SQL Server"
SCHEMA = "dbo"

TABLE_NAMES = {
    "products": "Products",
    "website_sessions": "WebsiteSessions",
    "website_pageviews": "WebsitePageViews",
    "orders": "Orders",
    "order_items": "OrderItems",
    "order_item_refunds": "OrderItemRefunds",
}

PARSE_DATES = {
    "products": ["created_at"],
    "website_sessions": ["created_at"],
    "website_pageviews": ["created_at"],
    "orders": ["created_at"],
    "order_items": ["created_at"],
    "order_item_refunds": ["created_at"],
}

DTYPES_HINTS = {
    "products": {"product_id": "string", "product_name": "string"},
    "website_pageviews": {"website_pageview_id": "string", "website_session_id": "string", "pageview_url": "string"},
    "order_item_refunds": {"order_item_refund_id": "string", "order_item_id": "string", "order_id": "string", "refund_amount_usd": "float"},
    "website_sessions": {
        "website_session_id": "string",
        "user_id": "string",
        "is_repeat_session": "boolean",
        "utm_source": "string",
        "utm_campaign": "string",
        "utm_content": "string",
        "device_type": "string",
        "http_referer": "string",
    },
    "orders": {
        "order_id": "string",
        "website_session_id": "string",
        "user_id": "string",
        "primary_product_id": "string",
        "items_purchased": "Int64",
        "price_usd": "float",
        "cogs_usd": "float",
    },
    "order_items": {
        "order_item_id": "string",
        "order_id": "string",
        "product_id": "string",
        "is_primary_item": "boolean",
        "price_usd": "float",
        "cogs_usd": "float",
    },
}

# Categorical sets (provided by you)
PRODUCT_NAMES = [
    "The Original Mr. Fuzzy",
    "The Forever Love Bear",
    "The Birthday Sugar Panda",
    "The Hudson River Mini bear",
]
PAGEVIEW_URLS = [
    "/the-birthday-sugar-panda", "/shipping", "/lander-1", "/the-forever-love-bear",
    "/billing", "/cart", "/products", "/the-hudson-river-mini-bear", "/lander-3",
    "/billing-2", "/the-original-mr-fuzzy", "/lander-2", "/home", "/lander-4",
    "/thank-you-for-your-order", "/lander-5",
]
UTM_SOURCE = ["socialbook", "direct", "gsearch", "bsearch"]
UTM_CONTENT = ["social_ad_1", "b_ad_2", "g_ad_2", "b_ad_1", "social_ad_2", "unspecified", "g_ad_1"]
UTM_CAMPAIGN = ["brand", "unspecified", "pilot", "nonbrand", "desktop_targeted"]
DEVICE_TYPE = ["desktop", "mobile"]
HTTP_REFERRER = ["direct", "https://www.socialbook.com", "https://www.gsearch.com", "https://www.bsearch.com"]

# Default date window (override in UI)
DEFAULT_DATE_DAYS = 180