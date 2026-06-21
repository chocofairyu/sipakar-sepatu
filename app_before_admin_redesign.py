"""
app.py
Antarmuka Streamlit — Sistem Pakar Pencucian Sepatu
Metode: Certainty Factor (CF)
"""

import hashlib
import streamlit as st
import pandas as pd
from database import (
    get_semua_bahan, get_semua_noda, get_semua_metode,
    get_aturan_by_bahan_noda, get_semua_aturan,
    simpan_konsultasi, get_riwayat_konsultasi, get_statistik,
)
from cf_engine import (
    inferensi, inferensi_noda_ganda,
    perlu_profesional, ringkasan_perhitungan,
)

# ─────────────────────────────────────────────
# Kredensial admin
# Ganti password ini sesuai kebutuhan.
# ─────────────────────────────────────────────
ADMIN_PASSWORD = "admin123"

# ─────────────────────────────────────────────
# Konfigurasi halaman
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SiPakar Sepatu",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Inisialisasi session state
# ─────────────────────────────────────────────
if "saved_keys" not in st.session_state:
    st.session_state.saved_keys = set()
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


def get_risk_profile(cf_final, bahan, jumlah_noda):
    """Buat label risiko yang mudah dipahami user setelah hasil CF muncul."""
    bahan_sensitif = ["Suede", "Nubuck", "Satin", "Kulit Asli"]
    risk_score = 0

    if cf_final < 0.45:
        risk_score += 2
    elif cf_final < 0.65:
        risk_score += 1

    if jumlah_noda > 1:
        risk_score += 1
    if any(item.lower() in bahan.lower() for item in bahan_sensitif):
        risk_score += 1

    if risk_score >= 3:
        return {
            "label": "Risiko Tinggi",
            "color": "#B42318",
            "bg": "#FFF1F0",
            "note": "Kerjakan perlahan, tes area kecil dulu, dan pertimbangkan jasa profesional.",
        }
    if risk_score == 2:
        return {
            "label": "Risiko Sedang",
            "color": "#B54708",
            "bg": "#FFF7E6",
            "note": "Masih aman dikerjakan mandiri jika alat sesuai dan tidak terlalu basah.",
        }
    return {
        "label": "Risiko Rendah",
        "color": "#027A48",
        "bg": "#ECFDF3",
        "note": "Cocok untuk perawatan mandiri dengan prosedur pembersihan normal.",
    }


def get_care_steps(nama_metode, bahan, noda_list, butuh_profesional):
    """Checklist langkah perawatan yang mengikuti rekomendasi metode."""
    steps = [
        "Lepas tali sepatu dan insole agar area kotor lebih mudah dijangkau.",
        "Bersihkan debu kering memakai sikat halus sebelum diberi cairan pembersih.",
        "Tes cairan pembersih di area kecil yang tidak terlalu terlihat.",
    ]

    metode = nama_metode.lower()
    if "dry" in metode or butuh_profesional:
        steps.append("Hindari merendam sepatu; gunakan pembersihan kering atau serahkan ke profesional.")
    elif "spot" in metode:
        steps.append("Fokuskan cairan hanya pada titik noda, lalu angkat sisa cairan dengan kain microfiber.")
    elif "rendam" in metode:
        steps.append("Rendam singkat saja, jangan lebih dari 10-15 menit, lalu bilas sampai tidak berbusa.")
    elif "steam" in metode:
        steps.append("Gunakan uap dari jarak aman dan jangan terlalu lama pada satu titik.")
    else:
        steps.append("Sikat perlahan searah serat bahan, jangan menekan terlalu kuat.")

    if any(item.lower() in bahan.lower() for item in ["suede", "nubuck"]):
        steps.append("Untuk suede/nubuck, rapikan kembali tekstur bahan dengan suede brush setelah kering.")
    if any("minyak" in noda.lower() for noda in noda_list):
        steps.append("Untuk noda minyak, taburi sedikit baking soda atau bedak sebelum pembersihan basah.")

    steps.append("Keringkan di tempat teduh dan berangin; jangan dijemur langsung di bawah matahari.")
    return steps


def get_toolkit(nama_metode, bahan):
    """Daftar alat praktis yang bisa disiapkan pengguna."""
    tools = ["Sikat halus", "Kain microfiber", "Air bersih secukupnya"]
    metode = nama_metode.lower()

    if "suede" in bahan.lower() or "nubuck" in bahan.lower():
        tools.extend(["Suede brush", "Penghapus suede"])
    if "enzim" in metode:
        tools.append("Pembersih enzimatik")
    elif "kimia" in metode:
        tools.append("Cleaner khusus sepatu")
    elif "dry" in metode:
        tools.append("Dry cleaning kit")
    else:
        tools.append("Sabun sepatu pH ringan")

    return tools


