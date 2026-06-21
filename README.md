# 👟 Sistem Pakar Pencucian Sepatu
### Metode Certainty Factor (CF)

---

## 📁 Struktur File

```
sistem_pakar_sepatu/
├── app.py          → Antarmuka Streamlit (jalankan ini)
├── database.py     → Koneksi & query MySQL
├── cf_engine.py    → Logika perhitungan Certainty Factor
├── database.sql    → Schema + data 72 rule (import ke MySQL)
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalasi

### Langkah 1 — Siapkan Database MySQL (XAMPP)

1. Buka **XAMPP Control Panel**, nyalakan **Apache** dan **MySQL**
2. Buka browser → `http://localhost/phpmyadmin`
3. Klik **New** → buat database bernama `db_sepatu_cf`
4. Pilih database `db_sepatu_cf` → klik tab **Import**
5. Pilih file `database.sql` → klik **Go**

### Langkah 2 — Install Python & Dependensi

```bash
# Pastikan Python 3.9+ terinstall
python --version

# Install library
pip install -r requirements.txt
```

### Langkah 3 — Jalankan Aplikasi

```bash
# Di folder sistem_pakar_sepatu/
streamlit run app.py
```

Buka browser: **http://localhost:8501**

---

## 🔧 Konfigurasi Database

Edit bagian `DB_CONFIG` di file `database.py` jika perlu:

```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",       # Isi jika MySQL Anda punya password
    "database": "db_sepatu_cf",
}
```

---

## 📊 Fitur Aplikasi

| Halaman | Fitur |
|---------|-------|
| 🔍 Konsultasi | Input bahan + noda, hitung CF, tampilkan rekomendasi |
| 📚 Basis Pengetahuan | Lihat & filter 72 rule, grafik CF |
| 📋 Riwayat | Histori konsultasi, ekspor CSV |
| ℹ️ Tentang | Penjelasan metode & formula |

---

## 🧮 Rumus Certainty Factor

```
CF_rule   = CF_pakar × CF_user
CF_comb   = CF1 + CF2 × (1 − CF1)   [keduanya positif]
```

**Interpretasi CF:**
- 0.8 – 1.0 : Sangat Yakin
- 0.6 – 0.8 : Hampir Pasti
- 0.4 – 0.6 : Cukup Yakin
- 0.2 – 0.4 : Sedikit Yakin
- 0.0 – 0.2 : Tidak Yakin

---

## 📋 Basis Pengetahuan

- **8 bahan**: Kulit Asli, Kulit Sintetis, Kanvas, Suede, Mesh/Rajut, Rubber/Karet, Nubuck, Satin
- **9 noda**: Minyak, Lumpur, Darah, Tinta, Jamur, Makanan, Cat, Karat, Debu
- **12 metode**: Cuci Manual, Deep Clean, Dry Clean, Rendam, Spot Cleaning, Sikat Kering, Lap Lembab, Steam, Pembersih Suede, Pembersih Kimia, Enzimatik, Mesin Gentle
- **72 aturan** dari wawancara pakar

---

## 🔬 Teknologi

- **Backend** : Python 3.9+
- **UI** : Streamlit
- **Database** : MySQL via XAMPP
- **Library** : mysql-connector-python, pandas
