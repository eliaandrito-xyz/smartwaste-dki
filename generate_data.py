"""
============================================================
GENERATOR DATA HISTORIS SAMPAH DKI JAKARTA
Membuat dataset sintetis volume sampah 2 tahun terakhir
Dikalibrasi berdasarkan data DLH DKI Jakarta (~8.700 ton/hari)
============================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from config import LOCATIONS, EVENT_TYPES, WEATHER_CONDITIONS, SEASONS, DATA_DIR

np.random.seed(42)


# ============================================================
# FAKTOR VOLUME PER ZONA
# Dikalibrasi agar total 20 lokasi ≈ 8.700 ton/hari
# base_volume = population_density × zone_factor (kg/hari)
# ============================================================
ZONE_FACTORS = {
    "urban": 15.5,
    "komersial": 18.0,
    "industri": 13.0,
    "suburban": 11.5,
    "pemerintahan": 14.0,
    "wisata": 20.0,
}


def get_season(month):
    """Tentukan musim berdasarkan bulan."""
    for season_name, info in SEASONS.items():
        if month in info["months"]:
            return season_name, info["base_factor"]
    return "Kemarau", 1.0


def generate_weather(date, season):
    """Generate cuaca berdasarkan musim Jakarta."""
    if season == "Hujan":
        weights = [0.08, 0.12, 0.30, 0.28, 0.17, 0.05]
    else:
        weights = [0.40, 0.30, 0.15, 0.10, 0.04, 0.01]

    conditions = list(WEATHER_CONDITIONS.keys())
    return np.random.choice(conditions, p=weights)


def generate_events(start_date, end_date):
    """Generate event Jakarta yang realistis sepanjang periode."""
    events = []

    for year in range(start_date.year, end_date.year + 1):
        # === FIXED ANNUAL EVENTS ===

        # Jakarta Fair (PRJ) - Juni-Juli setiap tahun
        events.append({
            "date_start": datetime(year, 6, 12),
            "date_end": datetime(year, 7, 12),
            "type": "Jakarta Fair (PRJ)",
            "location": "Jakarta Pusat - Kemayoran",
            "estimated_visitors": np.random.randint(30000, 100000),
        })

        # HUT DKI Jakarta - 22 Juni
        events.append({
            "date_start": datetime(year, 6, 20),
            "date_end": datetime(year, 6, 24),
            "type": "HUT DKI Jakarta",
            "location": np.random.choice(list(LOCATIONS.keys())),
            "estimated_visitors": np.random.randint(10000, 50000),
        })

        # Malam Tahun Baru - 31 Des - 1 Jan
        events.append({
            "date_start": datetime(year, 12, 31),
            "date_end": datetime(year + 1, 1, 1) if year < end_date.year else datetime(year, 12, 31),
            "type": "Malam Tahun Baru",
            "location": "Jakarta Pusat - Tanah Abang",  # Sudirman-Thamrin area
            "estimated_visitors": np.random.randint(50000, 200000),
        })

        # Natal - 24-26 Des
        events.append({
            "date_start": datetime(year, 12, 24),
            "date_end": datetime(year, 12, 26),
            "type": "Natal",
            "location": np.random.choice(list(LOCATIONS.keys())),
            "estimated_visitors": np.random.randint(10000, 40000),
        })

        # Hari Kemerdekaan RI - 17 Agustus
        events.append({
            "date_start": datetime(year, 8, 16),
            "date_end": datetime(year, 8, 18),
            "type": "Hari Kemerdekaan RI",
            "location": "Jakarta Pusat - Gambir",  # Monas area
            "estimated_visitors": np.random.randint(20000, 80000),
        })

        # Idul Fitri (approximate - shifts each year)
        month_idul = 4 if year % 2 == 0 else 3
        day_idul = 10 if year % 2 == 0 else 28

        # Persiapan Lebaran (5 hari sebelum)
        prep_start = datetime(year, month_idul, day_idul) - timedelta(days=12)
        events.append({
            "date_start": prep_start,
            "date_end": prep_start + timedelta(days=5),
            "type": "Persiapan Lebaran",
            "location": "ALL",
            "estimated_visitors": 0,
        })

        # Hari Raya Idul Fitri (volume turun ~80%)
        events.append({
            "date_start": datetime(year, month_idul, day_idul),
            "date_end": datetime(year, month_idul, day_idul) + timedelta(days=7),
            "type": "Hari Raya Idul Fitri",
            "location": "ALL",
            "estimated_visitors": 0,
        })

        # Arus Balik Lebaran
        balik_start = datetime(year, month_idul, day_idul) + timedelta(days=8)
        events.append({
            "date_start": balik_start,
            "date_end": balik_start + timedelta(days=4),
            "type": "Arus Balik Lebaran",
            "location": "ALL",
            "estimated_visitors": 0,
        })

        # Imlek (Februari area)
        events.append({
            "date_start": datetime(year, 2, 10),
            "date_end": datetime(year, 2, 12),
            "type": "Imlek & Cap Go Meh",
            "location": "Jakarta Barat - Tambora",  # Glodok area
            "estimated_visitors": np.random.randint(10000, 40000),
        })

        # Paskah (April)
        events.append({
            "date_start": datetime(year, 4, 18),
            "date_end": datetime(year, 4, 20),
            "type": "Paskah",
            "location": np.random.choice(list(LOCATIONS.keys())),
            "estimated_visitors": np.random.randint(5000, 20000),
        })

    # === RANDOM EVENTS ===
    random_event_types = [
        "Konser GBK / Stadion", "Festival Kuliner Jakarta",
        "Jakarta Marathon", "Pemilihan Umum", "Banjir Besar",
    ]

    num_random = int((end_date - start_date).days / 20)
    for _ in range(num_random):
        evt_type = np.random.choice(random_event_types)
        evt_info = EVENT_TYPES[evt_type]
        random_date = start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))

        # Banjir cenderung di musim hujan
        if evt_type == "Banjir Besar" and random_date.month not in [11, 12, 1, 2, 3]:
            continue

        events.append({
            "date_start": random_date,
            "date_end": random_date + timedelta(days=evt_info["duration_days"]),
            "type": evt_type,
            "location": np.random.choice(list(LOCATIONS.keys())),
            "estimated_visitors": np.random.randint(500, 50000),
        })

    return events


def generate_historical_data():
    """Generate dataset historis volume sampah DKI Jakarta."""
    print("🔄 Generating DKI Jakarta historical waste data...")

    end_date = datetime(2026, 5, 15)
    start_date = end_date - timedelta(days=730)  # 2 tahun

    events = generate_events(start_date, end_date)

    records = []
    current_date = start_date

    while current_date <= end_date:
        month = current_date.month
        day_of_week = current_date.weekday()
        day_of_year = current_date.timetuple().tm_yday
        is_weekend = 1 if day_of_week >= 5 else 0

        season_name, season_factor = get_season(month)
        weather = generate_weather(current_date, season_name)
        weather_factor = WEATHER_CONDITIONS[weather]["impact_factor"]

        # Check city-wide events (like Lebaran)
        city_wide_factor = 1.0
        city_wide_event = None
        for evt in events:
            if evt["date_start"] <= current_date <= evt["date_end"]:
                evt_info = EVENT_TYPES.get(evt["type"], {})
                if evt_info.get("city_wide", False):
                    mult = evt_info["multiplier"]
                    if mult < city_wide_factor:
                        city_wide_factor = mult
                        city_wide_event = evt
                    elif mult > 1.0 and city_wide_factor >= 1.0:
                        if mult > city_wide_factor:
                            city_wide_factor = mult
                            city_wide_event = evt

        for loc_name, loc_info in LOCATIONS.items():
            # Base volume: kepadatan × faktor zona
            zone = loc_info["zone"]
            zone_factor = ZONE_FACTORS.get(zone, 23)
            base_volume = loc_info["population_density"] * zone_factor

            # Weekend effect (lebih banyak sampah rumah tangga)
            weekend_factor = 1.15 if is_weekend else 1.0

            # Payday effect (gajian = belanja naik)
            if 25 <= current_date.day <= 30 or 1 <= current_date.day <= 3:
                payday_factor = 1.12
            elif 13 <= current_date.day <= 17:
                payday_factor = 1.08
            else:
                payday_factor = 1.0

            # Local event impact
            event_factor = 1.0
            active_event = None
            active_visitors = 0

            for evt in events:
                if evt["date_start"] <= current_date <= evt["date_end"]:
                    evt_info = EVENT_TYPES.get(evt["type"], {})
                    if evt_info.get("city_wide", False):
                        continue  # Handled separately

                    if evt["location"] == loc_name or loc_info["zone"] in ["urban", "komersial"]:
                        evt_multiplier = evt_info["multiplier"]
                        if evt["location"] != loc_name:
                            evt_multiplier = 1.0 + (evt_multiplier - 1.0) * 0.2
                        if evt_multiplier > event_factor:
                            event_factor = evt_multiplier
                            active_event = evt["type"]
                            active_visitors = evt.get("estimated_visitors", 0)

            # Apply city-wide event
            if city_wide_event:
                active_event = city_wide_event["type"]
                active_visitors = city_wide_event.get("estimated_visitors", 0)

            # Car Free Day effect (Minggu pagi, area Sudirman-Thamrin)
            cfd_factor = 1.0
            if day_of_week == 6 and loc_name in ["Jakarta Pusat - Tanah Abang", "Jakarta Pusat - Menteng"]:
                cfd_factor = 1.08

            # Calculate final volume
            volume = (
                base_volume
                * season_factor
                * weather_factor
                * weekend_factor
                * payday_factor
                * event_factor
                * city_wide_factor
                * cfd_factor
            )

            # Realistic noise (±10%)
            noise = np.random.normal(1.0, 0.10)
            volume = max(50, volume * noise)

            # Komposisi sampah Jakarta (DLH data)
            organic_pct = np.random.uniform(0.55, 0.65)
            recyclable_pct = np.random.uniform(0.12, 0.22)

            records.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "location": loc_name,
                "latitude": loc_info["lat"],
                "longitude": loc_info["lon"],
                "zone": zone,
                "kota_adm": loc_info["kota_adm"],
                "population_density": loc_info["population_density"],
                "day_of_week": day_of_week,
                "day_of_month": current_date.day,
                "month": month,
                "year": current_date.year,
                "day_of_year": day_of_year,
                "is_weekend": is_weekend,
                "season": season_name,
                "weather": weather,
                "temperature_c": round(np.random.uniform(27, 36) if season_name == "Kemarau" else np.random.uniform(25, 33), 1),
                "humidity_pct": round(np.random.uniform(55, 78) if season_name == "Kemarau" else np.random.uniform(72, 98), 1),
                "rainfall_mm": round(max(0, np.random.normal(3, 5) if season_name == "Kemarau" else np.random.normal(18, 12)), 1),
                "event_name": active_event if active_event else "Tidak Ada",
                "event_visitors": active_visitors,
                "has_event": 1 if active_event else 0,
                "volume_kg": round(volume, 2),
                "organic_kg": round(volume * organic_pct, 2),
                "anorganic_kg": round(volume * (1 - organic_pct), 2),
                "recyclable_kg": round(volume * recyclable_pct, 2),
            })

        current_date += timedelta(days=1)

    df = pd.DataFrame(records)

    # Save to CSV
    output_path = os.path.join(DATA_DIR, "waste_historical.csv")
    df.to_csv(output_path, index=False)

    total_daily_avg = df.groupby("date")["volume_kg"].sum().mean()
    print(f"✅ Dataset DKI Jakarta saved: {output_path}")
    print(f"   📊 Total records: {len(df):,}")
    print(f"   📅 Period: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    print(f"   📍 Locations: {len(LOCATIONS)} kecamatan")
    print(f"   🗑️ Avg daily total: {total_daily_avg/1e6:.2f} Ton ({total_daily_avg/1e3:.0f} ton)")

    # Save events data
    events_data = []
    for evt in events:
        events_data.append({
            "date_start": evt["date_start"].strftime("%Y-%m-%d"),
            "date_end": evt["date_end"].strftime("%Y-%m-%d"),
            "type": evt["type"],
            "location": evt["location"],
            "estimated_visitors": evt.get("estimated_visitors", 0),
        })

    events_path = os.path.join(DATA_DIR, "events_history.json")
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(events_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Events saved: {events_path} ({len(events_data)} events)")

    return df


if __name__ == "__main__":
    df = generate_historical_data()
    print("\n📈 Sample statistics:")
    print(df[["volume_kg", "organic_kg", "anorganic_kg"]].describe().round(2))
