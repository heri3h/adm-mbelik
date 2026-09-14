from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class DomainMapping(db.Model):
    __tablename__ = 'domain_mappings'

    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(100), nullable=False, unique=True, index=True) # e.g. mbelik.com
    google_ads_customer_id = db.Column(db.String(50), nullable=True)                 # e.g. 123-456-7890
    campaign_name = db.Column(db.String(100), nullable=True)                         # Nama Kampanye
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "domain_name": self.domain_name,
            "google_ads_customer_id": self.google_ads_customer_id or "-",
            "campaign_name": self.campaign_name or "-",
            "description": self.description or ""
        }

class ManualGoogleAdsSpend(db.Model):
    __tablename__ = 'manual_google_ads_spends'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    domain = db.Column(db.String(100), nullable=False, default='mbelik.com', index=True)
    google_ads_customer_id = db.Column(db.String(50), nullable=False, default='123-456-7890')
    spend = db.Column(db.Float, nullable=False, default=0.0) # Biaya Iklan (Rp)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    impressions = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.strftime('%Y-%m-%d'),
            "domain": self.domain,
            "google_ads_customer_id": self.google_ads_customer_id,
            "spend": round(self.spend, 0),
            "clicks": self.clicks,
            "impressions": self.impressions
        }

class DailyAdMetric(db.Model):
    __tablename__ = 'daily_ad_metrics'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    domain = db.Column(db.String(100), nullable=False, default='mbelik.com', index=True) # Domain / Site Name
    source = db.Column(db.String(50), nullable=False, default='GAM')                      # GAM / Google Ads / Aggregated
    google_ads_customer_id = db.Column(db.String(50), nullable=True)                      # Customer ID Google Ads
    
    # Financial Metrics
    spend = db.Column(db.Float, nullable=False, default=0.0)               # Biaya Iklan / Ad Spend (Rp)
    revenue = db.Column(db.Float, nullable=False, default=0.0)             # Pendapatan / Earning (Rp)
    profit = db.Column(db.Float, nullable=False, default=0.0)              # Net Profit = Earning - Spend (Rp)
    roi = db.Column(db.Float, nullable=False, default=0.0)                 # ROI (%) = ((Earning - Spend) / Spend) * 100

    # Ad Performance Metrics
    impressions = db.Column(db.Integer, nullable=False, default=0)         # Impression
    clicks = db.Column(db.Integer, nullable=False, default=0)              # Klik
    ad_requests = db.Column(db.Integer, nullable=False, default=0)          # Ad Requests
    matched_requests = db.Column(db.Integer, nullable=False, default=0)     # Matched Requests (Responses Served)

    # Derived Metrics
    ctr = db.Column(db.Float, nullable=False, default=0.0)                 # CTR (%) = Clicks / Impressions * 100
    fill_rate = db.Column(db.Float, nullable=False, default=0.0)           # Fill Rate (%) = Matched / Ad Requests * 100
    rpm = db.Column(db.Float, nullable=False, default=0.0)                 # RPM (Rp) = (Revenue / Impressions) * 1000

    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    def calculate_derived_metrics(self):
        """Hitung metrik turunan: Profit, ROI, CTR, Fill Rate, dan RPM secara otomatis."""
        self.profit = round(self.revenue - self.spend, 0)
        self.roi = round((self.profit / self.spend * 100), 2) if self.spend > 0 else 0.0
        self.ctr = round((self.clicks / self.impressions * 100), 2) if self.impressions > 0 else 0.0
        self.fill_rate = round((self.matched_requests / self.ad_requests * 100), 2) if self.ad_requests > 0 else 0.0
        self.rpm = round((self.revenue / self.impressions * 1000), 0) if self.impressions > 0 else 0.0

    def to_dict(self):
        """Konversi objek model ke dictionary untuk output JSON API."""
        return {
            "id": self.id,
            "date": self.date.strftime('%Y-%m-%d'),
            "domain": self.domain,
            "source": self.source,
            "google_ads_customer_id": self.google_ads_customer_id or "-",
            "spend": round(self.spend, 0),
            "earning": round(self.revenue, 0),
            "revenue": round(self.revenue, 0),
            "profit": round(self.profit, 0),
            "roi": round(self.roi, 2),
            "impressions": self.impressions,
            "clicks": self.clicks,
            "ad_requests": self.ad_requests,
            "matched_requests": self.matched_requests,
            "ctr": round(self.ctr, 2),
            "fill_rate": round(self.fill_rate, 2),
            "rpm": round(self.rpm, 0)
        }
