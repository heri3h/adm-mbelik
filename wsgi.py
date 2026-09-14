from app import app, seed_database_if_empty

# Inisialisasi database jika belum ada saat startup production
seed_database_if_empty()

if __name__ == "__main__":
    app.run()
