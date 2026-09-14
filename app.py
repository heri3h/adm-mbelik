from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from datetime import datetime, timedelta
from config import Config
from models import db, DailyAdMetric
from services.gam_service import GAMService
from services.google_ads_service import GoogleAdsService
from services.oauth_service import get_authorization_url, get_credentials_from_code

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def seed_database_if_empty():
    """Mengisi database awal dengan data mock jika database masih kosong."""
    with app.app_context():
        db.create_all()
        if DailyAdMetric.query.count() == 0:
            print("[DB Seed] Memulai sinkronisasi data awal ke SQLite...")
            sync_data_internal(days=30)

def sync_data_internal(days=30):
    """Fungsi internal untuk menarik data dari GAM & Google Ads ke database SQLite."""
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=days)

    gam_service = GAMService()
    gads_service = GoogleAdsService()

    gam_records = gam_service.fetch_daily_report(start_date, end_date)
    gads_records = gads_service.fetch_daily_report(start_date, end_date)

    all_records = gam_records + gads_records

    for rec in all_records:
        existing = DailyAdMetric.query.filter_by(date=rec['date'], source=rec['source']).first()
        if not existing:
            existing = DailyAdMetric(
                date=rec['date'],
                source=rec['source']
            )
            db.session.add(existing)

        existing.revenue = rec['revenue']
        existing.impressions = rec['impressions']
        existing.clicks = rec['clicks']
        existing.ad_requests = rec['ad_requests']
        existing.matched_requests = rec['matched_requests']
        existing.calculate_derived_metrics()

    db.session.commit()
    print(f"[DB Sync] Berhasil memperbarui {len(all_records)} catatan metrik iklan.")

@app.before_request
def require_login_check():
    """Memastikan user harus login terlebih dahulu jika REQUIRE_LOGIN aktif."""
    if not Config.REQUIRE_LOGIN:
        return None
    
    # Endpoint bebas akses tanpa login
    allowed_routes = ['login', 'static', 'auth_callback']
    if request.endpoint in allowed_routes or session.get('logged_in'):
        return None
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        user = request.form.get('username', '').strip()
        pwd = request.form.get('password', '').strip()
        
        if user == Config.DASHBOARD_USERNAME and pwd == Config.DASHBOARD_PASSWORD:
            session['logged_in'] = True
            session['username'] = user
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Username atau Password salah!")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    is_mock = Config.USE_MOCK_DATA or not bool(Config.GAM_NETWORK_CODE and Config.GOOGLE_CLIENT_ID)
    return jsonify({
        "status": "online",
        "mode": "Mock / Simulation Mode" if is_mock else "Live Google API Mode",
        "database": Config.SQLALCHEMY_DATABASE_URI,
        "gam_network_code": Config.GAM_NETWORK_CODE or "Belum Diatur"
    })

@app.route('/api/sync', methods=['POST'])
def api_sync():
    try:
        data = request.get_json(silent=True) or {}
        days = int(data.get('days', 30))
        sync_data_internal(days=days)
        return jsonify({"success": True, "message": f"Berhasil menyinkronkan data {days} hari terakhir."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/summary')
def api_summary():
    days = int(request.args.get('days', 30))
    source = request.args.get('source', 'All')

    start_date = datetime.now().date() - timedelta(days=days)
    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date)

    if source != 'All':
        query = query.filter_by(source=source)

    metrics = query.all()

    total_revenue = sum(m.revenue for m in metrics)
    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_ad_requests = sum(m.ad_requests for m in metrics)
    total_matched_requests = sum(m.matched_requests for m in metrics)

    avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0
    avg_fill_rate = round((total_matched_requests / total_ad_requests * 100), 2) if total_ad_requests > 0 else 0.0
    avg_rpm = round((total_revenue / total_impressions * 1000), 2) if total_impressions > 0 else 0.0

    return jsonify({
        "period_days": days,
        "source_filter": source,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "total_impressions": total_impressions,
            "total_clicks": total_clicks,
            "total_ad_requests": total_ad_requests,
            "total_matched_requests": total_matched_requests,
            "avg_ctr": avg_ctr,
            "avg_fill_rate": avg_fill_rate,
            "avg_rpm": avg_rpm
        }
    })

