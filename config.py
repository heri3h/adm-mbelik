import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///ad_metrics.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Dashboard Access Credentials
    DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin")
    DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
    REQUIRE_LOGIN = os.getenv("REQUIRE_LOGIN", "True").lower() in ["true", "1", "t"]

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://adm.mbelik.com/auth/callback")
    GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN", "")

    # Google Ad Manager
    GAM_NETWORK_CODE = os.getenv("GAM_NETWORK_CODE", "")
    GAM_APPLICATION_NAME = os.getenv("GAM_APPLICATION_NAME", "AdManagerDashboard")

    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    GOOGLE_ADS_CUSTOMER_ID = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "")

    # Flag mode Mock
    USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "True").lower() in ["true", "1", "t"]
