"""
cf_engine.py
Mesin inferensi Certainty Factor (CF)
Sistem Pakar Pencucian Sepatu

Referensi formula:
  CF_rule    = CF_pakar × CF_user
  CF_combine = CF1 + CF2 × (1 − CF1)   [keduanya positif]
  CF_combine = CF1 + CF2 × (1 + CF1)   [keduanya negatif]
  CF_combine = (CF1 + CF2) / (1 − min(|CF1|, |CF2|))  [berbeda tanda]
"""

from dataclasses import dataclass
from typing import List


# ─────────────────────────────────────────────
# Struktur data
# ─────────────────────────────────────────────

@dataclass
class HasilCF:
    id_metode:       int
    nama_metode:     str
    deskripsi:       str
    cf_pakar:        float
    cf_user:         float
    cf_rule:         float
    cf_final:        float          # setelah kombinasi bila ada rule ganda
    catatan:         str
    persentase:      float          # cf_final × 100
    label_keyakinan: str
    warna:           str            # untuk UI badge


# ─────────────────────────────────────────────
# Fungsi inti CF
# ─────────────────────────────────────────────

def hitung_cf_rule(cf_pakar: float, cf_user: float) -> float:
    """
    Menggabungkan keyakinan pakar dengan keyakinan pengguna.
    CF_rule = CF_pakar × CF_user
    """
    return round(cf_pakar * cf_user, 4)


def kombinasi_cf(cf1: float, cf2: float) -> float:
    """
    Menggabungkan dua nilai CF dari dua rule berbeda menuju hipotesis sama.
    Menggunakan formula kombinasi standar:
      - Keduanya positif : CF1 + CF2 × (1 − CF1)
      - Keduanya negatif : CF1 + CF2 × (1 + CF1)
      - Berbeda tanda    : (CF1 + CF2) / (1 − min(|CF1|, |CF2|))
    """
    if cf1 >= 0 and cf2 >= 0:
        return round(cf1 + cf2 * (1 - cf1), 4)
    elif cf1 < 0 and cf2 < 0:
        return round(cf1 + cf2 * (1 + cf1), 4)
    else:
        denom = 1 - min(abs(cf1), abs(cf2))
        if denom == 0:
            return 0.0
        return round((cf1 + cf2) / denom, 4)


def kombinasi_cf_list(cf_list: List[float]) -> float:
    """
    Mengkombinasikan CF dari beberapa rule secara berantai.
    Iterasi: CF_combined = kombinasi(CF_combined, CF_berikutnya)
    """
    if not cf_list:
        return 0.0
    result = cf_list[0]
    for cf in cf_list[1:]:
        result = kombinasi_cf(result, cf)
    return result


# ─────────────────────────────────────────────
# Label dan warna interpretasi
# ─────────────────────────────────────────────

def get_label_keyakinan(cf: float) -> tuple[str, str]:
    """
    Mengembalikan (label_teks, warna_hex) berdasarkan nilai CF akhir.
    """
    pct = cf * 100
    if pct >= 80:
        return "Sangat Yakin",  "#27500A"
    elif pct >= 60:
        return "Hampir Pasti",  "#085041"
    elif pct >= 40:
        return "Cukup Yakin",   "#633806"
    elif pct >= 20:
        return "Sedikit Yakin", "#791F1F"
    else:
        return "Tidak Yakin",   "#444441"


def get_warna_badge(cf: float) -> str:
    """Kembalikan warna latar badge berdasarkan CF."""
    pct = cf * 100
    if pct >= 80:
        return "#EAF3DE"
    elif pct >= 60:
        return "#E1F5EE"
    elif pct >= 40:
        return "#FAEEDA"
    elif pct >= 20:
        return "#FCEBEB"
    else:
        return "#F1EFE8"


# ─────────────────────────────────────────────
# Fungsi utama inferensi
# ─────────────────────────────────────────────

