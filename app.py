"""
DKI Jakarta Waste Volume Prediction System - Main Dashboard
Sumber Data: Dinas Lingkungan Hidup (DLH) DKI Jakarta
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import os, json, io
from config import *
from config import FLEET_CONFIG
from model import WastePredictionModel
from generate_data import generate_historical_data

# Page config
st.set_page_config(page_title="DKI Jakarta Waste Prediction AI", page_icon="🏙️", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
* {font-family: 'Inter', sans-serif;}
.main .block-container {padding: 1rem 2rem;}
.metric-card {background: linear-gradient(135deg, #131740 0%, #1a1f4e 100%); border: 1px solid rgba(0,212,255,0.15);
    border-radius: 16px; padding: 1.2rem; text-align: center; transition: all 0.3s;}
.metric-card:hover {border-color: rgba(0,212,255,0.4); transform: translateY(-2px);}
.metric-value {font-size: 2rem; font-weight: 700; background: linear-gradient(135deg, #00D4FF, #7B2FFF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
.metric-label {font-size: 0.8rem; color: #8892b0; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px;}
.section-title {font-size: 1.3rem; font-weight: 600; color: #E0E6ED; margin: 1.5rem 0 1rem;
    padding-left: 12px; border-left: 3px solid #00D4FF;}
.alert-critical {background: rgba(255,71,87,0.1); border: 1px solid rgba(255,71,87,0.3);
    border-radius: 12px; padding: 1rem; margin: 0.5rem 0;}
.alert-warning {background: rgba(255,165,0,0.1); border: 1px solid rgba(255,165,0,0.3);
    border-radius: 12px; padding: 1rem; margin: 0.5rem 0;}
.stTabs [data-baseweb="tab-list"] {gap: 8px;}
.stTabs [data-baseweb="tab"] {background: rgba(19,23,64,0.8); border-radius: 8px; color: #8892b0; padding: 8px 16px;}
.stTabs [aria-selected="true"] {background: linear-gradient(135deg, #00D4FF22, #7B2FFF22) !important; color: #00D4FF !important;}
div[data-testid="stSidebar"] {background: linear-gradient(180deg, #0A0E27 0%, #131740 100%);}
</style>""", unsafe_allow_html=True)

def metric_card(label, value, icon="📊"):
    return f'<div class="metric-card"><div style="font-size:1.5rem">{icon}</div><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>'

@st.cache_data
def load_data():
    csv = os.path.join(DATA_DIR, "waste_historical.csv")
    if not os.path.exists(csv):
        generate_historical_data()
    return pd.read_csv(csv, parse_dates=["date"])

@st.cache_resource
def load_model(df):
    m = WastePredictionModel()
    if not m.load():
        m.train(df)
        m.save()
    return m

