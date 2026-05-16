"""
============================================================
KONFIGURASI SISTEM PREDIKSI VOLUME SAMPAH DKI JAKARTA
Sumber Data: Dinas Lingkungan Hidup (DLH) DKI Jakarta
Rata-rata timbulan: ~8.700 ton/hari (2024)
============================================================
"""

import os

# ============================================================
# PATH CONFIGURATION
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, EXPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# LOKASI MONITORING - 20 Kecamatan DKI Jakarta
# Data kepadatan penduduk (jiwa/km²) berdasarkan BPS DKI Jakarta
# Zone: urban, komersial, industri, suburban, pemerintahan, wisata
# ============================================================
LOCATIONS = {
    # --- Jakarta Pusat ---
    "Jakarta Pusat - Menteng": {
        "lat": -6.1944, "lon": 106.8367,
        "population_density": 12500, "zone": "urban",
        "kota_adm": "Jakarta Pusat"
    },
    "Jakarta Pusat - Tanah Abang": {
        "lat": -6.1857, "lon": 106.8110,
        "population_density": 22000, "zone": "komersial",
        "kota_adm": "Jakarta Pusat"
    },
    "Jakarta Pusat - Kemayoran": {
        "lat": -6.1567, "lon": 106.8557,
        "population_density": 26500, "zone": "urban",
        "kota_adm": "Jakarta Pusat"
    },
    "Jakarta Pusat - Gambir": {
        "lat": -6.1754, "lon": 106.8272,
        "population_density": 9800, "zone": "pemerintahan",
        "kota_adm": "Jakarta Pusat"
    },
    # --- Jakarta Utara ---
    "Jakarta Utara - Tanjung Priok": {
        "lat": -6.1247, "lon": 106.8770,
        "population_density": 13500, "zone": "industri",
        "kota_adm": "Jakarta Utara"
    },
    "Jakarta Utara - Penjaringan": {
        "lat": -6.1171, "lon": 106.7960,
        "population_density": 19200, "zone": "urban",
        "kota_adm": "Jakarta Utara"
    },
    "Jakarta Utara - Kelapa Gading": {
        "lat": -6.1588, "lon": 106.9054,
        "population_density": 11800, "zone": "komersial",
        "kota_adm": "Jakarta Utara"
    },
    # --- Jakarta Barat ---
    "Jakarta Barat - Cengkareng": {
        "lat": -6.1440, "lon": 106.7284,
        "population_density": 21500, "zone": "urban",
        "kota_adm": "Jakarta Barat"
    },
    "Jakarta Barat - Grogol Petamburan": {
        "lat": -6.1684, "lon": 106.7851,
        "population_density": 19800, "zone": "komersial",
        "kota_adm": "Jakarta Barat"
    },
    "Jakarta Barat - Tambora": {
        "lat": -6.1503, "lon": 106.8043,
        "population_density": 44400, "zone": "urban",
        "kota_adm": "Jakarta Barat"
    },
    "Jakarta Barat - Kebon Jeruk": {
        "lat": -6.1901, "lon": 106.7673,
        "population_density": 17500, "zone": "urban",
        "kota_adm": "Jakarta Barat"
    },
    # --- Jakarta Selatan ---
    "Jakarta Selatan - Kebayoran Baru": {
        "lat": -6.2447, "lon": 106.7969,
        "population_density": 14800, "zone": "urban",
        "kota_adm": "Jakarta Selatan"
    },
    "Jakarta Selatan - Tebet": {
        "lat": -6.2262, "lon": 106.8492,
        "population_density": 21200, "zone": "urban",
        "kota_adm": "Jakarta Selatan"
    },
    "Jakarta Selatan - Pancoran": {
        "lat": -6.2480, "lon": 106.8418,
        "population_density": 17600, "zone": "urban",
        "kota_adm": "Jakarta Selatan"
    },
    "Jakarta Selatan - Jagakarsa": {
        "lat": -6.3325, "lon": 106.8256,
        "population_density": 11500, "zone": "suburban",
        "kota_adm": "Jakarta Selatan"
    },
    # --- Jakarta Timur ---
    "Jakarta Timur - Jatinegara": {
        "lat": -6.2194, "lon": 106.8706,
        "population_density": 21800, "zone": "komersial",
        "kota_adm": "Jakarta Timur"
    },
    "Jakarta Timur - Cakung": {
        "lat": -6.1824, "lon": 106.9372,
        "population_density": 14200, "zone": "industri",
        "kota_adm": "Jakarta Timur"
    },
    "Jakarta Timur - Duren Sawit": {
        "lat": -6.2361, "lon": 106.9100,
        "population_density": 17300, "zone": "urban",
        "kota_adm": "Jakarta Timur"
    },
    "Jakarta Timur - Matraman": {
        "lat": -6.2026, "lon": 106.8589,
        "population_density": 36200, "zone": "urban",
        "kota_adm": "Jakarta Timur"
    },
    # --- Kepulauan Seribu ---
    "Kepulauan Seribu - Pulau Pramuka": {
        "lat": -5.7440, "lon": 106.6145,
        "population_density": 450, "zone": "wisata",
        "kota_adm": "Kepulauan Seribu"
    },
}

