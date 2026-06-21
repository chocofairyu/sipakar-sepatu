"""
database.py
Modul koneksi dan operasi database MySQL
Sistem Pakar Pencucian Sepatu - Certainty Factor
"""

import mysql.connector
from mysql.connector import Error
import streamlit as st


# ─────────────────────────────────────────────
# Konfigurasi koneksi (sesuaikan jika berbeda)
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     st.secrets["mysql"]["host"],
    "port":     int(st.secrets["mysql"]["port"]),
    "user":     st.secrets["mysql"]["user"],
    "password": st.secrets["mysql"]["password"],
    "database": st.secrets["mysql"]["database"],
    "charset":  "utf8mb4",
    "ssl_disabled": False,
}


@st.cache_resource(show_spinner=False)
def get_connection():
    """Buat koneksi ke MySQL. Di-cache agar tidak reconnect setiap request."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"❌ Gagal terhubung ke database: {e}")
        return None


def fetch_all(query: str, params: tuple = ()):
    """Jalankan SELECT dan kembalikan list of dict."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        if not conn.is_connected():
            conn.reconnect()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    except Error as e:
        st.error(f"❌ Query error: {e}")
        return []
    finally:
        cursor.close()


def execute_query(query: str, params: tuple = ()):
    """Jalankan INSERT / UPDATE / DELETE. Kembalikan lastrowid."""
    conn = get_connection()
    if conn is None:
        return None
    try:
        if not conn.is_connected():
            conn.reconnect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except Error as e:
        st.error(f"❌ Execute error: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()


# ─────────────────────────────────────────────
# Fungsi-fungsi data akses
# ─────────────────────────────────────────────

def get_semua_bahan():
    """Ambil semua jenis bahan sepatu."""
    return fetch_all("SELECT id_bahan, nama_bahan, deskripsi FROM tb_bahan ORDER BY id_bahan")


def get_semua_noda():
    """Ambil semua jenis noda."""
    return fetch_all("SELECT id_noda, nama_noda, deskripsi FROM tb_noda ORDER BY id_noda")


def get_semua_metode():
    """Ambil semua metode pencucian."""
    return fetch_all("SELECT id_metode, nama_metode, deskripsi FROM tb_metode ORDER BY id_metode")


def get_aturan_by_bahan_noda(id_bahan: int, id_noda: int):
    """
    Ambil semua aturan yang cocok dengan bahan dan noda tertentu.
    Satu kombinasi bahan+noda → satu rule (sesuai basis pengetahuan).
    """
    query = """
        SELECT
            a.id_aturan,
            a.cf_pakar,
            a.catatan,
            m.id_metode,
            m.nama_metode,
            m.deskripsi AS deskripsi_metode
        FROM tb_aturan a
        JOIN tb_metode m ON a.id_metode = m.id_metode
        WHERE a.id_bahan = %s AND a.id_noda = %s
        ORDER BY a.cf_pakar DESC
    """
    return fetch_all(query, (id_bahan, id_noda))


def get_semua_aturan():
    """Ambil seluruh basis pengetahuan (untuk halaman admin)."""
    query = """
        SELECT
            a.id_aturan,
            b.nama_bahan,
            n.nama_noda,
            m.nama_metode,
            a.cf_pakar,
            a.catatan
        FROM tb_aturan a
        JOIN tb_bahan  b ON a.id_bahan  = b.id_bahan
        JOIN tb_noda   n ON a.id_noda   = n.id_noda
        JOIN tb_metode m ON a.id_metode = m.id_metode
        ORDER BY b.nama_bahan, n.nama_noda
    """
    return fetch_all(query)


def simpan_konsultasi(nama_pengguna: str, id_bahan: int, id_noda: int,
                      cf_user: float, id_metode: int, cf_akhir: float):
    """Simpan hasil konsultasi ke tabel riwayat."""
    query = """
        INSERT INTO tb_konsultasi
            (nama_pengguna, id_bahan, id_noda, cf_user, id_metode_hasil, cf_akhir)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    return execute_query(query, (nama_pengguna, id_bahan, id_noda, cf_user, id_metode, cf_akhir))


def get_riwayat_konsultasi(limit: int = 50):
    """Ambil riwayat konsultasi terbaru."""
    query = """
        SELECT
            k.id_konsultasi,
            k.nama_pengguna,
            b.nama_bahan,
            n.nama_noda,
            k.cf_user,
            m.nama_metode,
            k.cf_akhir,
            k.tanggal
        FROM tb_konsultasi k
        JOIN tb_bahan  b ON k.id_bahan        = b.id_bahan
        JOIN tb_noda   n ON k.id_noda          = n.id_noda
        JOIN tb_metode m ON k.id_metode_hasil  = m.id_metode
        ORDER BY k.tanggal DESC
        LIMIT %s
    """
    return fetch_all(query, (limit,))


def get_statistik():
    """Ambil statistik ringkasan untuk dashboard."""
    total_konsultasi = fetch_all("SELECT COUNT(*) AS total FROM tb_konsultasi")
    metode_terpopuler = fetch_all("""
        SELECT m.nama_metode, COUNT(*) AS jumlah
        FROM tb_konsultasi k
        JOIN tb_metode m ON k.id_metode_hasil = m.id_metode
        GROUP BY k.id_metode_hasil
        ORDER BY jumlah DESC
        LIMIT 5
    """)
    bahan_terbanyak = fetch_all("""
        SELECT b.nama_bahan, COUNT(*) AS jumlah
        FROM tb_konsultasi k
        JOIN tb_bahan b ON k.id_bahan = b.id_bahan
        GROUP BY k.id_bahan
        ORDER BY jumlah DESC
        LIMIT 5
    """)
    return {
        "total": total_konsultasi[0]["total"] if total_konsultasi else 0,
        "metode_populer": metode_terpopuler,
        "bahan_terbanyak": bahan_terbanyak,
    }
