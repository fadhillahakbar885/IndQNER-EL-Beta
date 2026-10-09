# Rencana Detail Proyek: Revisi dan Pengayaan Dataset IndQNER Berbasis Mention IndQEL

**Dokumen Rencana Kerja Skripsi / Proyek Riset NLP**  
**Fokus:** Data Engineering, Entity Linking Alignment, dan Named Entity Recognition Enrichment  
**Prinsip Utama:** *Strict Zero Deletion Policy* (Preservasi 100% label asli IndQNER)

---

## 1. Ringkasan Eksekutif & Latar Belakang

Penelitian ini bertujuan untuk merevisi dan memperkaya dataset **IndQNER** (*Indonesian Quranic Named Entity Recognition*) dengan memanfaatkan informasi *mention* dan entitas dari dataset **IndQEL** (*Indonesian Quranic Entity Linking*). 

Kedua dataset dibangun menggunakan korpus yang sama, yaitu **Terjemahan Al-Qur'an Bahasa Indonesia (Kementerian Agama RI)**. Namun, dataset IndQNER yang dianotasi secara manual memiliki potensi *missing entities* (*False Negatives*). Melalui proyek ini:
1. Mention dari IndQEL dipetakan ke dalam **20 kelas konsep Qurani** sesuai *Annotation Guideline IndQNER*.
2. Seluruh file IndQEL (`train_per_mention.tsv`, `val_per_mention.tsv`, `test_per_mention.tsv`) diperkaya dengan kolom baru: `label`.
3. Split **`train`** pada IndQNER diperkaya secara terarah menggunakan *span alignment* tanpa mengubah atau menghapus satu pun label yang sudah ada di IndQNER aslinya.

---

## 2. Analisis & Statistik Dataset Awal

| Karakteristik | Dataset IndQNER | Dataset IndQEL |
| :--- | :--- | :--- |
| **Format File** | CoNLL / BIO Tagging (`token \t tag`) | Tabular TSV (`surah_id \t ayah \t sentence \t mention \t uri`) |
| **Kelas / Entitas** | 16–20 Kelas Konsep Quran (misal: *Allah*, *Prophet*, *HolyBook*, *GeographicalLocation*) | Wikidata URI (misal: `Q2095353`, `Q9458`, `Q428`) |
| **Split Berkas** | `train.txt`, `dev.txt`, `test.txt` | `train_per_mention.tsv`, `val_per_mention.tsv`, `test_per_mention.tsv` |
| **Cakupan Baris IndQEL** | - | `train`: 2.324 baris<br>`val`: 293 baris<br>`test`: 269 baris |
| **Karakteristik Unik IndQEL** | - | **Hanya terdapat 140 pasangan unik `(mention, uri)`** di seluruh ketiga file! |

> **Implikasi Metodologis:** Karena hanya ada 140 pasangan unik `(mention, uri)`, proses pemetaan ke 20 kelas IndQNER dapat dilakukan secara transparan, deterministik, dan dapat diaudit secara manual 100% untuk kebutuhan laporan skripsi.

---

## 3. Pipeline Proyek Step-by-Step

```
[datasets IndQEL]
   ├── train_per_mention.tsv
   ├── val_per_mention.tsv
   └── test_per_mention.tsv
            │
            ▼
[Tahap 1: Ekstraksi 140 Pasangan Unik]
   └──> Menghasilkan file kandidat pemetaan
            │
            ▼
[Tahap 2: Pemetaan ke 20 Kelas IndQNER]
   └──> Master file: data/mappings/indqel_to_indqner_mapping.csv
            │
            ▼
[Tahap 3: Update 3 File IndQEL]
   └──> Menambahkan kolom "label" pada:
        - train_per_mention.tsv
        - val_per_mention.tsv
        - test_per_mention.tsv
            │
            ▼
[Tahap 4: Token Span Alignment & Enrichment (Split Train)]
   └──> Mencocokkan mention IndQEL ke token IndQNER train.txt
   └──> Menerapkan Strict Preservation Policy (0 label hilang)
            │
            ▼
[Tahap 5: Zero-Deletion Audit & Verification]
   └──> Pembuktian matematis: Label lama = 100% utuh, label baru bertambah
   └──> Output final: data/indqner_revised/train.txt
```

