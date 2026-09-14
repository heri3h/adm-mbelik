import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timedelta
from app import app, db
from models import DailyAdMetric
from services.gam_service import GAMService
from services.google_ads_service import GoogleAdsService

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def login_client(client, username="admin", password="admin123"):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def test_derived_metrics_calculation():
    """Menguji keakuratan perhitungan metrik CTR, Fill Rate, dan RPM."""
    metric = DailyAdMetric(
        date=datetime.now().date(),
        source="GAM",
        revenue=150.0,
        impressions=50000,
        clicks=1000,
        ad_requests=60000,
        matched_requests=54000
    )
    metric.calculate_derived_metrics()

    assert metric.ctr == 2.0
    assert metric.fill_rate == 90.0
    assert metric.rpm == 3.0

def test_derived_metrics_zero_division():
    """Menguji proteksi pembagian dengan nol pada metrik turunan."""
    metric = DailyAdMetric(
        date=datetime.now().date(),
        source="GAM",
        revenue=0.0,
        impressions=0,
        clicks=0,
        ad_requests=0,
        matched_requests=0
    )
    metric.calculate_derived_metrics()

    assert metric.ctr == 0.0
    assert metric.fill_rate == 0.0
    assert metric.rpm == 0.0

def test_gam_service_mock_generation():
    """Menguji penarikan data mock dari GAM Service."""
    service = GAMService()
    start_date = datetime.now().date() - timedelta(days=5)
    end_date = datetime.now().date() - timedelta(days=1)
    
    records = service.fetch_daily_report(start_date, end_date)
    assert len(records) == 5
    first = records[0]
    assert "revenue" in first
    assert "impressions" in first
    assert "clicks" in first
    assert "ad_requests" in first
    assert "matched_requests" in first
    assert first["source"] == "GAM"

def test_google_ads_service_mock_generation():
    """Menguji penarikan data mock dari Google Ads Service."""
    service = GoogleAdsService()
    start_date = datetime.now().date() - timedelta(days=3)
    end_date = datetime.now().date() - timedelta(days=1)

    records = service.fetch_daily_report(start_date, end_date)
    assert len(records) == 3
    assert records[0]["source"] == "Google Ads"

def test_login_protection_redirect(client):
    """Menguji bahwa user tanpa login dialihkan ke halaman /login."""
    res = client.get('/', follow_redirects=False)
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

def test_login_success_and_logout(client):
    """Menguji proses login berhasil dan logout."""
    res = login_client(client, "admin", "admin123")
    assert res.status_code == 200
    assert b"Ad Profit & Metrics Dashboard" in res.data

    logout_res = client.get('/logout', follow_redirects=True)
    assert b"Login - Ad Performance Dashboard" in logout_res.data

def test_api_status_endpoint_after_login(client):
    """Menguji response endpoint /api/status setelah login."""
    login_client(client)
    res = client.get('/api/status')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "online"

def test_api_sync_and_summary_after_login(client):
    """Menguji alur sinkronisasi API dan pembacaan /api/summary setelah login."""
    login_client(client)
    sync_res = client.post('/api/sync', json={"days": 7})
    assert sync_res.status_code == 200
    assert sync_res.get_json()["success"] is True

    summary_res = client.get('/api/summary?days=7')
    assert summary_res.status_code == 200
    summary_data = summary_res.get_json()["summary"]

    assert summary_data["total_revenue"] > 0
    assert summary_data["total_impressions"] > 0

def test_api_timeseries_and_details_after_login(client):
    """Menguji endpoint timeseries dan daily-details setelah login."""
    login_client(client)
    client.post('/api/sync', json={"days": 5})

    ts_res = client.get('/api/timeseries?days=5')
    assert ts_res.status_code == 200
    ts_data = ts_res.get_json()
    assert "dates" in ts_data

    dt_res = client.get('/api/daily-details?days=5')
    assert dt_res.status_code == 200
    dt_data = dt_res.get_json()
    assert isinstance(dt_data, list)
