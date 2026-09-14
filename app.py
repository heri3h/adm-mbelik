from flask import Flask, render_template, jsonify, request, redirect, session, url_for
from datetime import datetime, timedelta
from config import Config
from models import db, DailyAdMetric, DomainMapping, ManualGoogleAdsSpend
from services.gam_service import GAMService
from services.google_ads_service import GoogleAdsService
from services.oauth_service import get_authorization_url, get_credentials_from_code

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def seed_database_if_empty():
    """Mengisi database awal dengan data mock dan migrasi tabel SQLite secara otomatis."""
    with app.app_context():
        db.create_all()

        # Migrasi kolom otomatis untuk SQLite jika kolom baru belum ada (Jalan DULUAN sebelum query model)
        try:
            inspector = db.inspect(db.engine)

            # 1. Migrasi tabel daily_ad_metrics
            if inspector.has_table('daily_ad_metrics'):
                columns_daily = [c['name'] for c in inspector.get_columns('daily_ad_metrics')]
                with db.engine.connect() as conn:
                    if 'spend' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN spend FLOAT DEFAULT 0.0"))
                    if 'profit' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN profit FLOAT DEFAULT 0.0"))
                    if 'roi' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN roi FLOAT DEFAULT 0.0"))
                    if 'domain' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN domain VARCHAR(100) DEFAULT 'mbelik.com'"))
                    if 'google_ads_customer_id' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN google_ads_customer_id VARCHAR(50) DEFAULT '-'"))
                    if 'mcc_id' not in columns_daily:
                        conn.execute(db.text("ALTER TABLE daily_ad_metrics ADD COLUMN mcc_id VARCHAR(50) DEFAULT '-'"))
                    conn.commit()

            # 2. Migrasi tabel domain_mappings
            if inspector.has_table('domain_mappings'):
                columns_map = [c['name'] for c in inspector.get_columns('domain_mappings')]
                with db.engine.connect() as conn:
                    if 'mcc_id' not in columns_map:
                        conn.execute(db.text("ALTER TABLE domain_mappings ADD COLUMN mcc_id VARCHAR(50) DEFAULT '-'"))
                    conn.commit()

            # 3. Migrasi tabel manual_google_ads_spends
            if inspector.has_table('manual_google_ads_spends'):
                columns_spend = [c['name'] for c in inspector.get_columns('manual_google_ads_spends')]
                with db.engine.connect() as conn:
                    if 'mcc_id' not in columns_spend:
                        conn.execute(db.text("ALTER TABLE manual_google_ads_spends ADD COLUMN mcc_id VARCHAR(50) DEFAULT '-'"))
                    conn.commit()

        except Exception as e:
            print(f"[DB Migration Warning] {e}")

        # Seed default DomainMapping jika belum ada
        if DomainMapping.query.count() == 0:
            db.session.add(DomainMapping(
                domain_name='mbelik.com',
                mcc_id='123-456-7890',
                google_ads_customer_id='987-654-3210',
                campaign_name='Kampanye Utama Mbelik',
                description='Domain Utama'
            ))
            db.session.commit()

        if DailyAdMetric.query.count() == 0:
            print("[DB Seed] Memulai sinkronisasi data awal ke SQLite...")
            sync_data_internal(days=30)