### Tahap 1: Ekstraksi Pasangan Unik `(mention, uri)`
* Menelusuri ketiga file `*_per_mention.tsv` di folder `datasets IndQEL`.
* Mengumpulkan semua kombinasi unik `(mention, uri)` dan frekuensi kemunculannya.
* Menangani baris kosong (*null mention*) secara terpisah.

### Tahap 2: Pemetaan Ontologi ke 20 Kelas IndQNER
* Merujuk pada 20 kelas dalam *Annotation Guideline IndQNER*:
  1. Allah
  2. Allah's Throne (`Throne`)
  3. Artifact (`Artifact`)
  4. Astronomical body (`AstronomicalBody`)
  5. Event (`Event`)
  6. False deity (`FalseDeity`)
  7. Holy book (`HolyBook`)
  8. Language (`Language`)
  9. Angel (`Angel`)
  10. Person (`Person`)
  11. Messenger (`Messenger`)
  12. Prophet (`Prophet`)
  13. Sentient (`Sentient`)
  14. Afterlife location (`AfterlifeLocation`)
  15. Geographical location (`GeographicalLocation`)
  16. Color (`Color`)
  17. Religion (`Religion`)
  18. Food (`Food`)
  19. Fruit (`Fruit`)
  20. The book of Allah (`TheBookOfAllah`)
* Memetakan 140 pasangan ke format:
  `mention, uri, count, proposed_label, status_verifikasi`
* Menyimpan kamus pemetaan dalam format CSV dan JSON.

### Tahap 3: Transformasi File IndQEL (+ Kolom `label`)
* Membaca `train_per_mention.tsv`, `val_per_mention.tsv`, dan `test_per_mention.tsv`.
* Menginjeksi kolom `label` berdasarkan hasil lookup dari kamus pemetaan.
* Struktur file keluaran menjadi 6 kolom:
  `surah_id \t ayah \t sentence \t mention \t uri \t label`
* Disimpan ke direktori `data/indqel_labeled/`.

### Tahap 4: Non-Destructive Span Alignment pada Split `train`
* **Mengapa tidak re-tokenization?**  
  File `IndQNER/datasets/train.txt` telah memiliki tokenisasi yang sudah baku. Re-tokenisasi dengan library luar berisiko memecah tanda baca/tanda kurung secara berbeda dan merusak format BIO.
* **Mekanisme Alignment:**
  1. Setiap ayat di `train.txt` dibaca sebagai urutan token berurutan `[(token_1, tag_1), (token_2, tag_2), ...]`.
  2. Cocokkan dengan entitas berlabel pada ayat tersebut dari `train_per_mention.tsv`.
  3. Temukan rentang indeks token (*span indices*) yang membentuk teks mention.
  4. **Aturan Preservasi Mutlak:**
     * Jika token pada span tersebut **sudah memiliki label** (bukan `O`), **JANGAN UBAH**. Nilai lama dipertahankan 100%.
     * Jika token berlabel `O`, ubah menjadi `B-<label>` (token pertama) dan `I-<label>` (token berikutnya).
     * Jika mention diapit tanda kurung seperti `(Al-Qur'an)`, token kurung `(` dan `)` wajib tetap berlabel `O`.
  5. Simpan dataset baru di `data/indqner_revised/train.txt`.

### Tahap 5: Audit & Laporan Verifikasi Matematis
Menjalankan script verifikasi otomatis untuk membuktikan:
1. **Preservasi 100%:** Memeriksa baris demi baris, memastikan tidak ada 1 pun tag lama di IndQNER yang berganti menjadi `O` atau hilang.
2. **Statistik Pengayaan:** Menghitung jumlah penambahan entitas baru per kelas.
3. **Log Perubahan:** Mencatat seluruh baris yang mengalami pengayaan untuk transparansi bab 4 skripsi.

---

## 4. Analisis Potensi Masalah Evaluasi & Mitigasi Ilmiah

Meskipun model training akan dilakukan di proyek/tahap berikutnya, langkah mitigasi berikut dipersiapkan sejak tahap dataset:

