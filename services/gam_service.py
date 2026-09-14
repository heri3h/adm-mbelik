import os
import random
from datetime import datetime, timedelta
from config import Config
from services.oauth_service import get_oauth_credentials

class GAMService:
    def __init__(self):
        self.network_code = Config.GAM_NETWORK_CODE
        self.app_name = Config.GAM_APPLICATION_NAME
        self.use_mock = Config.USE_MOCK_DATA or not bool(self.network_code and Config.GOOGLE_CLIENT_ID)

    def fetch_daily_report(self, start_date=None, end_date=None):
        """Menarik data metrik harian Google Ad Manager (GAM)."""
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date()

        if self.use_mock:
            return self._generate_mock_data(start_date, end_date)
        else:
            try:
                return self._fetch_real_gam_report(start_date, end_date)
            except Exception as e:
                print(f"[GAMService] Error koneksi API GAM: {e}. Mengalihkan ke Mock Data...")
                return self._generate_mock_data(start_date, end_date)

    def _fetch_real_gam_report(self, start_date, end_date):
        """Boilerplate integrasi API asli ke Google Ad Manager."""
        credentials = get_oauth_credentials()
        if not credentials:
            raise ValueError("Kredensial OAuth Google tidak valid atau belum lengkap.")

        raise NotImplementedError("Silakan sesuaikan konfigurasi Network Code dan SDK Google Ad Manager.")

    def _generate_mock_data(self, start_date, end_date):
        """Generasi data simulasi GAM realistis."""
        results = []
        current_date = start_date
        random.seed(42)

        while current_date <= end_date:
            is_weekend = current_date.weekday() in (5, 6)
            multiplier = 1.25 if not is_weekend else 0.85
            
            base_requests = int(random.randint(45000, 75000) * multiplier)
            matched_requests = int(base_requests * random.uniform(0.82, 0.94))
            impressions = int(matched_requests * random.uniform(0.88, 0.96))
            clicks = int(impressions * random.uniform(0.012, 0.028))
            revenue = round((impressions / 1000.0) * random.uniform(1.85, 3.40), 2)
            spend = round(revenue * random.uniform(0.35, 0.65), 2) # Est. Spend 35%-65% dari Revenue

            results.append({
                "date": current_date,
                "source": "GAM",
                "spend": spend,
                "revenue": revenue,
                "impressions": impressions,
                "clicks": clicks,
                "ad_requests": base_requests,
                "matched_requests": matched_requests
            })
            current_date += timedelta(days=1)

        return results