def build_report(nama_pengguna, bahan, noda_list, cf_user, hasil, risk_profile, care_steps, tools):
    """Susun ringkasan hasil agar bisa diunduh sebagai TXT."""
    nama = nama_pengguna or "Anonim"
    lines = [
        "LAPORAN KONSULTASI SIPAKAR SEPATU",
        "=" * 40,
        f"Nama pengguna     : {nama}",
        f"Bahan sepatu      : {bahan}",
        f"Jenis noda        : {', '.join(noda_list)}",
        f"Keyakinan user    : {cf_user}",
        "",
        "HASIL REKOMENDASI",
        f"Metode utama      : {hasil.nama_metode}",
        f"CF akhir          : {hasil.cf_final} ({hasil.persentase}%)",
        f"Interpretasi      : {hasil.label_keyakinan}",
        f"Level risiko      : {risk_profile['label']}",
        f"Catatan risiko    : {risk_profile['note']}",
        "",
        "CHECKLIST PERAWATAN",
    ]
    lines.extend([f"{idx}. {step}" for idx, step in enumerate(care_steps, start=1)])
    lines.extend(["", "ALAT YANG DISARANKAN", ", ".join(tools)])
    return "\n".join(lines)

# ─────────────────────────────────────────────
# CSS Profesional
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Import font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Root variabel ── */
:root {
    --primary:      #123C3A;
    --primary-mid:  #1F7A68;
    --accent:       #E7A93B;
    --accent-soft:  #FFF4D6;
    --bg:           #F6F8FB;
    --card:         #FFFFFF;
    --border:       #DCE5E8;
    --text:         #172321;
    --text-mid:     #435653;
    --text-muted:   #71827F;
    --success-bg:   #EAF8F1;
    --success-fg:   #087443;
    --warn-bg:      #FFF7E6;
    --warn-fg:      #9A5B00;
    --danger-bg:    #FFF1F0;
    --danger-fg:    #B42318;
    --radius:       8px;
    --shadow:       0 12px 28px rgba(18,60,58,0.08);
}

/* ── Global ── */
.stApp {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background:
        linear-gradient(180deg, #FFFFFF 0%, var(--bg) 42%, #EEF4F4 100%);
    color: var(--text);
    font-size: 20px;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #123C3A 0%, #0E2E2C 100%) !important;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.90) !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 19.5px !important;
    padding: 7px 0 !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.2) !important;
}

/* ── Perbaikan kontras komponen putih di sidebar (login admin) ── */
[data-testid="stSidebar"] details summary,
[data-testid="stSidebar"] details summary * {
    color: rgba(255,255,255,0.95) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] details summary svg {
    fill: rgba(255,255,255,0.95) !important;
}
[data-testid="stSidebar"] input {
    color: var(--text) !important;
}
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] > button {
    color: #123C3A !important;
    background: var(--accent) !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25) !important;
}
[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] > button:hover {
    background: var(--primary-mid) !important;
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] .sidebar-error-box,
[data-testid="stSidebar"] .sidebar-error-box * {
    color: #9B1C1C !important;
}
.sidebar-error-box {
    background: #FCECEA;
    border: 1px solid #C0392B;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 15.5px;
    font-weight: 600;
    margin-top: 8px;
}

/* ── Judul halaman ── */
h1 { font-size: 2.2rem !important; font-weight: 700 !important; color: var(--primary) !important; }
h2 { font-size: 1.75rem !important; font-weight: 700 !important; color: var(--primary) !important; }
h3 { font-size: 1.5rem !important; font-weight: 600 !important; color: var(--text) !important; }
h4 { font-size: 1.35rem !important; font-weight: 600 !important; }

/* ── Label input ── */
label, .stRadio label span, .stSelectbox label {
    font-size: 18.5px !important;
    font-weight: 500 !important;
    color: var(--text-mid) !important;
}

/* ── Caption ── */
.stCaption, small, .caption-text {
    font-size: 17px !important;
    color: var(--text-muted) !important;
}

/* ── Card hasil rekomendasi ── */
.hasil-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 6px solid var(--primary-mid);
    border-radius: var(--radius);
    padding: 1.5rem 1.7rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.hasil-card.warning { border-left-color: #D4801A; background: var(--warn-bg); }
.hasil-card.danger  { border-left-color: #C0392B; background: var(--danger-bg); }

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 17px;
    font-weight: 600;
    margin-left: 8px;
    letter-spacing: 0.02em;
}

/* ── Progress bar CF ── */
.cf-bar-container {
    background: #D5E5DF;
    border-radius: 8px;
    height: 10px;
    margin: 10px 0;
    overflow: hidden;
}
.cf-bar-fill {
    height: 100%;
    border-radius: 8px;
    transition: width 0.5s ease;
}

/* ── Kotak metrik ringkasan ── */
.metric-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: var(--shadow);
}
.metric-value {
    font-size: 2.3rem;
    font-weight: 700;
    color: var(--primary);
    line-height: 1.2;
}
.metric-label {
    font-size: 17px;
    color: var(--text-muted);
    margin-top: 5px;
    font-weight: 500;
}

/* ── Kotak langkah / step ── */
.step-box {
    background: var(--success-bg);
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    font-size: 18.5px;
    color: var(--success-fg);
    border: 1px solid #B6DDD2;
}