### A. "The Silver Label Penalty" (Precision Semu Menurun)
* **Gejala:** Model yang dilatih dengan data revisi mendeteksi entitas baru dengan benar, namun jika diuji pada *Test Set lama IndQNER* (yang belum direvisi), entitas tersebut masih berlabel `O`. Sistem mengkategorikannya sebagai **False Positive (FP)**, sehingga nilai Precision numerik tampak turun.
* **Mitigasi:**
  1. Terapkan **Dual-Evaluation Protocol**: laporkan hasil uji pada *Test Set Original* dan pada *Test Set yang Dianalisis*.
  2. Lakukan **Kajian Kualitatif False Positive**: Ambil sampel False Positive dan tunjukkan di skripsi bahwa sebagian besar "kesalahan" tersebut sebenarnya adalah entitas valid yang terlewat pada dataset asli.

### B. Pergeseran Batas Entitas (Span Boundary Drift)
* **Gejala:** Kesalahan klasifikasi karena tanda baca/kurung penjelasan (misal `(Nabi Muhammad)`).
* **Mitigasi:** Standarisasi isolasi tanda baca pada tahap alignment. Tanda kurung dan koma dipastikan selalu berada di luar span entitas.

### C. Ketimpangan Frekuensi Kelas (Class Imbalance)
* **Gejala:** Entitas `Allah` mendominasi penambahan data, sehingga menaikkan Micro-F1 secara semu tetapi tidak merefleksikan kelas minoritas.
* **Mitigasi:** Audit distribusi penambahan kelas di Tahap 5 dan gunakan **Macro-F1** serta **Per-Class F1 Score** saat evaluasi performa model di masa mendatang.

---

## 5. Struktur Folder Proyek (*Foldering*)

```text
Proyek 1/
│
├── IndQNER/                                 # [REFERENSI] Repository asli IndQNER
│   ├── datasets/                            # train.txt, dev.txt, test.txt asli
│   ├── Evaluation Codes/                    # Kode baseline BiLSTM-CRF & IndoBERT asli
│   └── Annotation guideline in Indonesian.pdf
│
├── datasets IndQEL/                         # [SUMBER] Dataset IndQEL sumber pengayaan
│   ├── train_per_mention.tsv
│   ├── val_per_mention.tsv
│   └── test_per_mention.tsv
│
├── data/                                    # [DATA PIPELINE]
│   ├── mappings/                            # Master kamus 140 pasangan (mention, uri) -> 20 label
│   │   ├── indqel_to_indqner_mapping.csv    # File CSV untuk review manual
│   │   └── indqel_to_indqner_mapping.json   # JSON untuk digunakan script
│   │
│   ├── indqel_labeled/                      # File IndQEL setelah ditambah kolom "label"
│   │   ├── train_per_mention.tsv
│   │   ├── val_per_mention.tsv
│   │   └── test_per_mention.tsv
│   │
│   └── indqner_revised/                     # Dataset IndQNER hasil pengayaan (BIO CoNLL)
│       ├── train.txt                        # train.txt baru (Zero-deletion enriched)
│       ├── dev.txt                          # Salinan dev.txt asli
│       └── test.txt                         # Salinan test.txt asli
│
├── src/                                     # [SOURCE CODE MODULAR]
│   ├── 01_extract_unique_mentions.py        # Ekstraksi 140 mention unik ke CSV pemetaan
│   ├── 02_add_label_to_indqel.py            # Menambahkan kolom "label" ke 3 file IndQEL
│   ├── 03_extract_unlabeled_mentions.py     # Ekstraksi mention belum berlabel (missing entities)
│   ├── 04_enrich_indqner_train.py           # Alignment kontekstual & pengayaan train.txt IndQNER
│   ├── 05_audit_and_verification.py         # Pembuktian matematis zero-deletion & laporan
│   └── generate_location_mapping.py         # Generator pemetaan 140 entitas dengan koordinat lokasi
│
├── reports/                                 # [LOG & BAHAN BAB 4 SKRIPSI]
│   ├── diff_inspection.log                  # Log detail token yang berhasil diperkaya
│   ├── audit_verification.log               # Log verifikasi token audit per baris
│   ├── stats_enrichment_summary.md          # Tabel sebelum vs sesudah untuk naskah skripsi
│   └── unlabeled_mentions_instances.csv     # Detail kemunculan mention tak berlabel di Al-Qur'an
│
├── PROJECT_PLAN.md                          # Dokumentasi lengkap rencana & log eksekusi proyek
└── README.md                                # Panduan operasional eksekusi
```

---

## 6. Jadwal & Langkah Eksekusi Berikutnya