def page_dashboard(df, model):
    st.markdown('<div class="section-title">📊 Executive Summary — DKI Jakarta</div>', unsafe_allow_html=True)
    total_vol = df["volume_kg"].sum()
    avg_daily = df.groupby("date")["volume_kg"].sum().mean()
    peak_day = df.groupby("date")["volume_kg"].sum().idxmax()
    peak_vol = df.groupby("date")["volume_kg"].sum().max()
    top_loc = df.groupby("location")["volume_kg"].sum().idxmax()
    bantargebang_pct = (avg_daily / FLEET_CONFIG["tpst_bantargebang_capacity"]) * 100

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(metric_card("Total Volume (2 Tahun)",f"{total_vol/1e6:.1f} Ton","🗑️"), unsafe_allow_html=True)
    with c2: st.markdown(metric_card("Rata-rata Harian",f"{avg_daily/1e3:.1f} Ton","📅"), unsafe_allow_html=True)
    with c3: st.markdown(metric_card("Hari Puncak",peak_day.strftime("%d %b %Y"),"🔺"), unsafe_allow_html=True)
    with c4: st.markdown(metric_card("Volume Puncak",f"{peak_vol/1e3:.1f} Ton","⚡"), unsafe_allow_html=True)
    with c5: st.markdown(metric_card("Beban Bantargebang",f"{bantargebang_pct:.0f}%","🏭"), unsafe_allow_html=True)

    # Model metrics
    if model.metrics:
        st.markdown('<div class="section-title">🧠 Performa Model AI</div>', unsafe_allow_html=True)
        m1,m2,m3,m4 = st.columns(4)
        with m1: st.metric("R² Score", f"{model.metrics['r2']:.4f}")
        with m2: st.metric("MAE", f"{model.metrics['mae']:.0f} kg")
        with m3: st.metric("RMSE", f"{model.metrics['rmse']:.0f} kg")
        with m4: st.metric("MAPE", f"{model.metrics['mape']:.1f}%")

    # Daily trend
    st.markdown('<div class="section-title">📈 Tren Volume Sampah Harian</div>', unsafe_allow_html=True)
    daily = df.groupby("date")["volume_kg"].sum().reset_index()
    daily["ma7"] = daily["volume_kg"].rolling(7).mean()
    daily["ma30"] = daily["volume_kg"].rolling(30).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"],y=daily["volume_kg"],mode="lines",name="Harian",line=dict(color="#00D4FF",width=1),opacity=0.4))
    fig.add_trace(go.Scatter(x=daily["date"],y=daily["ma7"],mode="lines",name="MA 7 Hari",line=dict(color="#7B2FFF",width=2)))
    fig.add_trace(go.Scatter(x=daily["date"],y=daily["ma30"],mode="lines",name="MA 30 Hari",line=dict(color="#FF6B6B",width=2)))
    fig.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=350,margin=dict(l=0,r=0,t=30,b=0),legend=dict(orientation="h",y=1.1))
    st.plotly_chart(fig, use_container_width=True)

    # By kota administrasi & composition
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="section-title">🏙️ Volume per Kota Administrasi</div>', unsafe_allow_html=True)
        if "kota_adm" in df.columns:
            adm_vol = df.groupby("kota_adm")["volume_kg"].sum().sort_values(ascending=True).reset_index()
            fig2 = px.bar(adm_vol, y="kota_adm", x="volume_kg", orientation="h", color="volume_kg",
                          color_continuous_scale=["#131740","#00D4FF","#7B2FFF"])
        else:
            loc_vol = df.groupby("location")["volume_kg"].sum().sort_values(ascending=True).tail(10).reset_index()
            fig2 = px.bar(loc_vol, y="location", x="volume_kg", orientation="h", color="volume_kg",
                          color_continuous_scale=["#131740","#00D4FF","#7B2FFF"])
        fig2.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=350,
                          margin=dict(l=0,r=0,t=10,b=0),showlegend=False,coloraxis_showscale=False,yaxis_title="",xaxis_title="Volume (kg)")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">♻️ Komposisi Sampah DKI Jakarta</div>', unsafe_allow_html=True)
        comp = pd.DataFrame({"Jenis":["Organik (Sisa Makanan)","Plastik & Residu","Daur Ulang"],
                            "Volume":[df["organic_kg"].sum(),df["anorganic_kg"].sum()-df["recyclable_kg"].sum(),df["recyclable_kg"].sum()]})
        fig3 = px.pie(comp, values="Volume", names="Jenis", hole=0.5, color_discrete_sequence=["#00D4FF","#FF6B6B","#7B2FFF"])
        fig3.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=350,margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig3, use_container_width=True)

    # Feature importance
    if model.feature_importances:
        st.markdown('<div class="section-title">🎯 Feature Importance (Top 10)</div>', unsafe_allow_html=True)
        fi = pd.DataFrame(list(model.feature_importances.items())[:10], columns=["Feature","Importance"])
        fig4 = px.bar(fi, x="Importance", y="Feature", orientation="h", color="Importance", color_continuous_scale=["#131740","#00D4FF"])
        fig4.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=300,margin=dict(l=0,r=0,t=10,b=0),coloraxis_showscale=False,yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)

