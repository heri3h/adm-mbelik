# Ad Performance & Profit Monitor Dashboard (GAM & Google Ads)

Aplikasi web dashboard full-stack berbasis Python (Flask), SQLite, dan Tailwind CSS + Chart.js untuk memonitor performa dan pendapatan iklan secara terpusat dari **Google Ad Manager (GAM)** dan **Google Ads**.

---

## 🌟 Fitur Utama

1. **Sinkronisasi Metrik Inti Google Ad Manager (GAM)**:
   - `AD_EXCHANGE_LINE_ITEM_LEVEL_REVENUE` (Pendapatan)
   - `AD_EXCHANGE_LINE_ITEM_LEVEL_IMPRESSIONS` (Impression)
   - `AD_EXCHANGE_LINE_ITEM_LEVEL_CLICKS` (Klik)
   - `AD_EXCHANGE_LINE_ITEM_LEVEL_TOTAL_REQUESTS` (Ad Requests)
   - `AD_EXCHANGE_LINE_ITEM_LEVEL_RESPONSES_SERVED` (Matched Requests)

2. **Kalkulasi Metrik Turunan Otomatis**:
   - **CTR (%)**: `(Clicks / Impressions) * 100`
   - **Fill Rate (%)**: `(Matched Requests / Ad Requests) * 100`
   - **RPM ($)**: `(Revenue / Impressions) * 1000`

3. **Penyimpanan Historis Lokal (Database SQLite)**:
   - Data harian tersimpan otomatis di `ad_metrics.sqlite` agar dashboard dapat dimuat sangat cepat tanpa terus-menerus memanggil API Google.

4. **UI Dashboard Modern & Interactive**:
   - **Summary Cards**: Ringkasan Total Pendapatan, Impression, Rata-rata Fill Rate, CTR, dan RPM.
   - **Time Series Charts (Chart.js)**: Grafik tren harian interaktif untuk Pendapatan, Impression, Fill Rate, dan CTR.
   - **Data Table**: Tabel rinci per hari dengan fitur pencarian cepat & filter sumber (GAM / Google Ads).
   - **Mock Data Engine**: Otomatis aktif saat kredensial Google API belum diatur agar tampilan dashboard langsung dapat dicoba secara instan.

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Prasyarat System
- Python 3.9+
- pip & venv

### 2. Setup Environment & Virtualenv
```bash
# Clone atau masuk ke direktori proyek
cd /Users/heritriharyanto/ANTGRVTY/adm

# Buat virtual environment
python3 -m venv venv

# Aktifkan virtual environment
# Di macOS / Linux:
source venv/bin/activate
# Di Windows:
# venv\Scripts\activate

# Install dependensi
pip install -r requirements.txt
```

### 3. Konfigurasi File Environment (.env)
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```

Isi konfigurasi pada file `.env`:
```ini
# Secret Key Flask
SECRET_KEY=secret-key-dashboard-anda

# Database Configuration (Default SQLite)
DATABASE_URL=sqlite:///ad_metrics.sqlite

# Google OAuth 2.0 Credentials (Dapatkan dari Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback
GOOGLE_REFRESH_TOKEN=your-refresh-token

# Google Ad Manager Network Code
GAM_NETWORK_CODE=123456789
GAM_APPLICATION_NAME=AdManagerDashboard

# Google Ads Developer Token & Customer ID
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CUSTOMER_ID=123-456-7890

# Set ke True untuk menjalankan dalam mode Simulasi/Mock Data
USE_MOCK_DATA=True
```

---

## 🔑 Panduan Konfigurasi API Google (OAuth 2.0 & GAM)

### Langkah 1: Buat Project di Google Cloud Console
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat project baru, lalu aktifkan API berikut:
   - **Google Ad Manager API**
   - **Google Ads API**
3. Buka **APIs & Services > Credentials**.
4. Buat **OAuth 2.0 Client ID** tipe *Web application*.
5. Tambahkan `http://localhost:5000/auth/callback` pada **Authorized redirect URIs**.
6. Salin **Client ID** dan **Client Secret** ke file `.env`.

### Langkah 2: Menghubungkan Google Ad Manager (GAM)
1. Buka dashboard Google Ad Manager Anda (`https://admanager.google.com`).
2. Masuk ke **Admin > Global settings**.
3. Catat **Network code** Anda, lalu masukkan ke `GAM_NETWORK_CODE` di `.env`.
4. Pastikan akses API diaktifkan di menu **API access**.

### Langkah 3: Menjalankan OAuth Login
1. Jalankan aplikasi web (buka `http://localhost:5000`).
2. Klik tombol **OAuth** di kanan atas header untuk memberikan izin akses ke akun Google Ad Manager & Google Ads Anda.

---

## 🧪 Pengujian Otomatis (Automated Tests)

Suite unit test menggunakan `pytest` telah disediakan untuk menguji logika kalkulasi metrik, fallback mock engine, dan endpoint API.

Jalankan perintah berikut:
```bash
./venv/bin/pytest tests/test_metrics.py
```

Atau jika virtualenv aktif:
```bash
pytest tests/test_metrics.py
```

---

## 💻 Menjalankan Server Aplikasi Web

Untuk menjalankan aplikasi Flask:
```bash
./venv/bin/python app.py
```

Buka browser di:
```text
http://localhost:5000
```

---

## 📂 Struktur Project

```text
adm/
├── app.py                      # Main Flask Application & REST API
├── config.py                   # Konfigurasi Environment & Credentials
├── models.py                   # Model SQLite & Kalkulasi Metrik (CTR, Fill Rate, RPM)
├── requirements.txt            # Python Dependencies
├── .env.example                # Template File Environment
├── README.md                   # Dokumentasi Lengkap
├── services/
│   ├── __init__.py
│   ├── oauth_service.py        # Module Google OAuth 2.0 Flow
│   ├── gam_service.py          # Google Ad Manager API Client & Mock Generator
│   └── google_ads_service.py   # Google Ads API Client & Mock Generator
├── static/
│   └── js/
│       └── dashboard.js        # Script Dashboard JS, Chart.js & AJAX requests
├── templates/
│   └── index.html              # HTML5 + Tailwind CSS Responsive Layout
└── tests/
    └── test_metrics.py         # Pytest Automated Test Suite
```
