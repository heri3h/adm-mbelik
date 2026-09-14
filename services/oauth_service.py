import os
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
from config import Config

# Scopes yang dibutuhkan untuk Google Ad Manager & Google Ads
SCOPES = [
    'https://www.googleapis.com/auth/dfp',              # GAM API Scope
    'https://www.googleapis.com/auth/adwords'            # Google Ads API Scope
]

def get_google_oauth_flow():
    """Membuat instance Flow OAuth 2.0 Google."""
    client_config = {
        "web": {
            "client_id": Config.GOOGLE_CLIENT_ID.strip(),
            "client_secret": Config.GOOGLE_CLIENT_SECRET.strip(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [Config.GOOGLE_REDIRECT_URI.strip()]
        }
    }
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = Config.GOOGLE_REDIRECT_URI.strip()
    return flow

def get_authorization_url():
    """Mendapatkan URL login Google OAuth 2.0 untuk user."""
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return None, "Client ID dan Client Secret belum dikonfigurasi di file .env"
    
    try:
        flow = get_google_oauth_flow()
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state
    except Exception as e:
        return None, f"Gagal membuat Flow OAuth: {str(e)}"

def get_credentials_from_code(code):
    """Menukar authorization code dari callback menjadi credential token."""
    try:
        flow = get_google_oauth_flow()
        flow.fetch_token(code=code)
        return flow.credentials
    except Exception as e:
        print(f"[OAuth Error] Fetch token failed: {e}")
        return None

def get_oauth_credentials():
    """Mendapatkan Credentials dari Refresh Token yang ada di environment."""
    if Config.GOOGLE_REFRESH_TOKEN and Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
        return Credentials(
            token=None,
            refresh_token=Config.GOOGLE_REFRESH_TOKEN.strip(),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.GOOGLE_CLIENT_ID.strip(),
            client_secret=Config.GOOGLE_CLIENT_SECRET.strip(),
            scopes=SCOPES
        )
    return None
