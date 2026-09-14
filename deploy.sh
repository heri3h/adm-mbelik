#!/bin/bash
# Script Otomatisasi Deployment ke Server VPS HestiaCP Ubuntu

echo "=== Memulai Otomatisasi Deployment Ad Dashboard (adm.mbelik.com) ==="

# 1. Pastikan Python 3 & venv terinstall
if ! command -v python3 &> /dev/null
then
    echo "Python3 tidak ditemukan. Menginstall python3..."
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip
fi

# 2. Buat virtual environment jika belum ada
if [ ! -d "venv" ]; then
    echo "Membuat Python Virtual Environment (venv)..."
    python3 -m venv venv 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Menginstall dependensi python3-venv dari apt..."
        sudo apt update && sudo apt install -y python3-venv python3-pip
        python3 -m venv venv
    fi
fi

# 3. Upgrade pip & install dependensi
echo "Menginstall dependensi Python..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 4. Buat file .env dari .env.example jika belum ada
if [ ! -f ".env" ]; then
    echo "Membuat file .env dari .env.example..."
    cp .env.example .env
    echo "PERHATIAN: Silakan edit file .env untuk mengatur SECRET_KEY & Google API credentials."
fi

# 5. Jalankan unit test untuk memastikan aplikasi berjalan tanpa error
echo "Menjalankan unit test..."
./venv/bin/pytest tests/test_metrics.py

if [ $? -eq 0 ]; then
    echo "=== Deployment Selesai Disiapkan! ==="
    echo "Langkah selanjutnya:"
    echo "1. Edit .env sesuai kredensial Google API Anda."
    echo "2. Salin adm.service: sudo cp adm.service /etc/systemd/system/adm.service"
    echo "3. Jalankan: sudo systemctl daemon-reload && sudo systemctl enable --now adm"
else
    echo "Pengujian gagal! Periksa error di atas sebelum menjalankan di production."
    exit 1
fi