1. **Langkah 1**: Setup direktori proyek (`data/`, `src/`, `reports/`, `notebooks/`). *(Status: SELESAI)*
2. **Langkah 2**: Jalankan `src/01_extract_unique_mentions.py` untuk menghasilkan `indqel_to_indqner_mapping.csv`. *(Status: SELESAI)*
3. **Langkah 3**: Review & finalisasi pemetaan 140 pasangan `(mention, uri)` ke 20 kelas IndQNER serta pembuatan berkas berkolom `location`. *(Status: SELESAI)*
4. **Langkah 4**: Jalankan `src/02_add_label_to_indqel.py` (tambah kolom `label` pada 3 file IndQEL) serta ekstraksi mention belum berlabel. *(Status: SELESAI)*
5. **Langkah 5**: Jalankan `src/04_enrich_indqner_train.py` (alignment kontekstual & pengayaan non-destruktif). *(Status: SELESAI)*
6. **Langkah 6**: Jalankan `src/05_audit_and_verification.py` (audit integritas matematis & laporan final). *(Status: SELESAI)*

---

## 7. Catatan Log Eksekusi & Riwayat Langkah Kerja (Execution Log)

Bagian ini mencatat setiap langkah teknis yang telah dikerjakan secara kronologis, lengkap dengan deskripsi fungsional, justifikasi metodologis, dan status berkas yang dihasilkan.

### 📌 Log 01: Inisialisasi Struktur Foldering Proyek
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Membangun fondasi repositori yang modular, aman (tidak merusak data mentah), dan dapat direproduksi (*reproducible*) untuk kebutuhan penelitian skripsi.
* **Rincian Direktori yang Dibuat & Fungsinya**:
  1. `data/mappings/`:
     * *Fungsi*: Menyimpan berkas pemetaan kamus relasi antara pasangan `(mention, uri)` Wikidata dari IndQEL menuju 20 kelas konsep Qurani IndQNER.
     * *Urgensi Skripsi*: Memastikan seluruh keputusan pelabelan terdokumentasi secara transparan dan dapat diaudit secara manual oleh dosen pembimbing maupun penguji.
  2. `data/indqel_labeled/`:
     * *Fungsi*: Menampung berkas keluaran dari dataset IndQEL (`train_per_mention.tsv`, `val_per_mention.tsv`, `test_per_mention.tsv`) yang telah diperkaya dengan kolom ke-6 yaitu `label`.
     * *Urgensi Skripsi*: Menjaga direktori sumber `datasets IndQEL/` tetap utuh sebagai *ground-truth origin* (prinsip *raw data immutability*).
  3. `data/indqner_revised/`:
     * *Fungsi*: Menampung dataset IndQNER versi revisi dalam format standar CoNLL/BIO. Berisi `train.txt` (hasil pengayaan non-destruktif), serta salinan `dev.txt` dan `test.txt`.
     * *Urgensi Skripsi*: Menjadi artefak dataset final yang siap digunakan untuk training model pada riset lanjutan.
  4. `src/`:
     * *Fungsi*: Menyimpan seluruh kode sumber Python yang diurutkan secara modular (`01_...`, `02_...`, dst.) sesuai urutan pipeline.
     * *Urgensi Skripsi*: Memenuhi kaidah keterulangan riset (*research reproducibility*), di mana pipeline data engineering dapat dijalankan kembali dari nol kapan saja.
  5. `reports/`:
     * *Fungsi*: Menyimpan berkas ringkasan statistik, tabel komparasi sebelum-sesudah revisi, dan log perbedaan baris token (*diff inspection*).
     * *Urgensi Skripsi*: Sumber data kuantitatif yang dapat langsung disalin ke Bab 3 (Metodologi) dan Bab 4 (Hasil dan Pembahasan) skripsi.
  6. `notebooks/`:
     * *Fungsi*: Wadah eksperimen visual dan analisis data eksploratif (EDA) jika dibutuhkan visualisasi interaktif.

### 📌 Log 02: Ekstraksi & Pemetaan Heuristik 140 Pasangan (mention, uri)
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Mengekstrak seluruh entitas unik dari dataset IndQEL lintas seluruh split (`train`, `val`, `test`), mengkuantifikasi frekuensinya, serta memetakan ke 20 kelas konsep Qurani IndQNER sesuai konvensi dataset asli.
* **Berkas yang Dihasilkan**:
  1. `src/01_extract_unique_mentions.py`: Skrip ekstraksi dan pemetaan berbasis aturan cerdas (*smart heuristic* & Wikidata entity).
  2. `data/mappings/indqel_to_indqner_mapping.csv`: Tabel master 140 entitas unik yang dilengkapi jumlah kemunculan per split, usulan label, contoh ayat, dan contoh kalimat.
  3. `data/mappings/indqel_to_indqner_mapping.json`: Kamus lookup terstruktur berformat JSON untuk mempercepat proses eksekusi tahap berikutnya.