def inferensi(aturan_list: list, cf_user: float) -> List[HasilCF]:
    """
    Jalankan inferensi CF untuk satu kombinasi bahan+noda.

    Parameter:
        aturan_list : list of dict dari get_aturan_by_bahan_noda()
                      Setiap dict berisi: id_metode, nama_metode,
                      deskripsi_metode, cf_pakar, catatan
        cf_user     : float (0.0–1.0) keyakinan pengguna terhadap noda

    Mengembalikan:
        List[HasilCF] diurutkan dari CF tertinggi ke terendah.

    Catatan:
        Dalam basis pengetahuan ini setiap bahan+noda hanya memiliki
        1 rule (1 metode). Namun fungsi ini tetap mendukung multi-rule
        via kombinasi CF berantai untuk skalabilitas.
    """
    if not aturan_list:
        return []

    # Kelompokkan rule per metode (antisipasi multi-rule satu metode)
    per_metode: dict[int, dict] = {}
    for r in aturan_list:
        mid = r["id_metode"]
        if mid not in per_metode:
            per_metode[mid] = {
                "id_metode":   mid,
                "nama_metode": r["nama_metode"],
                "deskripsi":   r["deskripsi_metode"],
                "cf_pakar":    r["cf_pakar"],
                "catatan":     r.get("catatan", ""),
                "cf_rules":    [],
            }
        cf_r = hitung_cf_rule(float(r["cf_pakar"]), cf_user)
        per_metode[mid]["cf_rules"].append(cf_r)

    hasil = []
    for mid, data in per_metode.items():
        cf_final = kombinasi_cf_list(data["cf_rules"])
        cf_final = max(0.0, min(1.0, cf_final))   # clamp [0,1]

        label, warna_teks = get_label_keyakinan(cf_final)
        warna_bg          = get_warna_badge(cf_final)

        hasil.append(HasilCF(
            id_metode       = mid,
            nama_metode     = data["nama_metode"],
            deskripsi       = data["deskripsi"],
            cf_pakar        = float(data["cf_pakar"]),
            cf_user         = cf_user,
            cf_rule         = data["cf_rules"][0] if len(data["cf_rules"]) == 1 else kombinasi_cf_list(data["cf_rules"]),
            cf_final        = cf_final,
            catatan         = data["catatan"],
            persentase      = round(cf_final * 100, 1),
            label_keyakinan = label,
            warna           = warna_bg,
        ))

    # Urutkan CF tertinggi ke terendah
    hasil.sort(key=lambda x: x.cf_final, reverse=True)
    return hasil


def inferensi_noda_ganda(aturan_per_noda: List[list],
                          cf_user: float,
                          penalti: float = 0.1) -> List[HasilCF]:
    """
    Inferensi untuk kasus lebih dari satu noda sekaligus.

    Sesuai pernyataan pakar: CF turun 0.1–0.2 poin untuk noda ganda.
    Strategi: ambil CF per-metode dari tiap noda, kombinasikan, lalu
    terapkan penalti.

    Parameter:
        aturan_per_noda : list of aturan_list (satu list per noda)
        cf_user         : keyakinan pengguna
        penalti         : pengurangan CF untuk noda ganda (default 0.1)
    """
    # Kumpulkan CF per metode dari semua noda
    per_metode: dict[int, dict] = {}

    for aturan_list in aturan_per_noda:
        sub_hasil = inferensi(aturan_list, cf_user)
        for h in sub_hasil:
            if h.id_metode not in per_metode:
                per_metode[h.id_metode] = {
                    "nama_metode": h.nama_metode,
                    "deskripsi":   h.deskripsi,
                    "cf_pakar":    h.cf_pakar,
                    "catatan":     h.catatan,
                    "cf_list":     [],
                }
            per_metode[h.id_metode]["cf_list"].append(h.cf_rule)

    hasil = []
    for mid, data in per_metode.items():
        cf_combined = kombinasi_cf_list(data["cf_list"])
        # Terapkan penalti noda ganda
        cf_final = max(0.0, cf_combined - penalti)
        cf_final = round(cf_final, 4)

        label, _ = get_label_keyakinan(cf_final)
        warna_bg = get_warna_badge(cf_final)

        hasil.append(HasilCF(
            id_metode       = mid,
            nama_metode     = data["nama_metode"],
            deskripsi       = data["deskripsi"],
            cf_pakar        = data["cf_pakar"],
            cf_user         = cf_user,
            cf_rule         = cf_combined,
            cf_final        = cf_final,
            catatan         = data["catatan"],
            persentase      = round(cf_final * 100, 1),
            label_keyakinan = label,
            warna           = warna_bg,
        ))

    hasil.sort(key=lambda x: x.cf_final, reverse=True)
    return hasil


# ─────────────────────────────────────────────
# Utilitas
# ─────────────────────────────────────────────

def perlu_profesional(hasil_list: List[HasilCF]) -> bool:
    """
    True jika rekomendasi utama adalah Dry Clean (id=3) dengan CF rendah,
    atau CF tertinggi < 0.4 — tanda sepatu perlu ditangani profesional.
    """
    if not hasil_list:
        return False
    top = hasil_list[0]
    return top.cf_final < 0.4 or "Dry Clean" in top.nama_metode


def ringkasan_perhitungan(hasil: HasilCF) -> str:
    """
    Teks penjelasan langkah perhitungan CF untuk tampilan di UI.
    """
    lines = [
        "**Langkah Perhitungan CF:**",
        f"1. CF Pakar (dari wawancara)  = **{hasil.cf_pakar}**",
        f"2. CF User (keyakinan Anda)   = **{hasil.cf_user}**",
        f"3. CF Rule = CF Pakar × CF User = {hasil.cf_pakar} × {hasil.cf_user} = **{hasil.cf_rule}**",
        f"4. CF Final (setelah kombinasi) = **{hasil.cf_final}** ({hasil.persentase}%)",
        f"5. Interpretasi: **{hasil.label_keyakinan}**",
    ]
    return "\n".join(lines)
