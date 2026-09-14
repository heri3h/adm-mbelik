from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class DailyAdMetric(db.Model):
    __tablename__ = 'daily_ad_metrics'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    source = db.Column(db.String(50), nullable=False, default='GAM') # GAM / Google Ads / Aggregated
    
    # Core Metrics
    revenue = db.Column(db.Float, nullable=False, default=0.0)             # Pendapatan (USD/IDR)
    impressions = db.Column(db.Integer, nullable=False, default=0)         # Impression
    clicks = db.Column(db.Integer, nullable=False, default=0)              # Klik
    ad_requests = db.Column(db.Integer, nullable=False, default=0)          # Ad Requests
    matched_requests = db.Column(db.Integer, nullable=False, default=0)     # Matched Requests (Responses Served)

    # Derived Metrics (Calculated & Saved)
    ctr = db.Column(db.Float, nullable=False, default=0.0)                 # CTR (%) = Clicks / Impressions * 100
    fill_rate = db.Column(db.Float, nullable=False, default=0.0)           # Fill Rate (%) = Matched / Ad Requests * 100
    rpm = db.Column(db.Float, nullable=False, default=0.0)                 # RPM ($) = (Revenue / Impressions) * 1000

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def calculate_derived_metrics(self):
        """Hitung metrik turunan: CTR, Fill Rate, dan RPM secara otomatis."""
        self.ctr = round((self.clicks / self.impressions * 100), 2) if self.impressions > 0 else 0.0
        self.fill_rate = round((self.matched_requests / self.ad_requests * 100), 2) if self.ad_requests > 0 else 0.0
        self.rpm = round((self.revenue / self.impressions * 1000), 2) if self.impressions > 0 else 0.0

    def to_dict(self):
        """Konversi objek model ke dictionary untuk output JSON API."""
        return {
            "id": self.id,
            "date": self.date.strftime('%Y-%m-%d'),
            "source": self.source,
            "revenue": round(self.revenue, 2),
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ad_requests": self.ad_requests,
            "matched_requests": self.matched_requests,
            "ctr": round(self.ctr, 2),
            "fill_rate": round(self.fill_rate, 2),
            "rpm": round(self.rpm, 2)
        }