/* ── Kotak peringatan ── */
.warning-box {
    background: var(--warn-bg);
    border: 1px solid #D4801A;
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 19px;
    color: var(--warn-fg);
}
.danger-box {
    background: var(--danger-bg);
    border: 1px solid #C0392B;
    border-radius: var(--radius);
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 19px;
    color: var(--danger-fg);
}

/* ── Auto-save badge ── */
.autosave-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #E8F5F1;
    color: #0D5C4A;
    border: 1px solid #B6DDD2;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 17px;
    font-weight: 600;
    margin-top: 0.5rem;
}

/* ── Card alternatif ── */
.alt-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    box-shadow: 0 1px 6px rgba(13,92,74,0.06);
}

.hero-panel {
    background: linear-gradient(135deg, #123C3A 0%, #1F7A68 72%, #E7A93B 100%);
    color: #FFFFFF;
    border-radius: 8px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.3rem;
    box-shadow: var(--shadow);
}
.hero-panel h1,
.hero-panel h2,
.hero-panel h3,
.hero-panel p {
    color: #FFFFFF !important;
}
.hero-panel p {
    margin: 0.35rem 0 0;
    font-size: 19px;
    line-height: 1.65;
    max-width: 860px;
}
.quick-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 0.5rem 0 1.1rem;
}
.quick-card,
.report-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.1rem;
    box-shadow: var(--shadow);
}
.quick-label {
    color: var(--text-muted);
    font-size: 15.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.quick-value {
    color: var(--primary);
    font-size: 1.35rem;
    font-weight: 800;
    margin-top: 0.2rem;
}
.risk-box {
    border-radius: 8px;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(18,60,58,0.10);
    margin: 0.7rem 0 1rem;
}
.checklist {
    margin: 0;
    padding-left: 1.2rem;
    color: var(--text-mid);
    font-size: 18px;
    line-height: 1.75;
}
.tool-chip {
    display: inline-block;
    background: #EEF7F5;
    color: var(--primary);
    border: 1px solid #CFE4DF;
    border-radius: 999px;
    padding: 6px 12px;
    margin: 4px 6px 4px 0;
    font-size: 16px;
    font-weight: 700;
}
.feature-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
    margin-top: 1rem;
}
.feature-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.2rem;
    box-shadow: var(--shadow);
}
.feature-card strong {
    display: block;
    color: var(--primary);
    font-size: 1.05rem;
    margin-bottom: 0.25rem;
}
.feature-card span {
    color: var(--text-mid);
    font-size: 17px;
    line-height: 1.55;
}

@media (max-width: 900px) {
    .quick-grid,
    .feature-grid {
        grid-template-columns: 1fr;
    }
}

/* ── Metric bawaan Streamlit ── */
div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.9rem 1rem;
    box-shadow: var(--shadow);
}
div[data-testid="stMetric"] label {
    font-size: 17px !important;
    color: var(--text-muted) !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 2.0rem !important;
    color: var(--primary) !important;
    font-weight: 700 !important;
}

/* ── Tabel dataframe ── */
.stDataFrame { font-size: 18.5px !important; }

/* ── Tombol utama ── */
.stButton > button[kind="primary"] {
    background: var(--primary) !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 19.5px !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    transition: background 0.2s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-mid) !important;
}
.stButton > button {
    border-radius: 8px !important;
    font-size: 18.5px !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab"] {
    font-size: 18.5px !important;
    font-weight: 500 !important;
}

