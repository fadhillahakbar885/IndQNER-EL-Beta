# Laporan Audit & Integritas Dataset IndQNER 1.0 (Format BIO Per Ayat)

## 1. Ringkasan Eksekutif

Dataset **IndQNER 1.0** merupakan hasil revisi struktural terhadap dataset `indqner_revised` di mana:
- **1 Teks = 1 Ayat Al-Qur'an Utuh** (merujuk pada definisi ayat pada korpus IndQEL).
- **Pemisah Baris Kosong (`\n`)**: HANYA memisahkan antar satu teks ayat dengan teks ayat berikutnya.
- **Penyatuan Kalimat**: Kalimat-kalimat yang berada di dalam ayat yang sama disatukan secara sekuensial tanpa baris kosong pemisah.
- **Zero Deletion & Zero Corruption Guarantee**: Mempertahankan **100% token kata** dan **100% label BIO** tanpa kehilangan satu kata atau satu entitas pun.

---

## 2. Perbandingan Kuantitatif Struktur Berkas

| Split Dataset | Metrik | IndQNER Revised (Lama) | IndQNER 1.0 (Baru) | Perubahan Struktural | Status Preservasi |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`train.txt`** | **Jumlah Teks / Sampel** | 2,495 kalimat | **1,050 ayat (teks)** | -1,445 batas kalimat internal | Rekonstruksi Ayat Sempurna |
| | **Total Token Kata** | 49,076 token | **49,076 token** | 0 token berubah/hilang | **100.00% Identik** |
| | **Distribusi Tag BIO** | 27 kelas tag | **27 kelas tag** | Identik 100% | **Lolos Validasi** |
| **`dev.txt`** | **Jumlah Teks / Sampel** | 312 kalimat | **161 ayat (teks)** | -151 batas kalimat internal | Rekonstruksi Ayat Sempurna |
| | **Total Token Kata** | 6,895 token | **6,895 token** | 0 token berubah/hilang | **100.00% Identik** |
| | **Distribusi Tag BIO** | 18 kelas tag | **18 kelas tag** | Identik 100% | **Lolos Validasi** |
| **`test.txt`** | **Jumlah Teks / Sampel** | 311 kalimat | **176 ayat (teks)** | -135 batas kalimat internal | Rekonstruksi Ayat Sempurna |
| | **Total Token Kata** | 6,056 token | **6,056 token** | 0 token berubah/hilang | **100.00% Identik** |
| | **Distribusi Tag BIO** | 20 kelas tag | **20 kelas tag** | Identik 100% | **Lolos Validasi** |

---

## 3. Rincian Distribusi Label Entitas (Zero Corruption Verification)

Berikut adalah bukti matematis bahwa frekuensi seluruh entitas Qurani di `train.txt`, `dev.txt`, dan `test.txt` identik 100%:

| Kelas Tag BIO | Train Revised | Train 1.0 | Dev Revised | Dev 1.0 | Test Revised | Test 1.0 | Selisih |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `B-AfterlifeLocation` | 16 | 16 | 2 | 2 | 2 | 2 | **0 (Identik)** |
| `B-Allah` | 1,146 | 1,146 | 82 | 82 | 136 | 136 | **0 (Identik)** |
| `B-Angel` | 13 | 13 | 0 | 0 | 2 | 2 | **0 (Identik)** |
| `B-Artifact` | 20 | 20 | 0 | 0 | 0 | 0 | **0 (Identik)** |
| `B-AstronomicalBody` | 155 | 155 | 23 | 23 | 20 | 20 | **0 (Identik)** |
| `B-Color` | 5 | 5 | 1 | 1 | 1 | 1 | **0 (Identik)** |
| `B-Event` | 84 | 84 | 7 | 7 | 7 | 7 | **0 (Identik)** |
| `B-Food` | 2 | 2 | 2 | 2 | 0 | 0 | **0 (Identik)** |
| `B-GeographicalLocation` | 23 | 23 | 3 | 3 | 3 | 3 | **0 (Identik)** |
| `B-HolyBook` | 106 | 106 | 22 | 22 | 10 | 10 | **0 (Identik)** |
| `B-Language` | 1 | 1 | 0 | 0 | 1 | 1 | **0 (Identik)** |
| `B-Messenger` | 307 | 307 | 61 | 61 | 37 | 37 | **0 (Identik)** |
| `B-Person` | 155 | 155 | 22 | 22 | 13 | 13 | **0 (Identik)** |
| `B-Prophet` | 48 | 48 | 5 | 5 | 3 | 3 | **0 (Identik)** |
| `B-Religion` | 13 | 13 | 0 | 0 | 2 | 2 | **0 (Identik)** |
| `B-Throne` | 1 | 1 | 1 | 1 | 0 | 0 | **0 (Identik)** |
| `I-AfterlifeLocation` | 1 | 1 | 1 | 1 | 0 | 0 | **0 (Identik)** |
| `I-Allah` | 144 | 144 | 7 | 7 | 13 | 13 | **0 (Identik)** |
| `I-Artifact` | 2 | 2 | 0 | 0 | 0 | 0 | **0 (Identik)** |
| `I-Color` | 1 | 1 | 0 | 0 | 0 | 0 | **0 (Identik)** |
| `I-Event` | 56 | 56 | 4 | 4 | 6 | 6 | **0 (Identik)** |
| `I-GeographicalLocation` | 3 | 3 | 1 | 1 | 1 | 1 | **0 (Identik)** |
| `I-Language` | 1 | 1 | 0 | 0 | 1 | 1 | **0 (Identik)** |
| `I-Messenger` | 29 | 29 | 0 | 0 | 0 | 0 | **0 (Identik)** |
| `I-Person` | 73 | 73 | 11 | 11 | 5 | 5 | **0 (Identik)** |
| `I-Religion` | 5 | 5 | 0 | 0 | 1 | 1 | **0 (Identik)** |
| `O` | 46,666 | 46,666 | 6,640 | 6,640 | 5,792 | 5,792 | **0 (Identik)** |

---

## 4. Kesimpulan Audit

- **Status Verifikasi:** PASSED (SUKSES 100%)
- **Preservasi Kata & Label:** 100.00% Zero-Deletion Guarantee terpenuhi.
- **Standar Segmentasi:** Sesuai definisi korpus Qurani, 1 Teks = 1 Ayat Al-Qur'an, siap dipakai untuk evaluasi dan publikasi skripsi.