* **Temuan & Statistik Data**:
  * Total entitas unik yang ditemukan: **140 pasangan `(mention, uri)`**.
  * Distribusi usulan kelas IndQNER:
    * `Person`: 31 entitas (misal: Bani Israil, Ahlulkitab, Fir‘aun, Maryam, kaum ‘Ad, dsb.)
    * `Allah`: 22 entitas (Lafaz Allah, Asmaul Husna seperti Yang Maha Pengasih, Tuhan semesta alam, dsb.)
    * `Messenger`: 18 entitas (Muhammad, Musa, Ibrahim, Isa, Nuh, Ismail, Harun, Daud, Sulaiman, dsb.)
    * `GeographicalLocation`: 16 entitas (Masjidilharam, Baitulmaqdis, Makkah, Babilonia, Safa, Marwah, dsb.)
    * `Event`: 12 entitas (hari Kiamat, hari Akhir, haji, umrah, Perang Badar, Perang Uhud, hari Sabat, dsb.)
    * `Prophet`: 8 entitas (Adam, Zakaria, Yahya, Ayyub, Ilyas, Ilyasa‘, Yusuf, Israil)
    * `HolyBook`: 6 entitas (Al-Qur’an, Taurat, Injil, Zabur, aż-Żikr, dsb.)
    * `AstronomicalBody`: 5 entitas (bumi, langit, matahari, bulan)
    * `Religion`: 5 entitas (Islam, Nasrani, Yahudi, agama Ibrahim)
    * `Angel`: 5 entitas (Jibril, Mikail, Harut, Marut, Ruhulkudus)
    * `Artifact`: 5 entitas (Ka‘bah, Baitullah, Baitulharam, Tabut, Maqam Ibrahim)
    * `AfterlifeLocation`: 3 entitas (neraka Jahanam, surga ‘Adn)
    * `Color`: 2 entitas (putih, hitam)
    * `Throne`: 1 entitas (ʻArasy)
    * `Language`: 1 entitas (bahasa Arab)
* **Justifikasi Metodologis Skripsi**:
  * Pemisahan kelas `Messenger` dan `Prophet` diselaraskan secara akurat dengan konvensi label IndQNER asli (di mana 5 Rasul Ulul Azmi dan rasul pembawa syariat dilabeli `Messenger`, sementara Nabi non-rasul dilabeli `Prophet`).
  * `Ka‘bah` dan `Baitullah` secara konsisten diarahkan ke kelas `Artifact` sesuai ground truth IndQNER.
  * Setiap baris tabel dilengkapi kutipan ayat spesifik (`sample_verse`) untuk memudahkan validasi silang oleh pakar/pembimbing.

### 📌 Log 03: Review, Finalisasi Pemetaan, dan Pembuatan Berkas Berkolom Location
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Meninjau akurasi 140 label, mengoreksi potensi anomali substring (misal: memastikan `Bani Israil` terkoreksi menjadi `Person`), serta memproduksi berkas pemetaan lengkap berkolom `location` tanpa teks contoh ayat panjang.
* **Berkas yang Dihasilkan / Diperbarui**:
  1. `src/generate_location_mapping.py`: Skrip agregasi koordinat ayat dan pembangun berkas pemetaan lokasi.
  2. `data/mappings/indqel_to_indqner_mapping_with_locations.csv`: Berkas tabel pemetaan final (140 baris) dengan skema:
     `no, mention, uri, total_count, train_count, val_count, test_count, proposed_label, verified_label, status, location`
  3. `data/mappings/indqel_to_indqner_mapping.csv`: Diperbarui dengan status `VERIFIED` dan koreksi label.
  4. `data/mappings/indqel_to_indqner_mapping.json`: Diperbarui dengan status terverifikasi dan array koordinat ayat.