/* ── Garis pembatas ── */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── Panduan CF tabel ── */
.cf-table { width: 100%; border-collapse: collapse; font-size: 18.5px; margin-top: 0.5rem; }
.cf-table th { background: var(--primary); color: white; padding: 9px 14px; text-align: left; font-weight: 600; }
.cf-table td { padding: 8px 14px; border-bottom: 1px solid var(--border); }
.cf-table tr:last-child td { border-bottom: none; }
.cf-table tr:hover td { background: #F0F7F4; }

/* ── Info box biru bawaan ── */
div[data-testid="stInfo"] { font-size: 18.5px !important; }
div[data-testid="stAlert"] { font-size: 18.5px !important; }

/* ── Logo / header sidebar ── */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.5rem 0 1rem;
}
.sidebar-brand-icon { font-size: 2.4rem; }
.sidebar-brand-name {
    font-size: 1.45rem;
    font-weight: 700;
    color: white;
    line-height: 1.2;
}
.sidebar-brand-sub {
    font-size: 15px;
    color: rgba(255,255,255,0.65);
    font-weight: 400;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Sidebar navigasi
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div class="sidebar-brand">
  <span class="sidebar-brand-icon">👟</span>
  <div>
    <div class="sidebar-brand-name">SiPakar Sepatu</div>
    <div class="sidebar-brand-sub">Sistem Pakar Pencucian Sepatu</div>
  </div>
</div>
""", unsafe_allow_html=True)

    menu_options = ["🔍 Konsultasi"]
    if st.session_state.is_admin:
        menu_options.append("📚 Basis Pengetahuan")
        menu_options.append("📋 Riwayat")
    menu_options.append("ℹ️ Tentang Sistem")

    halaman = st.radio(
        "Menu",
        menu_options,
        label_visibility="collapsed",
    )
    st.markdown("---")

    # ─── Login / Logout admin ───
    if st.session_state.is_admin:
        st.markdown(
            '<div class="autosave-badge" style="background:rgba(255,255,255,0.15);'
            'color:white;border:1px solid rgba(255,255,255,0.3)">'
            '🔓 Masuk sebagai Admin</div>',
            unsafe_allow_html=True,
        )
        if st.button("Logout Admin", use_container_width=True):
            st.session_state.is_admin = False
            st.rerun()
    else:
        with st.expander("🔐 Login Admin"):
            with st.form("admin_login_form", clear_on_submit=False):
                pwd_input = st.text_input(
                    "Password", type="password", key="admin_pwd_input",
                    label_visibility="collapsed", placeholder="Masukkan password admin",
                )
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if pwd_input == ADMIN_PASSWORD:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.markdown(
                        '<div class="sidebar-error-box">⚠️ Password salah.</div>',
                        unsafe_allow_html=True,
                    )

    st.markdown("---")
    st.markdown(
        '<p style="font-size: 15px;color:rgba(255,255,255,0.5);line-height:1.6">'
        'Metode: Certainty Factor<br>Basis: 72 Aturan Pakar<br>Versi 1.0</p>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════
# HALAMAN 1 — KONSULTASI
# ═══════════════════════════════════════════════
if halaman == "🔍 Konsultasi":
    st.markdown("""
<div class="hero-panel">
  <h1 style="margin:0">Konsultasi Pencucian Sepatu</h1>
  <p>
    Pilih bahan, noda, dan tingkat keyakinan Anda. Sistem akan menghitung rekomendasi
    dengan Certainty Factor, lalu memberi checklist perawatan yang bisa langsung dipakai.
  </p>
</div>
""", unsafe_allow_html=True)

    # Ambil data dari DB
    bahan_list = get_semua_bahan()
    noda_list  = get_semua_noda()

    if not bahan_list or not noda_list:
        st.error(
            "❌ Tidak dapat memuat data dari database. "
            "Pastikan MySQL/XAMPP berjalan dan database `db_sepatu_cf` sudah diimport."
        )
        st.stop()

    st.markdown(f"""
<div class="quick-grid">
  <div class="quick-card">
    <div class="quick-label">Jenis bahan</div>
    <div class="quick-value">{len(bahan_list)} material</div>
  </div>
  <div class="quick-card">
    <div class="quick-label">Jenis noda</div>
    <div class="quick-value">{len(noda_list)} kategori</div>
  </div>
  <div class="quick-card">
    <div class="quick-label">Basis pakar</div>
    <div class="quick-value">72 aturan</div>
  </div>
</div>
""", unsafe_allow_html=True)

    col_form, col_info = st.columns([3, 2], gap="large")

    with col_form:
        st.subheader("Data Sepatu")

        nama_pengguna = st.text_input(
            "Nama Pengguna (opsional)",
            placeholder="Masukkan nama Anda...",
        )

        # Pilih bahan
        bahan_options = {b["nama_bahan"]: b["id_bahan"] for b in bahan_list}
        bahan_dipilih = st.selectbox(
            "Jenis Bahan Sepatu",
            list(bahan_options.keys()),
            help="Pilih material dominan sepatu Anda",
        )
        id_bahan = bahan_options[bahan_dipilih]

        bahan_desc = next((b["deskripsi"] for b in bahan_list if b["id_bahan"] == id_bahan), "")
        if bahan_desc:
            st.caption(f"ℹ️ {bahan_desc}")

        st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)

        # Mode noda
        mode_noda = st.radio(
            "Mode Noda",
            ["Satu jenis noda", "Lebih dari satu noda"],
            horizontal=True,
        )

        noda_options = {n["nama_noda"]: n["id_noda"] for n in noda_list}

        if mode_noda == "Satu jenis noda":
            noda_dipilih_list = [st.selectbox("Jenis Noda", list(noda_options.keys()))]
            id_noda_list = [noda_options[noda_dipilih_list[0]]]
        else:
            noda_multi = st.multiselect(
                "Pilih Jenis Noda (maks. 3)",
                list(noda_options.keys()),
                max_selections=3,
                help="Pilih semua noda yang ada pada sepatu",
            )
            noda_dipilih_list = noda_multi if noda_multi else []
            id_noda_list = [noda_options[n] for n in noda_dipilih_list]

        st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
        st.markdown("**Seberapa yakin Anda dengan jenis noda tersebut?**")
        cf_user = st.slider(
            "Tingkat Keyakinan Anda",
            min_value=0.1, max_value=1.0, value=0.8, step=0.1, format="%.1f",
            help="0.1 = Tidak yakin  ·  1.0 = Sangat yakin",
        )

        # Label keyakinan
        if cf_user >= 0.8:
            lbl, bg, fg = "Sangat Yakin",  "#E8F5F1", "#0D5C4A"
        elif cf_user >= 0.6:
            lbl, bg, fg = "Hampir Pasti",  "#EAF5F0", "#16613D"
        elif cf_user >= 0.4:
            lbl, bg, fg = "Cukup Yakin",   "#FDF4E7", "#8A5700"
        elif cf_user >= 0.2:
            lbl, bg, fg = "Sedikit Yakin", "#FCECEA", "#9B1C1C"
        else:
            lbl, bg, fg = "Tidak Yakin",   "#F2F2F2", "#4A4A4A"

        st.markdown(
            f'<span style="background:{bg};color:{fg};padding:5px 16px;'
            f'border-radius:20px;font-size: 17px;font-weight:600;'
            f'border:1px solid {fg}33">{lbl} ({cf_user})</span>',
            unsafe_allow_html=True,
        )

        st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)
        tombol = st.button("🔍 Dapatkan Rekomendasi", type="primary", use_container_width=True)

    with col_info:
        st.subheader("Panduan Nilai CF")
        st.markdown("""
<table class="cf-table">
  <thead><tr><th>Nilai CF</th><th>Keterangan</th></tr></thead>
  <tbody>
    <tr><td>0.8 – 1.0</td><td>Sangat yakin</td></tr>
    <tr><td>0.6 – 0.8</td><td>Hampir pasti</td></tr>
    <tr><td>0.4 – 0.6</td><td>Cukup yakin</td></tr>
    <tr><td>0.2 – 0.4</td><td>Sedikit yakin</td></tr>
    <tr><td>0.0 – 0.2</td><td>Tidak yakin</td></tr>
  </tbody>
</table>
""", unsafe_allow_html=True)

        st.markdown('<div style="margin-top:1.2rem"></div>', unsafe_allow_html=True)
        st.markdown("**Formula CF:**")
        st.code(
            "CF_rule  = CF_pakar × CF_user\n"
            "CF_comb  = CF1 + CF2 × (1 − CF1)",
            language="text",
        )
        st.caption("Sumber: Shortliffe & Buchanan (1975)")

    # ─── Proses inferensi ───
    if tombol:
        if not id_noda_list:
            st.warning("⚠️ Pilih minimal satu jenis noda.")
            st.stop()

        st.markdown("---")
        st.subheader("Hasil Rekomendasi")

        with st.spinner("Menghitung nilai Certainty Factor..."):
            if mode_noda == "Satu jenis noda":
                id_noda = id_noda_list[0]
                aturan  = get_aturan_by_bahan_noda(id_bahan, id_noda)
                if not aturan:
                    st.error("⚠️ Tidak ditemukan aturan untuk kombinasi bahan dan noda ini.")
                    st.stop()
                hasil_list = inferensi(aturan, cf_user)
            else:
                aturan_per_noda = [get_aturan_by_bahan_noda(id_bahan, nid) for nid in id_noda_list]
                aturan_per_noda = [a for a in aturan_per_noda if a]
                if not aturan_per_noda:
                    st.error("⚠️ Tidak ditemukan aturan untuk kombinasi yang dipilih.")
                    st.stop()
                hasil_list = inferensi_noda_ganda(aturan_per_noda, cf_user)

        if not hasil_list:
            st.warning("Tidak ada hasil yang dapat ditampilkan.")
            st.stop()

        top = hasil_list[0]
        butuh_profesional = perlu_profesional(hasil_list)

        # ─── AUTO-SAVE ke database ───
        save_key = hashlib.md5(
            f"{nama_pengguna}|{id_bahan}|{id_noda_list[0]}|{cf_user}|{top.id_metode}".encode()
        ).hexdigest()

        if save_key not in st.session_state.saved_keys:
            id_saved = simpan_konsultasi(
                nama_pengguna or "Anonim",
                id_bahan,
                id_noda_list[0],
                cf_user,
                top.id_metode,
                top.cf_final,
            )
            if id_saved:
                st.session_state.saved_keys.add(save_key)
                st.markdown(
                    f'<div class="autosave-badge">✅ Konsultasi otomatis tersimpan '
                    f'— ID Riwayat: <strong>#{id_saved}</strong></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="autosave-badge">✅ Konsultasi sudah tersimpan di riwayat</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div style="margin-top:1rem"></div>', unsafe_allow_html=True)

        # ─── Peringatan profesional ───
        if butuh_profesional:
            st.markdown("""
<div class="danger-box">
  ⚠️ <strong>Perhatian:</strong> Kombinasi bahan dan noda ini berisiko tinggi.
  Nilai keyakinan rendah menunjukkan kesulitan penanganan mandiri.
  <strong>Disarankan membawa ke jasa laundry sepatu profesional.</strong>
</div>
""", unsafe_allow_html=True)

        # ─── Card rekomendasi utama ───
        color_bar = (
            "#16A085" if top.cf_final >= 0.6
            else ("#D4801A" if top.cf_final >= 0.4 else "#C0392B")
        )
        st.markdown(f"""
<div class="hasil-card">
  <p style="margin:0 0 4px;font-size: 16px;font-weight:600;
            color:#7A9088;text-transform:uppercase;letter-spacing:0.06em">
    ✅ Rekomendasi Utama
  </p>
  <h2 style="margin:0 0 10px;font-size: 1.8rem;color:#0D5C4A">{top.nama_metode}</h2>
  <div class="cf-bar-container">
    <div class="cf-bar-fill" style="width:{top.persentase}%;background:{color_bar}"></div>
  </div>
  <p style="margin:6px 0 0;font-size: 19.5px">
    Tingkat Keyakinan:
    <strong style="font-size: 1.55rem;color:{color_bar}">{top.persentase}%</strong>
    <span class="badge" style="background:{top.warna}22;color:{color_bar};
          border:1px solid {color_bar}55">{top.label_keyakinan}</span>
  </p>
  <hr style="margin:12px 0;opacity:0.2">
  <p style="margin:0;font-size: 18px;color:#4A6157;line-height:1.6">
    📋 {top.deskripsi}
  </p>
  {'<p style="margin:10px 0 0;font-size: 16.5px;color:#D4801A">💡 ' + top.catatan + '</p>' if top.catatan else ''}
</div>
""", unsafe_allow_html=True)

        # ─── Detail perhitungan ───
        with st.expander("🧮 Lihat Detail Perhitungan CF"):
            st.markdown(ringkasan_perhitungan(top))
            if mode_noda != "Satu jenis noda":
                st.info("ℹ️ Penalti noda ganda diterapkan: −0.1 dari CF kombinasi")

        # ─── Alternatif ───
        if len(hasil_list) > 1:
            st.markdown("#### Metode Alternatif")
            cols = st.columns(min(len(hasil_list) - 1, 3))
            for i, h in enumerate(hasil_list[1:4]):
                cb = (
                    "#16A085" if h.cf_final >= 0.6
                    else ("#D4801A" if h.cf_final >= 0.4 else "#C0392B")
                )
                with cols[i % 3]:
                    st.markdown(f"""
<div class="alt-card">
  <strong style="font-size: 17px;color:#1E2D2A">{h.nama_metode}</strong>
  <div class="cf-bar-container" style="margin:8px 0">
    <div class="cf-bar-fill" style="width:{h.persentase}%;background:{cb}"></div>
  </div>
  <span style="font-size: 16.5px;color:#4A6157">{h.persentase}% — {h.label_keyakinan}</span>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════
        risk_profile = get_risk_profile(
            top.cf_final,
            bahan_dipilih,
            len(noda_dipilih_list),
        )
        care_steps = get_care_steps(
            top.nama_metode,
            bahan_dipilih,
            noda_dipilih_list,
            butuh_profesional,
        )
        tools = get_toolkit(top.nama_metode, bahan_dipilih)

        st.markdown("#### Panduan Perawatan")
        st.markdown(f"""
<div class="risk-box" style="background:{risk_profile['bg']};color:{risk_profile['color']}">
  <strong style="font-size:1.1rem">{risk_profile['label']}</strong><br>
  <span style="font-size:17px">{risk_profile['note']}</span>
</div>
""", unsafe_allow_html=True)

        col_steps, col_tools = st.columns([3, 2], gap="large")
        with col_steps:
            st.markdown("**Checklist langkah aman**")
            step_items = "".join(f"<li>{step}</li>" for step in care_steps)
            st.markdown(
                f'<div class="report-card"><ol class="checklist">{step_items}</ol></div>',
                unsafe_allow_html=True,
            )

        with col_tools:
            st.markdown("**Perlengkapan yang disarankan**")
            tool_items = "".join(f'<span class="tool-chip">{tool}</span>' for tool in tools)
            st.markdown(
                f'<div class="report-card">{tool_items}</div>',
                unsafe_allow_html=True,
            )

        report_text = build_report(
            nama_pengguna,
            bahan_dipilih,
            noda_dipilih_list,
            cf_user,
            top,
            risk_profile,
            care_steps,
            tools,
        )
        st.download_button(
            "Unduh Laporan Konsultasi (TXT)",
            data=report_text.encode("utf-8"),
            file_name="laporan_konsultasi_sepatu.txt",
            mime="text/plain",
            use_container_width=True,
        )


# HALAMAN 2 — BASIS PENGETAHUAN
# ═══════════════════════════════════════════════
elif halaman == "📚 Basis Pengetahuan":
    st.title("Basis Pengetahuan")
    st.markdown(
        '<p style="font-size: 19px;color:#4A6157;margin-top:-0.4rem">'
        'Seluruh aturan IF-THEN yang menjadi landasan sistem pakar ini, '
        'diperoleh dari wawancara langsung dengan pakar pencucian sepatu.</p>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🗂️ Tabel Aturan (72 Rule)", "📊 Visualisasi CF", "📖 Keterangan Metode"])

    with tab1:
        aturan_all = get_semua_aturan()
        if aturan_all:
            df = pd.DataFrame(aturan_all)
            df.columns = ["No", "Bahan", "Noda", "Metode", "CF Pakar", "Catatan"]
            df["No"] = range(1, len(df) + 1)

            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_bahan = st.selectbox("Filter Bahan", ["Semua"] + df["Bahan"].unique().tolist())
            with col_f2:
                filter_noda = st.selectbox("Filter Noda", ["Semua"] + df["Noda"].unique().tolist())
            with col_f3:
                filter_cf = st.selectbox(
                    "Filter CF",
                    ["Semua", "Tinggi (≥ 0.7)", "Sedang (0.5 – 0.69)", "Rendah (< 0.5)"],
                )

            df_filtered = df.copy()
            if filter_bahan != "Semua":
                df_filtered = df_filtered[df_filtered["Bahan"] == filter_bahan]
            if filter_noda != "Semua":
                df_filtered = df_filtered[df_filtered["Noda"] == filter_noda]
            if filter_cf == "Tinggi (≥ 0.7)":
                df_filtered = df_filtered[df_filtered["CF Pakar"] >= 0.7]
            elif filter_cf == "Sedang (0.5 – 0.69)":
                df_filtered = df_filtered[
                    (df_filtered["CF Pakar"] >= 0.5) & (df_filtered["CF Pakar"] < 0.7)
                ]
            elif filter_cf == "Rendah (< 0.5)":
                df_filtered = df_filtered[df_filtered["CF Pakar"] < 0.5]

            st.caption(f"Menampilkan {len(df_filtered)} dari {len(df)} aturan")
            st.dataframe(
                df_filtered[["No", "Bahan", "Noda", "Metode", "CF Pakar", "Catatan"]],
                use_container_width=True,
                hide_index=True,
            )

    with tab2:
        aturan_all = get_semua_aturan()
        if aturan_all:
            df = pd.DataFrame(aturan_all)
            df.columns = ["No", "Bahan", "Noda", "Metode", "CF", "Catatan"]
            df["CF"] = pd.to_numeric(df["CF"])

            st.markdown("#### Rata-rata CF per Jenis Bahan")
            avg_bahan = (
                df.groupby("Bahan")["CF"].mean()
                .sort_values(ascending=False)
                .reset_index()
            )
            avg_bahan.columns = ["Bahan", "Rata-rata CF"]
            st.bar_chart(avg_bahan.set_index("Bahan"))

            st.markdown("#### Rata-rata CF per Jenis Noda")
            avg_noda = (
                df.groupby("Noda")["CF"].mean()
                .sort_values(ascending=False)
                .reset_index()
            )
            avg_noda.columns = ["Noda", "Rata-rata CF"]
            st.bar_chart(avg_noda.set_index("Noda"))

    with tab3:
        metode_all = get_semua_metode()
        if metode_all:
            st.markdown("#### Daftar Metode Pencucian")
            for m in metode_all:
                with st.expander(f"**{m['id_metode']}. {m['nama_metode']}**"):
                    st.markdown(
                        f'<p style="font-size: 18.5px;color:#4A6157;line-height:1.7">'
                        f'{m["deskripsi"]}</p>',
                        unsafe_allow_html=True,
                    )


# ═══════════════════════════════════════════════
# HALAMAN 3 — RIWAYAT KONSULTASI
# ═══════════════════════════════════════════════
elif halaman == "📋 Riwayat":
    st.title("Riwayat Konsultasi")
    st.markdown(
        '<p style="font-size: 19px;color:#4A6157;margin-top:-0.4rem">'
        'Semua konsultasi tersimpan secara otomatis setelah rekomendasi diberikan.</p>',
        unsafe_allow_html=True,
    )

    stat = get_statistik()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Konsultasi", stat["total"])
    with c2:
        top_metode = stat["metode_populer"][0]["nama_metode"] if stat["metode_populer"] else "-"
        st.metric("Metode Terpopuler", top_metode)
    with c3:
        top_bahan = stat["bahan_terbanyak"][0]["nama_bahan"] if stat["bahan_terbanyak"] else "-"
        st.metric("Bahan Terbanyak", top_bahan)

    st.markdown("---")

    riwayat = get_riwayat_konsultasi(limit=100)
    if riwayat:
        df_r = pd.DataFrame(riwayat)
        df_r.columns = ["ID", "Nama", "Bahan", "Noda", "CF User", "Metode", "CF Akhir", "Tanggal"]

        filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
        with filter_col1:
            cari_nama = st.text_input(
                "Cari pengguna",
                placeholder="Ketik nama pengguna...",
                key="filter_riwayat_nama",
            )
        with filter_col2:
            filter_bahan_riwayat = st.selectbox(
                "Bahan",
                ["Semua"] + sorted(df_r["Bahan"].dropna().unique().tolist()),
                key="filter_riwayat_bahan",
            )
        with filter_col3:
            filter_metode_riwayat = st.selectbox(
                "Metode",
                ["Semua"] + sorted(df_r["Metode"].dropna().unique().tolist()),
                key="filter_riwayat_metode",
            )

        df_r_filtered = df_r.copy()
        if cari_nama:
            df_r_filtered = df_r_filtered[
                df_r_filtered["Nama"].fillna("").str.contains(cari_nama, case=False, regex=False)
            ]
        if filter_bahan_riwayat != "Semua":
            df_r_filtered = df_r_filtered[df_r_filtered["Bahan"] == filter_bahan_riwayat]
        if filter_metode_riwayat != "Semua":
            df_r_filtered = df_r_filtered[df_r_filtered["Metode"] == filter_metode_riwayat]

        st.caption(f"Menampilkan {len(df_r_filtered)} dari {len(df_r)} konsultasi")

        df_r = df_r_filtered
        df_r["CF Akhir (%)"] = (df_r["CF Akhir"] * 100).round(1).astype(str) + "%"
        df_r["Tanggal"] = pd.to_datetime(df_r["Tanggal"]).dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(
            df_r[["ID", "Nama", "Bahan", "Noda", "Metode", "CF Akhir (%)", "Tanggal"]],
            use_container_width=True,
            hide_index=True,
        )

        csv = df_r.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Unduh Riwayat (CSV)",
            data=csv,
            file_name="riwayat_konsultasi.csv",
            mime="text/csv",
        )
    else:
        st.info("Belum ada riwayat konsultasi. Lakukan konsultasi terlebih dahulu.")


# ═══════════════════════════════════════════════
# HALAMAN 4 — TENTANG SISTEM
# ═══════════════════════════════════════════════
elif halaman == "ℹ️ Tentang Sistem":
    st.title("Tentang Sistem")
    st.markdown("""
<div class="feature-grid">
  <div class="feature-card">
    <strong>Konsultasi multi-noda</strong>
    <span>Mendukung sampai tiga jenis noda sekaligus dengan penalti CF sesuai aturan pakar.</span>
  </div>
  <div class="feature-card">
    <strong>Analisis risiko perawatan</strong>
    <span>Menggabungkan nilai CF, bahan sensitif, dan jumlah noda menjadi level risiko yang mudah dipahami.</span>
  </div>
  <div class="feature-card">
    <strong>Checklist dan perlengkapan</strong>
    <span>Memberikan langkah perawatan serta daftar alat yang menyesuaikan metode rekomendasi.</span>
  </div>
  <div class="feature-card">
    <strong>Laporan dan riwayat</strong>
    <span>Hasil konsultasi dapat diunduh, sedangkan admin dapat mencari, memfilter, dan mengekspor riwayat.</span>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("""
### Deskripsi Sistem
Sistem pakar ini dirancang untuk membantu menentukan **metode pencucian sepatu yang tepat**
berdasarkan jenis bahan sepatu dan jenis noda yang menempel, menggunakan
metode **Certainty Factor (CF)** untuk merepresentasikan tingkat keyakinan pakar
terhadap setiap aturan.

### Ruang Lingkup
- **8 jenis bahan**: Kulit Asli, Kulit Sintetis, Kanvas, Suede,
  Mesh/Rajut, Rubber/Karet, Nubuck, Satin
- **9 jenis noda**: Minyak, Lumpur, Darah, Tinta, Jamur,
  Makanan/Minuman, Cat, Karat, Debu
- **12 metode pencucian**: dari cuci manual hingga pembersih enzimatik
- **72 aturan** yang diperoleh dari wawancara pakar

### Sumber Pengetahuan
Basis pengetahuan diperoleh dari wawancara langsung dengan pakar
perawatan dan pencucian sepatu, direpresentasikan menggunakan nilai CF (0.0–1.0).
""")

    with col2:
        st.markdown("""
### Metode: Certainty Factor

**Formula inti:**
```
CF_rule = CF_pakar × CF_user
```
- `CF_pakar` : keyakinan pakar (0.0–1.0) dari wawancara
- `CF_user`  : keyakinan pengguna terhadap gejala yang diamati

**Formula kombinasi (multiple rule):**
```
CF_comb = CF1 + CF2 × (1 − CF1)
```
Diterapkan berantai bila ada lebih dari satu aturan menuju hipotesis yang sama.

**Noda ganda:**
Penalti −0.1 diterapkan sesuai pernyataan pakar bahwa CF turun 0.1–0.2 untuk kasus noda ganda.

### Teknologi
| Komponen | Teknologi |
|---|---|
| Antarmuka | Python Streamlit |
| Database | MySQL (XAMPP) |
| Logika CF | Python (cf_engine.py) |
""")

    st.markdown("---")
    st.markdown("""
### Cara Instalasi

**1. Persiapkan database:**
```bash
# Buka phpMyAdmin: http://localhost/phpmyadmin
# Buat database: db_sepatu_cf
# Import file: database.sql
```

**2. Install dependensi Python:**
```bash
pip install streamlit mysql-connector-python pandas
```

**3. Jalankan aplikasi:**
```bash
streamlit run app.py
```

**4. Buka browser:** `http://localhost:8501`
""")
