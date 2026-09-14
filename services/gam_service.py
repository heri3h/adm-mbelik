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
        """
        Menarik data metrik harian Google Ad Manager (GAM).
        
        Metrik Inti yang ditarik dari GAM Report:
        - AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE
        - AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS
        - AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS
        - AD_EXCHANGE_LINE_ITEM_LEVEL_TOTAL_REQUESTS
        - AD_EXCHANGE_LINE_ITEM_LEVEL_RESPONSES_SERVED
        """
        if not start_date:
            start_date = datetime.now().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now().date() - timedelta(days=1)

        if self.use_mock:
            print("[GAMService] Memakai Mock Data Engine (Simulation Mode)...")
            return self._generate_mock_data(start_date, end_date)
        else:
            try:
                return self._fetch_real_gam_report(start_date, end_date)
            except Exception as e:
                print(f"[GAMService] Error koneksi API GAM: {e}. Mengalihkan ke Mock Data...")
                return self._generate_mock_data(start_date, end_date)

    def _fetch_real_gam_report(self, start_date, end_date):
        """
        Boilerplate integrasi API asli ke Google Ad Manager menggunakan AdManagerClient.
        """
        credentials = get_oauth_credentials()
        if not credentials:
            raise ValueError("Kredensial OAuth Google tidak valid atau belum lengkap.")

        # Catatan: Dalam integrasi produksi dengan googleads SDK:
        # client = AdManagerClient(credentials, self.app_name, self.network_code)
        # report_service = client.GetService('ReportService', version='v202402')
        # report_job = {
        #     'reportQuery': {
        #         'dimensions': ['DATE'],
        #         'columns': [
        #             'AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE',
        #             'AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS',
        #             'AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS',
        #             'AD_EXCHANGE_LINE_ITEM_LEVEL_TOTAL_REQUESTS',
        #             'AD_EXCHANGE_LINE_ITEM_LEVEL_RESPONSES_SERVED'
        #         ],
        #         'dateRangeType': 'CUSTOM_DATE',
        #         'startDate': {'year': start_date.year, 'month': start_date.month, 'day': start_date.day},
        #         'endDate': {'year': end_date.year, 'month': end_date.month, 'day': end_date.day}
        #     }
        # }
        # report_job_id = report_service.runReportJob(report_job)['id']
        # Download & parsing hasil report CSV...

        raise NotImplementedError("Silakan sesuaikan konfigurasi Network Code dan SDK Google Ad Manager.")

    def _generate_mock_data(self, start_date, end_date):
        """
        Generasi data simulasi harian realistis untuk testing dan visualisasi dashboard.
        """
        results = []
        current_date = start_date
        
        # Seed acak stabil
        random.seed(42)

        while current_date <= end_date:
            # Pola tren dengan fluktuasi akhir pekan
            is_weekend = current_date.weekday() in (5, 6)
            multiplier = 1.25 if not is_weekend else 0.85
            
            base_requests = int(random.randint(45000, 75000) * multiplier)
            matched_requests = int(base_requests * random.uniform(0.82, 0.94))  # Fill rate ~82%-94%
            impressions = int(matched_requests * random.uniform(0.88, 0.96))      # Viewability
            clicks = int(impressions * random.uniform(0.012, 0.028))              # CTR ~1.2%-2.8%
            revenue = round((impressions / 1000.0) * random.uniform(1.85, 3.40), 2) # eCPM $1.85 - $3.40

            results.append({
                "date": current_date,
                "source": "GAM",
                "revenue": revenue,
                "impressions": impressions,
                "clicks": clicks,
                "ad_requests": base_requests,
                "matched_requests": matched_requests
            })
            current_date += timedelta(days=1)

        return results