* **Karakteristik Kolom `location`**:
  * Seluruh ayat dan surat tempat kemunculan mention terdata lengkap (bukan sampel 1 ayat saja).
  * Format seragam `nomor_surah:nomor_ayat` (contoh: `2:100`).
  * Diurutkan secara numerik menaik (*sorted ascending by surah & ayah*).
  * Menjadi dasar audit spasial teks Al-Qur'an yang sangat kuat untuk bab pembahasan skripsi.

### 📌 Log 04: Injeksi Kolom Label ke 3 File IndQEL & Ekstraksi Mention Belum Berlabel (Missing Entities)
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Menginjeksi kolom ke-6 (`label`) pada seluruh file IndQEL (`train`, `val`, `test`), serta mengidentifikasi secara komprehensif mention-mention mana saja yang saat ini belum terlabeli (berstatus `O` / *missing entities*) di dataset `train.txt` IndQNER asli beserta seluruh titik koordinat lokasinya.
* **Berkas yang Dihasilkan**:
  1. `src/02_add_label_to_indqel.py`: Skrip penambahan kolom `label` pada data tabular IndQEL.
  2. `data/indqel_labeled/train_per_mention.tsv`: 2.093 mention berlabel (231 baris tanpa mention).
  3. `data/indqel_labeled/val_per_mention.tsv`: 265 mention berlabel (28 baris tanpa mention).
  4. `data/indqel_labeled/test_per_mention.tsv`: 240 mention berlabel (29 baris tanpa mention).
  5. `src/03_extract_unlabeled_mentions.py`: Skrip pencocokan token span IndQNER vs IndQEL untuk mendeteksi *False Negatives*.
  6. `data/mappings/mentions_unlabeled_in_indqner.csv`: Berkas rekapitulasi mention yang berstatus `O` di IndQNER lengkap dengan kolom `locations` (`surah:ayah`).
  7. `reports/unlabeled_mentions_instances.csv`: Berkas log detail kejadian demi kejadian (101 baris) mencakup ayat, mention, kelas target, tag asal, dan kutipan kalimat.
* **Temuan Signifikan untuk Skripsi**:
  * Dari 2.093 baris mention di `train_per_mention.tsv`, ditemukan **101 kemunculan mention yang terlewat (berstatus 'O') di `train.txt` IndQNER asli**.
  * Rincian 9 konsep entitas yang terlewat:
    1. `langit` (`AstronomicalBody`): **61 kemunculan terlewat** (misal di 2:19, 2:22, 2:33, 2:59, dst.).
    2. `Ahlulkitab` (`Person`): **18 kemunculan terlewat** (misal di 2:105, 2:109, 3:64, 3:65, dst.).
    3. `Tuhan semesta alam` (`Allah`): **8 kemunculan terlewat** (di 5:28, 6:71, 7:54, 7:61, dst.).
    4. `Saleh` (`Messenger`): **4 kemunculan terlewat** (di 7:73, 7:75, 7:77, 7:79).
    5. `putih` (`Color`): **3 kemunculan terlewat** (di 2:61, 2:187, 3:107).
    6. `hitam` (`Color`): **3 kemunculan terlewat** (di 2:187, 10:26, 16:58).
    7. `yang menghidupkan dan mematikan` (`Allah`): **2 kemunculan terlewat** (di 2:258, 10:56).
    8. `bulan` (`AstronomicalBody`): **1 kemunculan terlewat** (di 2:226).
    9. `Hawa` (`Person`): **1 kemunculan terlewat** (di 4:25).
  * Temuan ini menjadi bukti ilmiah terpenting bagi skripsi: membuktikan secara empiris bahwa dataset IndQNER asli memiliki entitas yang tidak dianotasi (*False Negatives*), dan pengayaan melalui IndQEL akan menyempurnakan korpus tersebut.

### 📌 Log 05: Penyelarasan Kontekstual & Pengayaan Dataset IndQNER train.txt (Non-Destruktif)
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Menginjeksi label BIO baru pada token-token di `IndQNER/datasets/train.txt` yang sebelumnya berstatus `O` berdasarkan kemunculan mention terverifikasi di IndQEL train, dengan mematuhi secara mutlak **Strict Zero Deletion Policy** dan **Preservasi Split Evaluasi**.
* **Algoritma & Metodologi Pencocokan**:
  * Menggunakan *Window Overlap & Sequence Alignment*: Mencocokkan n-gram kata mention pada korpus `train.txt` lalu menghitung skor tumpang-tindih (*lexical overlap score*) terhadap teks kalimat ayat aslinya.
  * Memilih kandidat dengan skor irisan tertinggi, sehingga secara presisi membedakan kata jamak yang sering berulang (seperti kata `langit` yang muncul puluhan kali) tepat pada ayat yang bersangkutan tanpa menabrak token ayat lain.
  * Mempertahankan 100% token yang sudah memiliki label ground truth (1.782 mention ground truth dipertahankan utuh).
  * Menyalin `dev.txt` dan `test.txt` dari `IndQNER/datasets/` ke `data/indqner_revised/` secara murni tanpa modifikasi bit sedikitpun (menjamin validitas evaluasi model di proyek berikutnya).
