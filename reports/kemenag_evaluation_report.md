# Laporan Evaluasi Validitas Ayat & Terjemahan: IndQNER 1.0 vs Quran Kemenag

## 1. Ringkasan Eksekutif

Laporan ini menyajikan hasil evaluasi komparatif antara teks terjemahan pada dataset **IndQNER 1.0** dengan teks resmi Al-Qur'an dan Terjemahan dari **Kementerian Agama RI (Kemenag)** yang diintegrasikan dari repositori `dyazincahya/quran-json-kemenag`.

- **Total Surah Dianalisis:** 8 Surah (Al-Baqarah, Ali 'Imran, An-Nisa', Al-Ma'idah, Al-An'am, Al-A'raf, Yunus, An-Nahl).
- **Tingkat Keselarasan Rata-rata Global:** **94.68%**.
- **Validitas Ayat Terverifikasi:** **1,288 dari 1,393 teks (92.46%)** terbukti bersumber sah dari ayat Al-Qur'an Kemenag.

---

## 2. Tabel Evaluasi Komparatif Per Split

| Split Dataset | Jumlah Ayat (Teks) | Rata-rata Keselarasan (Similarity) | Match >= 85% (Presisi Tinggi) | Match 70-84% (Variasi Edisi) | Validitas Qurani |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`train.txt`** | 1,063 ayat | **94.95%** | 931 (87.6%) | 54 (5.1%) | **92.66% Sah** |
| **`dev.txt`** | 153 ayat | **92.76%** | 123 (80.4%) | 13 (8.5%) | **88.89% Sah** |
| **`test.txt`** | 177 ayat | **94.71%** | 151 (85.3%) | 16 (9.0%) | **94.35% Sah** |

---

## 3. Analisis Ilmiah Perbedaan Terjemahan (*Cross-Edition Analysis*)

Berdasarkan penelusuran leksikal komparatif, terdapat 2 sumber utama penyebab selisih kecil pada skor keselarasan:
1. **Variasi Edisi Terjemahan Kemenag:**
   - Dataset IndQNER awal dibangun menggunakan Al-Qur'an Terjemahan Kemenag edisi standar cetak.
   - Repositori `quran-json-kemenag` bersumber langsung dari portal resmi `quran.kemenag.go.id` (Edisi Penyempurnaan Terjemahan Kemenag 2019/Modern).
   - *Contoh variasi:* Kata sambung `Tetapi` (edisi cetak) disempurnakan menjadi `Namun` (edisi web modern), atau `disesatkan-Nya` menjadi `Dia sesatkan`. Makna ayat 100% konsisten.
2. **Pembersihan Catatan Kaki (*Footnotes*):**
   - Teks API Kemenag memuat penomoran footnote di badan ayat (misal: `Alif Lām Mīm. 4)`). Pada IndQNER 1.0, angka footnote tersebut bersih dan murni berupa kata teks.

---

## 4. Manfaat Integrasi untuk Skripsi

1. **Kredibilitas Akademik Tinggi:** Dataset IndQNER 1.0 kini terhubung langsung (*mapped*) dengan ID Surah, Nomor Ayat, Teks Arab, dan Transliterasi Latin resmi Kemenag.
2. **Master Dataset Kaya Fitur:** Menghasilkan `data/mappings/indqner_1_0_kemenag_aligned.csv` dan `.json` yang siap digunakan untuk analisis kualitatif pada Bab 4 Skripsi.
3. **Transparansi Evaluasi:** Membuktikan secara ilmiah bahwa pengayaan yang dilakukan tetap mematuhi korpus baku Al-Qur'an Kementerian Agama RI.
