import os
import random
from datetime import datetime, timedelta
from config import Config

class GoogleAdsService:
    def __init__(self):
        self.customer_id = Config.GOOGLE_ADS_CUSTOMER_ID
        self.developer_token = Config.GOOGLE_ADS_DEVELOPER_TOKEN
        self.use_mock = Config.USE_MOCK_DATA or not bool(self.customer_id and self.developer_token)

    def fetch_daily_report(self, start_date=None, end_date=None):
        """Menarik data performa kampanye harian dari Google Ads API."""
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date()

        if self.use_mock:
            return self._generate_mock_data(start_date, end_date)
        else:
            try:
                return self._fetch_real_google_ads_report(start_date, end_date)
            except Exception as e:
                print(f"[GoogleAdsService] Error API Google Ads: {e}. Menggunakan Mock Data...")
                return self._generate_mock_data(start_date, end_date)

    def _fetch_real_google_ads_report(self, start_date, end_date):
        """Boilerplate integrasi API asli ke Google Ads."""
        raise NotImplementedError("Silakan sesuaikan kredensial Google Ads API di file .env")

    def _generate_mock_data(self, start_date, end_date):
        """Generasi data simulasi Google Ads."""
        results = []
        current_date = start_date
        random.seed(99)

        while current_date <= end_date:
            base_requests = int(random.randint(15000, 30000))
            matched_requests = int(base_requests * random.uniform(0.85, 0.95))
            impressions = int(matched_requests * random.uniform(0.90, 0.98))
            clicks = int(impressions * random.uniform(0.015, 0.035))
            revenue = round((impressions / 1000.0) * random.uniform(1.20, 2.50), 2)
            spend = round(revenue * random.uniform(0.40, 0.70), 2)

            results.append({
                "date": current_date,
                "source": "Google Ads",
                "spend": spend,
                "revenue": revenue,
                "impressions": impressions,
                "clicks": clicks,
                "ad_requests": base_requests,
                "matched_requests": matched_requests
            })
            current_date += timedelta(days=1)

        return results
