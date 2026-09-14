# Solusi Permission Denied & Panduan Deployment Ubuntu VPS (`ubuntu` user)

Ketika Anda masuk SSH sebagai user **`ubuntu`**, folder `/home/mbummm/web/adm.mbelik.com/public_html` dimiliki oleh user **`mbummm`**. Oleh karena itu, perlu diberikan hak kepemilikan (ownership) sebelum menjalankan script.

---

## ⚡ Solusi Langkah demi Langkah di Terminal Ubuntu SSH

Jalankan urutan perintah berikut langsung dari terminal SSH **`ubuntu@vps`**:

### 1. Perbaiki Hak Akses / Ownership Folder ke User `mbummm`
```bash
sudo chown -R mbummm:mbummm /home/mbummm/web/adm.mbelik.com/public_html
```

### 2. Masuk ke Folder Proyek sebagai User `mbummm` (atau jalankan `sudo -u mbummm`)
```bash
cd /home/mbummm/web/adm.mbelik.com/public_html
```

### 3. Jalankan Script Deployment sebagai User `mbummm`
```bash
sudo -u mbummm bash -c "cd /home/mbummm/web/adm.mbelik.com/public_html && chmod +x deploy.sh && ./deploy.sh"
```

---

## 🛡️ 4. Aktifkan Service Gunicorn (Systemd)

Setelah script `deploy.sh` berhasil (100% test passed), aktifkan service di Ubuntu:

```bash
sudo cp /home/mbummm/web/adm.mbelik.com/public_html/adm.service /etc/systemd/system/adm.service
sudo systemctl daemon-reload
sudo systemctl enable --now adm
```

Cek status service:
```bash
sudo systemctl status adm
```

---

## 🌐 5. Pengesetan Nginx Proxy & SSL di Panel HestiaCP

1. Login ke Panel HestiaCP (`https://ip-vps:8083`).
2. Buka **WEB** > Edit **`adm.mbelik.com`**.
3. **Proxy Support**: Centang dan isi `http://127.0.0.1:5000`.
4. **Enable SSL**: Centang **Enable SSL support**, **Lets Encrypt Support**, dan **Redirect HTTP to HTTPS**.
5. Klik **Save**.

Buka di browser:
**`https://adm.mbelik.com`**