* **Berkas yang Dihasilkan**:
  1. `src/04_enrich_indqner_train.py`: Skrip pengayaan cerdas berbasis penyelarasan kontekstual.
  2. `data/indqner_revised/train.txt`: Berkas CoNLL BIO hasil revisi yang telah diperkaya.
  3. `data/indqner_revised/dev.txt`: Salinan murni `dev.txt` asli.
  4. `data/indqner_revised/test.txt`: Salinan murni `test.txt` asli.
  5. `reports/diff_inspection.log`: Log kronologis seluruh 88 span mention yang berhasil diperkaya.
* **Hasil Kuantitatif Pengayaan**:
  * Total Entitas Baru yang Diperkaya (*New Spans*): **88 span mention**.
  * Total Token Kata yang Bermutasi dari `O` ke Label Entitas: **105 token kata**.
  * Rincian penambahan tag per kelas:
    * `AstronomicalBody`: **+59 token** (`langit` dan `bulan`).
    * `Person`: **+17 token** (`Ahlulkitab`).
    * `Allah`: **+25 token** (8 `B-Allah` + 17 `I-Allah` untuk Asmaul Husna multi-kata).
    * `Color`: **+4 token** (`putih` dan `hitam`).
    * `O` (Non-entity): Berkurang tepat **-105 token** (46.771 -> 46.666).
    * 20 kelas lainnya: Tetap utuh 100% tanpa ada yang berkurang.

### 📌 Log 06: Audit Integritas Matematis & Verifikasi Menyeluruh (Zero-Deletion Guarantee)
* **Waktu Eksekusi**: 2026-10-09
* **Status**: ✅ **SELESAI (COMPLETED)**
* **Tujuan**: Membuktikan secara matematis dan algoritmik bahwa revisi dataset memenuhi standar baku integritas akademik: tidak ada satu pun token kata yang bergeser atau berubah hurufnya, tidak ada satu pun label lama yang terhapus, format skema BIO 100% valid, serta split `dev` dan `test` 100% identik.
* **Berkas yang Dihasilkan**:
  1. `src/05_audit_and_verification.py`: Skrip pengujian otomatis komparasi token-by-token dan validasi checksum MD5.
  2. `reports/stats_enrichment_summary.md`: Laporan komprehensif dalam format tabel Markdown siap pakai untuk Bab 3 & 4 Skripsi.
  3. `reports/audit_verification.log`: Log audit baris demi baris dari seluruh 105 token yang diperkaya.
* **Hasil Verifikasi Integritas (Semua Tes Passed 100%)**:
  1. *Row & Token Integrity Check*:
     * Jumlah baris asli `train.txt`: **51.570 baris** vs revisi: **51.570 baris** (Delta = 0).
     * Jumlah token kata asli: **49.076 token** vs revisi: **49.076 token** (Delta = 0, kata identik 100%).
  2. *Strict Zero Deletion Guarantee*:
     * Label ground truth asli yang terhapus menjadi `O`: **0 label (0.0%)**.
     * Label ground truth asli yang tertimpa label lain: **0 label (0.0%)**.
  3. *BIO Tagging Scheme Consistency*:
     * Ditemukan **0 token invalid/orphan `I-`** (semua tag `I-` didahului secara sah oleh tag `B-` dari kelas yang sama).
  4. *Evaluation Split Bit-by-Bit Checksum*:
     * `dev.txt`: MD5 `58e215d6b8c1c8187eedd875da194ff5` == `58e215d6b8c1c8187eedd875da194ff5` (100% Identik).
     * `test.txt`: MD5 `748389f59c44a48a8fec5ff0a7f98769` == `748389f59c44a48a8fec5ff0a7f98769` (100% Identik).





