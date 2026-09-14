import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timedelta
from app import app, db
from models import DailyAdMetric

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

def test_profit_and_roi_calculation():
    """Menguji keakuratan perhitungan Spend, Earning, Profit, ROI, CTR, Fill Rate, dan RPM."""
    metric = DailyAdMetric(
        date=datetime.now().date(),
        source="GAM",
        spend=50.0,
        revenue=150.0,
        impressions=50000,
        clicks=1000,
        ad_requests=60000,
        matched_requests=54000
    )
    metric.calculate_derived_metrics()

    # Profit = 150.0 - 50.0 = $100.0
    assert metric.profit == 100.0
    # ROI = (100.0 / 50.0) * 100 = 200.0%
    assert metric.roi == 200.0
    # CTR = 1000 / 50000 * 100 = 2.0%
    assert metric.ctr == 2.0
    # Fill Rate = 54000 / 60000 * 100 = 90.0%
    assert metric.fill_rate == 90.0
    # RPM = (150.0 / 50000) * 1000 = $3.0
    assert metric.rpm == 3.0

def test_zero_spend_roi_protection():
    """Menguji proteksi ROI saat spend = 0."""
    metric = DailyAdMetric(
        date=datetime.now().date(),
        source="GAM",
        spend=0.0,
        revenue=100.0,
        impressions=10000,
        clicks=200,
        ad_requests=12000,
        matched_requests=11000
    )
    metric.calculate_derived_metrics()

    assert metric.profit == 100.0
    assert metric.roi == 0.0

def test_period_filters_today_and_yesterday(client):
    """Menguji filter rentang waktu today, yesterday, dan custom."""
    login_client(client)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Inisialisasi data
    m1 = DailyAdMetric(date=today, source="GAM", spend=40.0, revenue=100.0, impressions=10000, clicks=200, ad_requests=12000, matched_requests=11000)
    m2 = DailyAdMetric(date=yesterday, source="GAM", spend=30.0, revenue=70.0, impressions=8000, clicks=150, ad_requests=9000, matched_requests=8500)
    m1.calculate_derived_metrics()
    m2.calculate_derived_metrics()

    db.session.add_all([m1, m2])
    db.session.commit()

    # Test filter Today
    res_today = client.get('/api/summary?period=today')
    assert res_today.status_code == 200
    data_today = res_today.get_json()["summary"]
    assert data_today["total_spend"] == 40.0
    assert data_today["total_earning"] == 100.0
    assert data_today["total_profit"] == 60.0

    # Test filter Yesterday
    res_yest = client.get('/api/summary?period=yesterday')
    assert res_yest.status_code == 200
    data_yest = res_yest.get_json()["summary"]
    assert data_yest["total_spend"] == 30.0
    assert data_yest["total_earning"] == 70.0
    assert data_yest["total_profit"] == 40.0

    # Test filter Custom Date Range
    res_custom = client.get(f'/api/summary?period=custom&start_date={yesterday.strftime("%Y-%m-%d")}&end_date={today.strftime("%Y-%m-%d")}')
    assert res_custom.status_code == 200
    data_custom = res_custom.get_json()["summary"]
    assert data_custom["total_spend"] == 70.0
    assert data_custom["total_earning"] == 170.0
    assert data_custom["total_profit"] == 100.0