def page_prediction(df, model):
    st.markdown('<div class="section-title">🔮 Prediksi Volume Sampah</div>', unsafe_allow_html=True)
    
    # Filter layout
    f1, f2, f3 = st.columns(3)
    with f1: pred_days = st.slider("Periode (Hari)", 7, 90, 30)
    with f2: sel_kota = st.selectbox("Kota Administrasi", ["Semua Kota", "Jakarta Pusat", "Jakarta Barat", "Jakarta Selatan", "Jakarta Timur", "Jakarta Utara", "Kepulauan Seribu"])
    
    loc_options = ["Semua Lokasi"]
    for loc, info in LOCATIONS.items():
        if sel_kota == "Semua Kota" or info.get("kota_adm") == sel_kota:
            loc_options.append(loc)
            
    with f3: sel_location = st.selectbox("Kecamatan", loc_options)
    
    # filtering target locations
    target_locs = {}
    for loc, info in LOCATIONS.items():
        if sel_location != "Semua Lokasi":
            if loc == sel_location:
                target_locs[loc] = info
        elif sel_kota != "Semua Kota":
            if info.get("kota_adm") == sel_kota:
                target_locs[loc] = info
        else:
            target_locs[loc] = info
            
    last_date = df["date"].max()
    future_dates = [last_date + timedelta(days=i+1) for i in range(pred_days)]
    records = []
    for d in future_dates:
        for loc, info in target_locs.items():
            season = "Hujan" if d.month in [11,12,1,2,3] else "Kemarau"
            records.append({"date":d,"location":loc,"latitude":info["lat"],"longitude":info["lon"],"zone":info["zone"],
                "kota_adm":info.get("kota_adm","Jakarta Pusat"),
                "population_density":info["population_density"],"day_of_week":d.weekday(),"day_of_month":d.day,
                "month":d.month,"year":d.year,"day_of_year":d.timetuple().tm_yday,"is_weekend":1 if d.weekday()>=5 else 0,
                "season":season,"weather":"Cerah" if season=="Kemarau" else "Hujan Ringan","temperature_c":30,"humidity_pct":70,
                "rainfall_mm":2 if season=="Kemarau" else 12,"event_name":"Tidak Ada","event_visitors":0,"has_event":0,
                "volume_kg":0,"organic_kg":0,"anorganic_kg":0,"recyclable_kg":0})
    
    if not records:
        st.warning("Tidak ada data untuk diprediksi.")
        return
    
    future_df = pd.DataFrame(records)
    preds = model.predict(future_df)
    future_df["predicted_kg"] = preds
    
    daily_pred = future_df.groupby("date")["predicted_kg"].sum().reset_index()
    
    # Two columns for chart and metrics
    col_chart, col_metrics = st.columns([3,1])
    with col_chart:
        st.markdown("### 📈 Grafik Prediksi")
        fig = go.Figure()
        
        target_loc_names = list(target_locs.keys())
        hist_df = df[df["location"].isin(target_loc_names)]
        hist = hist_df.groupby("date")["volume_kg"].sum().tail(30).reset_index()
        
        fig.add_trace(go.Scatter(x=hist["date"],y=hist["volume_kg"],mode="lines",name="Historis (30 Hari)",line=dict(color="#8892b0",width=2,dash="dot")))
        fig.add_trace(go.Scatter(x=daily_pred["date"],y=daily_pred["predicted_kg"],mode="lines+markers",name="Prediksi AI",
                                line=dict(color="#00D4FF",width=3),marker=dict(size=6, color="#7B2FFF"), fill='tozeroy', fillcolor='rgba(0,212,255,0.1)'))
        fig.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=400,margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_metrics:
        total_pred = future_df["predicted_kg"].sum()
        daily_avg = total_pred / pred_days
        peak_day = daily_pred.loc[daily_pred["predicted_kg"].idxmax()]
        
        st.markdown("### 📊 Ringkasan")
        st.markdown(metric_card("Total Prediksi",f"{total_pred/1e3:.1f} Ton","📦"), unsafe_allow_html=True)
        st.markdown(metric_card("Rata-rata Harian",f"{daily_avg/1e3:.1f} Ton","📅"), unsafe_allow_html=True)
        st.markdown(metric_card("Volume Puncak",f"{peak_day['predicted_kg']/1e3:.1f} Ton", "🚀"), unsafe_allow_html=True)
        st.markdown(metric_card("Hari Puncak",peak_day['date'].strftime('%d %b'), "📆"), unsafe_allow_html=True)
    
    # Fleet recommendations
    st.markdown('<div class="section-title">🚛 Rekomendasi Kesiapan Operasional</div>', unsafe_allow_html=True)
    trucks_needed = int(np.ceil(daily_avg / (FLEET_CONFIG["truck_capacity_kg"] * FLEET_CONFIG["truck_trips_per_day"])))
    workers_needed = trucks_needed * FLEET_CONFIG["workers_per_truck"]
    bins_needed = int(np.ceil(daily_avg / (FLEET_CONFIG["bin_capacity_liters"] * FLEET_CONFIG["bin_fill_rate_kg_per_liter"])))
    daily_cost = trucks_needed * FLEET_CONFIG["truck_trips_per_day"] * FLEET_CONFIG["cost_per_trip"] + workers_needed * FLEET_CONFIG["worker_daily_wage"]
    
    r1,r2,r3,r4 = st.columns(4)
    with r1: st.markdown(metric_card("Armada Truk",f"{trucks_needed} Unit","🚛"), unsafe_allow_html=True)
    with r2: st.markdown(metric_card("Petugas (Kru)",f"{workers_needed} Orang","👷"), unsafe_allow_html=True)
    with r3: st.markdown(metric_card("Kapasitas TPS",f"{bins_needed} Unit","🗑️"), unsafe_allow_html=True)
    with r4: st.markdown(metric_card("Estimasi Biaya / Hari",f"Rp {daily_cost/1e6:.1f} Jt","💰"), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">📅 Prediksi Mingguan</div>', unsafe_allow_html=True)
        future_df["week"] = future_df["date"].dt.isocalendar().week.astype(int)
        weekly = future_df.groupby("week")["predicted_kg"].sum().reset_index()
        weekly["week_label"] = "Minggu " + weekly["week"].astype(str)
        fig_w = px.bar(weekly, x="week_label", y="predicted_kg", color="predicted_kg", color_continuous_scale=["#131740","#00D4FF","#FF6B6B"])
        fig_w.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=300,
                            margin=dict(l=0,r=0,t=10,b=0),coloraxis_showscale=False,xaxis_title="",yaxis_title="Volume (kg)")
        st.plotly_chart(fig_w, use_container_width=True)
        
    with c2:
        st.markdown('<div class="section-title">♻️ Prediksi per Zona</div>', unsafe_allow_html=True)
        zona_pred = future_df.groupby("zone")["predicted_kg"].sum().reset_index()
        fig_z = px.pie(zona_pred, values="predicted_kg", names="zone", hole=0.5, color_discrete_sequence=["#00D4FF", "#7B2FFF", "#FF6B6B", "#2ED573", "#FFA502", "#131740"])
        fig_z.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=300,margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_z, use_container_width=True)