# ============================================================
# JENIS EVENT YANG MEMPENGARUHI VOLUME SAMPAH DKI JAKARTA
# Sumber: DLH DKI Jakarta & laporan media
# city_wide=True → berlaku untuk SELURUH lokasi
# ============================================================
EVENT_TYPES = {
    "Jakarta Fair (PRJ)": {
        "multiplier": 1.6, "duration_days": 30, "category": "festival",
        "city_wide": False
    },
    "HUT DKI Jakarta": {
        "multiplier": 1.8, "duration_days": 5, "category": "perayaan",
        "city_wide": False
    },
    "Malam Tahun Baru": {
        "multiplier": 2.2, "duration_days": 2, "category": "perayaan",
        "city_wide": False
    },
    "Natal": {
        "multiplier": 1.6, "duration_days": 3, "category": "agama",
        "city_wide": False
    },
    "Hari Raya Idul Fitri": {
        "multiplier": 0.2, "duration_days": 7, "category": "agama",
        "city_wide": True,  # warga mudik, volume turun ~80%
    },
    "Persiapan Lebaran": {
        "multiplier": 1.5, "duration_days": 5, "category": "agama",
        "city_wide": True,
    },
    "Arus Balik Lebaran": {
        "multiplier": 1.3, "duration_days": 4, "category": "agama",
        "city_wide": True,
    },
    "Imlek & Cap Go Meh": {
        "multiplier": 1.7, "duration_days": 3, "category": "agama",
        "city_wide": False
    },
    "Paskah": {
        "multiplier": 1.3, "duration_days": 2, "category": "agama",
        "city_wide": False
    },
    "Jakarta Marathon": {
        "multiplier": 1.4, "duration_days": 1, "category": "olahraga",
        "city_wide": False
    },
    "Konser GBK / Stadion": {
        "multiplier": 1.8, "duration_days": 2, "category": "hiburan",
        "city_wide": False
    },
    "Festival Kuliner Jakarta": {
        "multiplier": 1.9, "duration_days": 5, "category": "festival",
        "city_wide": False
    },
    "Hari Kemerdekaan RI": {
        "multiplier": 1.5, "duration_days": 3, "category": "nasional",
        "city_wide": True
    },
    "Pemilihan Umum": {
        "multiplier": 1.3, "duration_days": 2, "category": "politik",
        "city_wide": True
    },
    "Banjir Besar": {
        "multiplier": 2.5, "duration_days": 5, "category": "bencana",
        "city_wide": False,  # area-specific
    },
}

# ============================================================
# KONDISI CUACA JAKARTA (Tropis)
# ============================================================
WEATHER_CONDITIONS = {
    "Cerah": {"impact_factor": 1.0, "icon": "☀️"},
    "Berawan": {"impact_factor": 1.05, "icon": "⛅"},
    "Hujan Ringan": {"impact_factor": 1.15, "icon": "🌦️"},
    "Hujan Sedang": {"impact_factor": 1.3, "icon": "🌧️"},
    "Hujan Lebat": {"impact_factor": 1.5, "icon": "⛈️"},
    "Banjir Lokal": {"impact_factor": 1.8, "icon": "🌊"},
}

# ============================================================
# MUSIM DI JAKARTA
# ============================================================
SEASONS = {
    "Kemarau": {"months": [4, 5, 6, 7, 8, 9, 10], "base_factor": 1.0},
    "Hujan": {"months": [11, 12, 1, 2, 3], "base_factor": 1.25},
}

# ============================================================
# PARAMETER ARMADA & FASILITAS - Skala DKI Jakarta
# Sumber: DLH DKI Jakarta
# ============================================================
FLEET_CONFIG = {
    "truck_capacity_kg": 8000,        # Kapasitas dump truck DKI (kg)
    "truck_trips_per_day": 4,         # Rata-rata trip per hari
    "workers_per_truck": 4,           # Petugas per truk (supir + 3 kru)
    "worker_hours_per_shift": 8,      # Jam kerja per shift
    "bin_capacity_liters": 660,       # Kapasitas kontainer TPS (liter)
    "bin_fill_rate_kg_per_liter": 0.35,  # Rasio kg per liter
    "cost_per_trip": 550000,          # Biaya per trip Jakarta (Rp)
    "worker_daily_wage": 220000,      # UMP DKI Jakarta 2024 harian (Rp)
    "tpst_bantargebang_capacity": 7800000,  # Kapasitas TPST Bantargebang (kg/hari)
}

# ============================================================
# KOMPOSISI SAMPAH DKI JAKARTA (%)
# Sumber: DLH DKI Jakarta / SIPSN KLHK
# ============================================================
WASTE_COMPOSITION = {
    "organic_pct_range": (0.55, 0.65),       # 55-65% sampah organik (sisa makanan)
    "plastic_pct_range": (0.18, 0.25),       # 18-25% plastik (~22.95% rata-rata)
    "recyclable_pct_range": (0.12, 0.22),    # 12-22% daur ulang (kertas, logam, kaca)
}

# ============================================================
# MODEL CONFIGURATION
# ============================================================
MODEL_CONFIG = {
    "test_size": 0.2,
    "random_state": 42,
    "n_estimators": 200,
    "max_depth": 15,
    "min_samples_split": 5,
}

# ============================================================
# UI CONFIGURATION
# ============================================================
APP_TITLE = "🗑️ DKI Jakarta Waste Prediction System"
APP_SUBTITLE = "Sistem Prediksi Volume Sampah DKI Jakarta — Dinas Lingkungan Hidup"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Dinas Lingkungan Hidup DKI Jakarta × AI Team"