def sync_data_internal(days=30):
    """Fungsi internal untuk menarik data dari GAM & Google Ads ke database SQLite per Domain."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    gam_service = GAMService()
    gads_service = GoogleAdsService()

    mappings = DomainMapping.query.all()
    if not mappings:
        mappings = [DomainMapping(domain_name='mbelik.com', google_ads_customer_id='123-456-7890')]

    all_records = []
    for m in mappings:
        gam_records = gam_service.fetch_daily_report(start_date, end_date, domain=m.domain_name)
        gads_records = gads_service.fetch_daily_report(start_date, end_date, domain=m.domain_name, customer_id=m.google_ads_customer_id)
        all_records.extend(gam_records + gads_records)

    for rec in all_records:
        existing = DailyAdMetric.query.filter_by(
            date=rec['date'], 
            source=rec['source'], 
            domain=rec['domain']
        ).first()

        if not existing:
            existing = DailyAdMetric(
                date=rec['date'],
                domain=rec['domain'],
                source=rec['source'],
                google_ads_customer_id=rec.get('google_ads_customer_id', '-')
            )
            db.session.add(existing)

        existing.google_ads_customer_id = rec.get('google_ads_customer_id', '-')
        existing.spend = rec.get('spend', 0.0)
        existing.revenue = rec.get('revenue', 0.0)
        existing.impressions = rec.get('impressions', 0)
        existing.clicks = rec.get('clicks', 0)
        existing.ad_requests = rec.get('ad_requests', 0)
        existing.matched_requests = rec.get('matched_requests', 0)
        existing.calculate_derived_metrics()

    db.session.commit()
    print(f"[DB Sync] Berhasil menyinkronkan {len(all_records)} catatan metrik iklan.")

def get_date_range_from_request(req):
    """Mendapatkan tanggal mulai dan selesai dari parameter request."""
    period = req.args.get('period', '30')
    today = datetime.now().date()
    
    if period == 'today':
        return today, today
    elif period == 'yesterday':
        yest = today - timedelta(days=1)
        return yest, yest
    elif period == 'custom':
        s_str = req.args.get('start_date')
        e_str = req.args.get('end_date')
        try:
            start_date = datetime.strptime(s_str, '%Y-%m-%d').date() if s_str else today - timedelta(days=30)
            end_date = datetime.strptime(e_str, '%Y-%m-%d').date() if e_str else today
        except Exception:
            start_date = today - timedelta(days=30)
            end_date = today
        return start_date, end_date
    else:
        try:
            days = int(period)
        except Exception:
            days = 30
        return today - timedelta(days=days - 1), today

@app.before_request
def require_login_check():
    """Memastikan user harus login terlebih dahulu jika REQUIRE_LOGIN aktif."""
    if not Config.REQUIRE_LOGIN:
        return None
    
    allowed_routes = ['login', 'static', 'auth_callback']
    if request.endpoint in allowed_routes or session.get('logged_in'):
        return None
    
    if request.path.startswith('/api/'):
        return jsonify({"error": "Sesi login telah berakhir. Silakan login kembali.", "login_required": True}), 401

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

@app.route('/api/domain-mappings', methods=['GET', 'POST'])
def api_domain_mappings():
    """Endpoint CRUD untuk mapping Domain GAM dengan MCC ID & Google Ads Customer ID."""
    if request.method == 'POST':
        try:
            data = request.get_json() or {}
            domain_name = data.get('domain_name', '').strip()
            mcc_id = data.get('mcc_id', '').strip()
            customer_id = data.get('google_ads_customer_id', '').strip()
            campaign_name = data.get('campaign_name', '').strip()
            description = data.get('description', '').strip()

            if not domain_name:
                return jsonify({"success": False, "error": "Nama domain wajib diisi."}), 400

            existing = DomainMapping.query.filter_by(domain_name=domain_name).first()
            if not existing:
                existing = DomainMapping(domain_name=domain_name)
                db.session.add(existing)

            existing.mcc_id = mcc_id
            existing.google_ads_customer_id = customer_id
            existing.campaign_name = campaign_name
            existing.description = description
            db.session.commit()

            # Trigger auto sync data untuk domain baru
            sync_data_internal(days=30)

            return jsonify({"success": True, "message": f"Berhasil menyimpan mapping domain {domain_name}."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        mappings = DomainMapping.query.all()
        return jsonify([m.to_dict() for m in mappings])

@app.route('/api/manual-spend', methods=['GET', 'POST'])
def api_manual_spend():
    """Endpoint untuk memasukkan biaya iklan Google Ads secara manual."""
    if request.method == 'POST':
        try:
            data = request.get_json() or {}
            d_str = data.get('date', datetime.now().strftime('%Y-%m-%d')).strip()
            domain = data.get('domain', 'mbelik.com').strip()
            mcc_id = data.get('mcc_id', '').strip()
            customer_id = data.get('google_ads_customer_id', '123-456-7890').strip()
            spend = float(data.get('spend', 0.0))
            clicks = int(data.get('clicks', 0))
            impressions = int(data.get('impressions', 0))

            entry_date = datetime.strptime(d_str, '%Y-%m-%d').date()

            existing = ManualGoogleAdsSpend.query.filter_by(date=entry_date, domain=domain).first()
            if not existing:
                existing = ManualGoogleAdsSpend(date=entry_date, domain=domain)
                db.session.add(existing)

            existing.mcc_id = mcc_id
            existing.google_ads_customer_id = customer_id
            existing.spend = spend
            existing.clicks = clicks
            existing.impressions = impressions
            db.session.commit()

            # Trigger sync data otomatis agar dashboard langsung terupdate
            sync_data_internal(days=30)

            return jsonify({"success": True, "message": f"Berhasil menyimpan Spend manual Rp {spend:,.0f} untuk {domain} pada tanggal {d_str}."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        entries = ManualGoogleAdsSpend.query.order_by(ManualGoogleAdsSpend.date.desc()).all()
        return jsonify([e.to_dict() for e in entries])

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
    if DailyAdMetric.query.count() == 0:
        sync_data_internal(days=30)

    start_date, end_date = get_date_range_from_request(request)
    source = request.args.get('source', 'All')
    domain = request.args.get('domain', 'All')

    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date, DailyAdMetric.date <= end_date)

    if source != 'All':
        query = query.filter_by(source=source)
    if domain != 'All':
        query = query.filter_by(domain=domain)

    metrics = query.all()
    if not metrics:
        sync_data_internal(days=30)
        metrics = query.all()

    total_spend = sum(m.spend for m in metrics)
    total_earning = sum(m.revenue for m in metrics)
    total_profit = total_earning - total_spend
    total_roi = round((total_profit / total_spend * 100), 2) if total_spend > 0 else 0.0

    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_ad_requests = sum(m.ad_requests for m in metrics)
    total_matched_requests = sum(m.matched_requests for m in metrics)

    avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0
    avg_fill_rate = round((total_matched_requests / total_ad_requests * 100), 2) if total_ad_requests > 0 else 0.0
    avg_rpm = round((total_earning / total_impressions * 1000), 0) if total_impressions > 0 else 0.0

    return jsonify({
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "source_filter": source,
        "domain_filter": domain,
        "summary": {
            "total_spend": round(total_spend, 0),
            "total_earning": round(total_earning, 0),
            "total_profit": round(total_profit, 0),
            "total_roi": total_roi,
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
    if DailyAdMetric.query.count() == 0:
        sync_data_internal(days=30)

    start_date, end_date = get_date_range_from_request(request)
    source = request.args.get('source', 'All')
    domain = request.args.get('domain', 'All')

    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date, DailyAdMetric.date <= end_date)

    if source != 'All':
        query = query.filter_by(source=source)
    if domain != 'All':
        query = query.filter_by(domain=domain)

    metrics = query.order_by(DailyAdMetric.date.asc()).all()
    if not metrics:
        sync_data_internal(days=30)
        metrics = query.order_by(DailyAdMetric.date.asc()).all()

    daily_map = {}
    for m in metrics:
        d_str = m.date.strftime('%Y-%m-%d')
        if d_str not in daily_map:
            daily_map[d_str] = {
                "spend": 0.0,
                "revenue": 0.0,
                "impressions": 0,
                "clicks": 0,
                "ad_requests": 0,
                "matched_requests": 0
            }
        daily_map[d_str]["spend"] += m.spend
        daily_map[d_str]["revenue"] += m.revenue
        daily_map[d_str]["impressions"] += m.impressions
        daily_map[d_str]["clicks"] += m.clicks
        daily_map[d_str]["ad_requests"] += m.ad_requests
        daily_map[d_str]["matched_requests"] += m.matched_requests

    dates = sorted(daily_map.keys())
    spends = []
    earnings = []
    profits = []
    rois = []
    impressions = []
    ctrs = []
    fill_rates = []
    rpms = []

    for d in dates:
        item = daily_map[d]
        sp = item["spend"]
        rev = item["revenue"]
        prof = rev - sp
        roi = round((prof / sp * 100), 2) if sp > 0 else 0.0
        imp = item["impressions"]
        clk = item["clicks"]
        req = item["ad_requests"]
        mat = item["matched_requests"]

        ctr = round((clk / imp * 100), 2) if imp > 0 else 0.0
        fill = round((mat / req * 100), 2) if req > 0 else 0.0
        rpm = round((rev / imp * 1000), 0) if imp > 0 else 0.0

        spends.append(round(sp, 0))
        earnings.append(round(rev, 0))
        profits.append(round(prof, 0))
        rois.append(roi)
        impressions.append(imp)
        ctrs.append(ctr)
        fill_rates.append(fill)
        rpms.append(rpm)

    return jsonify({
        "dates": dates,
        "spends": spends,
        "earnings": earnings,
        "profits": profits,
        "rois": rois,
        "impressions": impressions,
        "ctrs": ctrs,
        "fill_rates": fill_rates,
        "rpms": rpms
    })

@app.route('/api/daily-details')
def api_daily_details():
    if DailyAdMetric.query.count() == 0:
        sync_data_internal(days=30)

    start_date, end_date = get_date_range_from_request(request)
    source = request.args.get('source', 'All')
    domain = request.args.get('domain', 'All')

    query = DailyAdMetric.query.filter(DailyAdMetric.date >= start_date, DailyAdMetric.date <= end_date)

    if source != 'All':
        query = query.filter_by(source=source)
    if domain != 'All':
        query = query.filter_by(domain=domain)

    metrics = query.order_by(DailyAdMetric.date.desc(), DailyAdMetric.source.asc()).all()
    if not metrics:
        sync_data_internal(days=30)
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