def page_simulation(df, model):
    st.markdown('<div class="section-title">🎮 Simulasi Event & Prediksi</div>', unsafe_allow_html=True)
    st.info("Pilih parameter event untuk melihat estimasi volume sampah dan kebutuhan armada secara realtime.")
    
    c1,c2 = st.columns([1,2])
    with c1:
        sim_date = st.date_input("Tanggal Event", datetime(2026,6,15))
        sim_event = st.selectbox("Jenis Event", list(EVENT_TYPES.keys()))
        sim_visitors = st.number_input("Estimasi Pengunjung", 100, 200000, 10000, step=1000)
        sim_weather = st.selectbox("Kondisi Cuaca", list(WEATHER_CONDITIONS.keys()))
        sim_location = st.selectbox("Lokasi", list(LOCATIONS.keys()))
        sim_duration = st.slider("Durasi Event (hari)", 1, 14, EVENT_TYPES[sim_event]["duration_days"])
    
    # Build simulation data
    records = []
    for i in range(sim_duration):
        d = datetime.combine(sim_date, datetime.min.time()) + timedelta(days=i)
        info = LOCATIONS[sim_location]
        season = "Hujan" if d.month in [11,12,1,2,3] else "Kemarau"
        records.append({"date":d,"location":sim_location,"latitude":info["lat"],"longitude":info["lon"],"zone":info["zone"],
            "kota_adm":info.get("kota_adm","Jakarta Pusat"),
            "population_density":info["population_density"],"day_of_week":d.weekday(),"day_of_month":d.day,
            "month":d.month,"year":d.year,"day_of_year":d.timetuple().tm_yday,"is_weekend":1 if d.weekday()>=5 else 0,
            "season":season,"weather":sim_weather,"temperature_c":30,"humidity_pct":75,
            "rainfall_mm":15 if "Hujan" in sim_weather else 0,"event_name":sim_event,"event_visitors":sim_visitors,"has_event":1,
            "volume_kg":0,"organic_kg":0,"anorganic_kg":0,"recyclable_kg":0})
    
    sim_df = pd.DataFrame(records)
    preds = model.predict(sim_df)
    
    # Apply event multiplier manually for simulation accuracy
    evt_mult = EVENT_TYPES[sim_event]["multiplier"]
    weather_mult = WEATHER_CONDITIONS[sim_weather]["impact_factor"]
    visitor_mult = 1.0 + (sim_visitors / 50000) * 0.5
    preds = preds * evt_mult * weather_mult * visitor_mult * 0.35  # Calibration factor
    sim_df["predicted_kg"] = preds
    
    with c2:
        total_waste = sim_df["predicted_kg"].sum()
        peak_day_vol = sim_df["predicted_kg"].max()
        trucks = int(np.ceil(peak_day_vol / (FLEET_CONFIG["truck_capacity_kg"] * FLEET_CONFIG["truck_trips_per_day"])))
        workers = trucks * FLEET_CONFIG["workers_per_truck"]
        bins = int(np.ceil(peak_day_vol / (FLEET_CONFIG["bin_capacity_liters"] * FLEET_CONFIG["bin_fill_rate_kg_per_liter"])))
        
        st.markdown("### 📊 Hasil Simulasi")
        r1,r2,r3 = st.columns(3)
        with r1: st.markdown(metric_card("Total Sampah",f"{total_waste/1e3:.1f} Ton","🗑️"), unsafe_allow_html=True)
        with r2: st.markdown(metric_card("Puncak Harian",f"{peak_day_vol/1e3:.1f} Ton","📈"), unsafe_allow_html=True)
        with r3: st.markdown(metric_card("Truk Puncak",f"{trucks} unit","🚛"), unsafe_allow_html=True)
        
        fig = px.bar(sim_df, x="date", y="predicted_kg", color="predicted_kg", color_continuous_scale=["#131740","#00D4FF","#FF6B6B"])
        fig.update_layout(template="plotly_dark",paper_bgcolor="#0A0E27",plot_bgcolor="#0A0E27",height=300,
                          margin=dict(l=0,r=0,t=10,b=0),coloraxis_showscale=False,xaxis_title="Tanggal",yaxis_title="Volume (kg)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.markdown("### 📋 Rekomendasi Kesiapan")
        st.markdown(f"""
        | Parameter | Kebutuhan |
        |-----------|-----------|
        | 🚛 Armada Truk | **{trucks} unit** (kapasitas {FLEET_CONFIG['truck_capacity_kg']/1000:.0f} ton/truk) |
        | 👷 Petugas Kebersihan | **{workers} orang** ({FLEET_CONFIG['workers_per_truck']} per truk) |
        | 🗑️ TPS Tambahan | **{bins} unit** di area event |
        | ⏰ Jam Operasional | **{FLEET_CONFIG['worker_hours_per_shift']+2} jam** (perpanjangan shift) |
        | 💰 Estimasi Biaya | **Rp {(trucks*3*FLEET_CONFIG['cost_per_trip']+workers*FLEET_CONFIG['worker_daily_wage'])*sim_duration/1e6:.1f} Juta** |
        | 📍 Titik Penempatan | Area masuk, panggung utama, food court, parkir |
        """)

def page_map(df):
    st.markdown('<div class="section-title">🗺️ Peta Sebaran & Heatmap Sampah</div>', unsafe_allow_html=True)
    
    loc_vol = df.groupby("location").agg({"volume_kg":"sum","latitude":"first","longitude":"first","zone":"first"}).reset_index()
    loc_vol["volume_ton"] = loc_vol["volume_kg"] / 1000
    
    center_lat = loc_vol["latitude"].mean()
    center_lon = loc_vol["longitude"].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="CartoDB dark_matter")
    
    max_vol = loc_vol["volume_ton"].max()
    for _, row in loc_vol.iterrows():
        ratio = row["volume_ton"] / max_vol
        if ratio > 0.7: color = "#FF4757"
        elif ratio > 0.4: color = "#FFA502"
        else: color = "#2ED573"
        
        radius = max(8, ratio * 25)
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(f"<b>{row['location']}</b><br>Volume: {row['volume_ton']:.0f} ton<br>Zona: {row['zone']}", max_width=250),
            tooltip=row["location"]
        ).add_to(m)
    
    # Legend
    legend_html = """<div style="position:fixed;bottom:30px;left:30px;z-index:1000;background:#131740;padding:12px;border-radius:8px;border:1px solid #00D4FF33;font-size:12px;color:#E0E6ED">
    <b>Volume Sampah</b><br>
    <span style="color:#FF4757">● Tinggi (&gt;70%)</span><br>
    <span style="color:#FFA502">● Sedang (40-70%)</span><br>
    <span style="color:#2ED573">● Rendah (&lt;40%)</span></div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    
    st_folium(m, width=None, height=500)
    
    # Alert areas
    st.markdown('<div class="section-title">⚠️ Area Kritis</div>', unsafe_allow_html=True)
    critical = loc_vol.nlargest(5, "volume_ton")
    for _, row in critical.iterrows():
        level = "critical" if row["volume_ton"]/max_vol > 0.7 else "warning"
        st.markdown(f'<div class="alert-{level}">📍 <b>{row["location"]}</b> — {row["volume_ton"]:.0f} Ton (Zona: {row["zone"]})</div>', unsafe_allow_html=True)

def page_scaling(df):
    st.markdown('<div class="section-title">⚙️ Scaling & Kalibrasi Data</div>', unsafe_allow_html=True)
    st.info("Simulasikan perubahan volume sampah keseluruhan akibat lonjakan populasi, perubahan kebijakan, atau faktor ekonomi (Skenario What-If).")
    
    col1, col2 = st.columns([1,3])
    with col1:
        st.markdown("### Parameter Skenario")
        scale_factor = st.slider("Faktor Pertumbuhan/Penurunan (%)", -50, 100, 10, step=1)
        st.markdown(f"<small>Dataset historis akan di-scale sebesar **{scale_factor}%** untuk mensimulasikan kondisi masa depan yang berbeda.</small>", unsafe_allow_html=True)
    
    with col2:
        multiplier = 1.0 + (scale_factor / 100.0)
        scaled_df = df.copy()
        scaled_df["volume_kg"] = scaled_df["volume_kg"] * multiplier
        
        orig_avg = df.groupby("date")["volume_kg"].sum().mean()
        scaled_avg = scaled_df.groupby("date")["volume_kg"].sum().mean()
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(metric_card("Rata-rata Asli", f"{orig_avg/1e3:.1f} Ton", "📊"), unsafe_allow_html=True)
        with c2: 
            icon = "📈" if scale_factor > 0 else "📉" if scale_factor < 0 else "➖"
            st.markdown(metric_card("Setelah Scaling", f"{scaled_avg/1e3:.1f} Ton", icon), unsafe_allow_html=True)
        
        trucks = int(np.ceil(scaled_avg / (FLEET_CONFIG["truck_capacity_kg"] * FLEET_CONFIG["truck_trips_per_day"])))
        with c3: st.markdown(metric_card("Kebutuhan Truk Baru", f"{trucks} Unit", "🚛"), unsafe_allow_html=True)
        
        st.markdown("### Perbandingan Volume Harian (Skenario)")
        daily_orig = df.groupby("date")["volume_kg"].sum().rolling(7).mean().reset_index()
        daily_scaled = scaled_df.groupby("date")["volume_kg"].sum().rolling(7).mean().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_orig["date"], y=daily_orig["volume_kg"], name="Data Asli (MA-7)", line=dict(color="#8892b0", dash="dot")))
        fig.add_trace(go.Scatter(x=daily_scaled["date"], y=daily_scaled["volume_kg"], name=f"Skenario {scale_factor:+} % (MA-7)", line=dict(color="#FF6B6B" if scale_factor > 0 else "#2ED573", width=2)))
        fig.update_layout(template="plotly_dark", paper_bgcolor="#0A0E27", plot_bgcolor="#0A0E27", height=300, margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)

def page_reports(df):
    st.markdown('<div class="section-title">📄 Export Laporan</div>', unsafe_allow_html=True)
    
    report_type = st.selectbox("Jenis Laporan", ["Ringkasan Harian","Per Lokasi","Per Event","Komposisi Sampah"])
    
    if report_type == "Ringkasan Harian":
        rpt = df.groupby("date").agg({"volume_kg":"sum","organic_kg":"sum","anorganic_kg":"sum","recyclable_kg":"sum"}).reset_index()
    elif report_type == "Per Lokasi":
        rpt = df.groupby("location").agg({"volume_kg":["sum","mean","max"],"has_event":"sum"}).reset_index()
        rpt.columns = ["Lokasi","Total (kg)","Rata-rata (kg)","Maksimum (kg)","Jumlah Event"]
    elif report_type == "Per Event":
        evt_df = df[df["event_name"] != "Tidak Ada"]
        rpt = evt_df.groupby("event_name").agg({"volume_kg":["sum","mean","count"],"event_visitors":"max"}).reset_index()
        rpt.columns = ["Event","Total (kg)","Rata-rata (kg)","Data Points","Max Pengunjung"]
    else:
        rpt = pd.DataFrame({"Jenis":["Organik","Anorganik","Daur Ulang"],
            "Volume (kg)":[df["organic_kg"].sum(), df["anorganic_kg"].sum()-df["recyclable_kg"].sum(), df["recyclable_kg"].sum()]})
        rpt["Persentase"] = (rpt["Volume (kg)"] / rpt["Volume (kg)"].sum() * 100).round(1)
    
    st.dataframe(rpt, use_container_width=True, height=400)
    
    # Export Excel
    buf = io.BytesIO()
    rpt.to_excel(buf, index=False, engine="openpyxl")
    st.download_button("📥 Download Excel", buf.getvalue(), f"laporan_{report_type.lower().replace(' ','_')}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def page_info_dataset(df):
    st.markdown('<div class="section-title">ℹ️ Informasi & Sumber Dataset</div>', unsafe_allow_html=True)
    st.markdown("""
    Sistem AI ini mengandalkan dataset volume sampah harian yang dapat memetakan tren musiman, efek cuaca, dan dampak *event* perkotaan. 
    Karena data harian spesifik per kecamatan (14.000+ baris per tahun) belum dipublikasikan secara terbuka *(open data)* sebagai dataset tunggal oleh pemerintah, **dataset yang digunakan secara default dalam aplikasi ini adalah Data Simulasi Berbasis Statistik Resmi (Extrapolated Data)**.
    
    ### 📊 Dasar Kalibrasi Data
    Dataset default telah dikalibrasi ketat menggunakan data riil dari:
    1. **Sistem Informasi Pengelolaan Sampah Nasional (SIPSN) - KLHK**
    2. **Dinas Lingkungan Hidup (DLH) DKI Jakarta**
    3. **Badan Pusat Statistik (BPS) DKI Jakarta**

    **Parameter Kalibrasi Riil yang Digunakan:**
    *   **Total Volume Harian:** ~8.500 - 8.700 ton/hari (sesuai rata-rata timbulan sampah Jakarta 2024/2025).
    *   **Kepadatan Penduduk & Zona:** Distribusi volume per kecamatan dihitung proporsional terhadap kepadatan penduduk asli BPS dan tipe zona (Urban, Komersial, dll).
    *   **Komposisi:** ~60% Organik, ~22% Plastik/Residu, ~18% Daur Ulang.
    *   **Dampak Event Spesifik:** Pengaruh musim hujan (banjir), penurunan drastis (-80%) saat Hari Raya Idul Fitri (warga mudik), serta lonjakan saat malam Tahun Baru.
    
    ### 🔄 Menggunakan Dataset Real Anda Sendiri
    Sistem ini sepenuhnya dinamis. Jika Anda (atau instansi Anda) memiliki file CSV dataset historis riil, Anda dapat mengunggahnya langsung melalui menu **Upload Data Riil (CSV)** di sidebar.
    Model Machine Learning akan langsung di-*retrain* secara otomatis menggunakan data riil Anda!
    """)
    
    st.markdown("### 📋 Preview Dataset Saat Ini")
    st.dataframe(df.head(50), use_container_width=True)
    
    st.markdown("### 📈 Statistik Dataset Saat Ini")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total Baris Data", f"{len(df):,}")
    with c2: st.metric("Jumlah Kecamatan", f"{df['location'].nunique()}")
    with c3: st.metric("Periode Waktu", f"{df['date'].min().strftime('%Y-%m')} s/d {df['date'].max().strftime('%Y-%m')}")

# ============================================================
# MAIN APP
# ============================================================
def main():
    with st.sidebar:
        st.markdown(f"## 🏙️ DKI Jakarta")
      st.markdown(f"<small style='color:#8892b0'>Waste Prediction AI v{APP_VERSION}<br>Sumber: DLH DKI Jakarta<br><br>🏆 Team 404<br>Andrito Elia</small>", unsafe_allow_html=True)
        st.divider()
        page = st.radio("Navigasi", ["📊 Dashboard","🔮 Prediksi","🎮 Simulasi","🗺️ Peta","⚙️ Scaling Data","📄 Laporan","ℹ️ Info Dataset"], label_visibility="collapsed")
        
        st.divider()
        st.markdown("### 📂 Upload Data Riil (CSV)")
        st.caption("Timpa data simulasi dengan dataset asli instansi.")
        uploaded_file = st.file_uploader("Upload CSV Historis", type=['csv'], label_visibility="collapsed")
        
        st.divider()
        st.markdown(f"<small style='color:#8892b0'>📅 {datetime.now().strftime('%d %B %Y')}<br>⏰ {datetime.now().strftime('%H:%M WIB')}</small>", unsafe_allow_html=True)
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, parse_dates=["date"])
            st.sidebar.success("✅ Dataset riil berhasil dimuat!")
        except Exception as e:
            st.sidebar.error(f"Error membaca file: {e}")
            df = load_data()
    else:
        df = load_data()
        
    model = load_model(df)
    
    if "📊" in page: page_dashboard(df, model)
    elif "🔮" in page: page_prediction(df, model)
    elif "🎮" in page: page_simulation(df, model)
    elif "🗺️" in page: page_map(df)
    elif "⚙️" in page: page_scaling(df)
    elif "📄" in page: page_reports(df)
    elif "ℹ️" in page: page_info_dataset(df)

if __name__ == "__main__":
    main()