@app.route('/api/timeseries')
def api_timeseries():
    days = int(request.args.get('days', 30))
    source = request.args.get('source', 'All')

    start_date = datetime.now().date() - timedelta(days=days)
    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date)

    if source != 'All':
        query = query.filter_by(source=source)

    metrics = query.order_by(DailyAdMetric.date.asc()).all()

    # Agregasikan berdasarkan tanggal jika source == All
    daily_map = {}
    for m in metrics:
        d_str = m.date.strftime('%Y-%m-%d')
        if d_str not in daily_map:
            daily_map[d_str] = {
                "revenue": 0.0,
                "impressions": 0,
                "clicks": 0,
                "ad_requests": 0,
                "matched_requests": 0
            }
        daily_map[d_str]["revenue"] += m.revenue
        daily_map[d_str]["impressions"] += m.impressions
        daily_map[d_str]["clicks"] += m.clicks
        daily_map[d_str]["ad_requests"] += m.ad_requests
        daily_map[d_str]["matched_requests"] += m.matched_requests

    dates = sorted(daily_map.keys())
    revenues = []
    impressions = []
    ctrs = []
    fill_rates = []
    rpms = []

    for d in dates:
        item = daily_map[d]
        rev = item["revenue"]
        imp = item["impressions"]
        clk = item["clicks"]
        req = item["ad_requests"]
        mat = item["matched_requests"]

        ctr = round((clk / imp * 100), 2) if imp > 0 else 0.0
        fill = round((mat / req * 100), 2) if req > 0 else 0.0
        rpm = round((rev / imp * 1000), 2) if imp > 0 else 0.0

        revenues.append(round(rev, 2))
        impressions.append(imp)
        ctrs.append(ctr)
        fill_rates.append(fill)
        rpms.append(rpm)

    return jsonify({
        "dates": dates,
        "revenues": revenues,
        "impressions": impressions,
        "ctrs": ctrs,
        "fill_rates": fill_rates,
        "rpms": rpms
    })

@app.route('/api/daily-details')
def api_daily_details():
    days = int(request.args.get('days', 30))
    source = request.args.get('source', 'All')

    start_date = datetime.now().date() - timedelta(days=days)
    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date)

    if source != 'All':
        query = query.filter_by(source=source)

    metrics = query.order_by(DailyAdMetric.date.desc(), DailyAdMetric.source.asc()).all()
    return jsonify([m.to_dict() for m in metrics])

@app.route('/auth/login')
def auth_login():
    try:
        url, state = get_authorization_url()
        if not url:
            return f"""
            <div style="font-family:sans-serif;max-w:600px;margin:50px auto;padding:24px;background:#1e293b;color:#f87171;border:1px solid #334155;border-radius:12px;">
                <h3 style="margin-top:0;">⚠️ Gagal Membuat OAuth Authorization URL</h3>
                <p style="color:#e2e8f0;">{state}</p>
                <p><a href="/" style="color:#60a5fa;text-decoration:none;">&larr; Kembali ke Dashboard</a></p>
            </div>
            """, 400
        session['oauth_state'] = state
        return redirect(url)
    except Exception as e:
        return f"""
        <div style="font-family:sans-serif;max-w:600px;margin:50px auto;padding:24px;background:#1e293b;color:#f87171;border:1px solid #334155;border-radius:12px;">
            <h3 style="margin-top:0;">⚠️ Error Server OAuth</h3>
            <p style="color:#e2e8f0;">{str(e)}</p>
            <p><a href="/" style="color:#60a5fa;text-decoration:none;">&larr; Kembali ke Dashboard</a></p>
        </div>
        """, 500

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get('code')
    if not code:
        return f"""
        <div style="font-family:sans-serif;max-w:600px;margin:50px auto;padding:24px;background:#1e293b;color:#f87171;border:1px solid #334155;border-radius:12px;">
            <h3 style="margin-top:0;">⚠️ Authorization Code Tidak Ditemukan</h3>
            <p><a href="/" style="color:#60a5fa;text-decoration:none;">&larr; Kembali ke Dashboard</a></p>
        </div>
        """, 400
    credentials = get_credentials_from_code(code)
    if not credentials:
        return f"""
        <div style="font-family:sans-serif;max-w:600px;margin:50px auto;padding:24px;background:#1e293b;color:#f87171;border:1px solid #334155;border-radius:12px;">
            <h3 style="margin-top:0;">⚠️ Gagal Menukar OAuth Code dengan Token</h3>
            <p style="color:#e2e8f0;">Pastikan Client ID & Client Secret di file .env sudah sesuai.</p>
            <p><a href="/" style="color:#60a5fa;text-decoration:none;">&larr; Kembali ke Dashboard</a></p>
        </div>
        """, 400
    return jsonify({
        "success": True,
        "message": "Autentikasi OAuth 2.0 Berhasil!",
        "refresh_token": credentials.refresh_token or "Token berhasil disimpan"
    })

@app.errorhandler(500)
def internal_server_error(e):
    return f"""
    <div style="font-family:sans-serif;max-w:600px;margin:50px auto;padding:24px;background:#1e293b;color:#f87171;border:1px solid #334155;border-radius:12px;">
        <h3 style="margin-top:0;">⚠️ 500 Internal Server Error</h3>
        <p style="color:#e2e8f0;">{str(e)}</p>
        <p><a href="/" style="color:#60a5fa;text-decoration:none;">&larr; Kembali ke Dashboard</a></p>
    </div>
    """, 500

if __name__ == '__main__':
    seed_database_if_empty()
    app.run(host='0.0.0.0', port=5000, debug=True)
