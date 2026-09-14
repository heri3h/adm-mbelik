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
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
        }
    }
    
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    flow.redirect_uri = Config.GOOGLE_REDIRECT_URI
    return flow

def get_authorization_url():
    """Mendapatkan URL login Google OAuth 2.0 untuk user."""
    if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
        return None, "Client ID dan Client Secret belum dikonfigurasi di file .env"
    
    flow = get_google_oauth_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return authorization_url, state

def get_credentials_from_code(code):
    """Menukar authorization code dari callback menjadi credential token."""
    flow = get_google_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials

def get_oauth_credentials():
    """Mendapatkan Credentials dari Refresh Token yang ada di environment."""
    if Config.GOOGLE_REFRESH_TOKEN and Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET:
        return Credentials(
            token=None,
            refresh_token=Config.GOOGLE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )
    return None
