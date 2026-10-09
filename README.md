# Pengayaan Dataset Indonesian Quranic NER (IndQNER) Berbasis Entity Linking (IndQEL)

Proyek penelitian pengayaan dan penyelarasan dataset **IndQNER** (*Indonesian Quranic Named Entity Recognition*) menggunakan basis kemunculan entitas dari dataset **IndQEL** (*Indonesian Quranic Entity Linking*), dengan menerapkan **Strict Zero Deletion Policy** (preservasi 100% ground-truth asli) serta preservasi murni split evaluasi (*dev* & *test*).

---

## 📌 Ringkasan Hasil Pengayaan & Audit Integritas

| Metrik Dataset | IndQNER Asli (`train.txt`) | IndQNER Revisi (`train.txt`) | Delta (Perubahan) | Status Integritas |
| :--- | :---: | :---: | :---: | :--- |
| **Total Baris** | 51.570 | 51.570 | **0** | ✅ Identik 100% |
| **Total Token Kata** | 49.076 | 49.076 | **0** | ✅ Preservasi Korpus Kata |
| **Entitas Baru (`B-*` Span)** | 2.007 | 2.095 | **+88 span** | 🚀 Entitas Baru Terinjeksi |
| **Token Berlabel Entitas** | 2.305 | 2.410 | **+105 token** | 🚀 Bermutasi dari status `O` |
| **Token Non-Entitas (`O`)** | 46.771 | 46.666 | **-105 token** | Berkurang proporsional |
| **Label Asli Terhapus/Tertimpa**| 0 | 0 | **0** | 🛡️ **Zero Deletion Guarantee** |
| **Split `dev.txt` & `test.txt`** | — | — | **0 bit diff** | ✅ MD5 Checksum Identik 100% |

---

## 🗂️ Struktur Direktori Proyek

```text
├── data/
│   ├── mappings/
│   │   ├── indqel_to_indqner_mapping_with_locations.csv  # 140 entitas unik + koordinat surah:ayah
│   │   ├── indqel_to_indqner_mapping.csv                 # Master kamus relasi IndQEL -> IndQNER
│   │   ├── indqel_to_indqner_mapping.json                # Master JSON dictionary
│   │   └── mentions_unlabeled_in_indqner.csv             # Daftar mention yang terlewat di IndQNER
│   │
│   ├── indqel_labeled/                                   # 3 berkas IndQEL ditambah kolom ke-6 "label"
│   │   ├── train_per_mention.tsv                         # 2.093 mention berlabel
│   │   ├── val_per_mention.tsv                           # 265 mention berlabel
│   │   └── test_per_mention.tsv                          # 240 mention berlabel
│   │
│   └── indqner_revised/                                  # Dataset IndQNER Final Format CoNLL/BIO
│       ├── train.txt                                     # train.txt hasil revisi & pengayaan
│       ├── dev.txt                                       # Salinan murni dev.txt asli (benchmark)
│       └── test.txt                                      # Salinan murni test.txt asli (benchmark)
│
├── src/
│   ├── 01_extract_unique_mentions.py                     # Ekstraksi 140 mention unik
│   ├── 02_add_label_to_indqel.py                         # Injeksi kolom label ke IndQEL TSV
│   ├── 03_extract_unlabeled_mentions.py                  # Identifikasi missing entities & lokasi
│   ├── 04_enrich_indqner_train.py                        # Penyelarasan kontekstual & pengayaan train.txt
│   ├── 05_audit_and_verification.py                      # Audit integritas matematis token-by-token
│   └── generate_location_mapping.py                      # Agregasi koordinat surah:ayah
│
├── reports/
│   ├── stats_enrichment_summary.md                       # Laporan komparatif siap pakai untuk Skripsi
│   ├── detailed_88_spans_105_tokens.md                   # Rincian 88 span & 105 token yang diperkaya
│   ├── diff_inspection.log                               # Log audit penambahan tag BIO
│   └── audit_verification.log                            # Log audit baris demi baris
│
├── PROJECT_PLAN.md                                       # Master blueprint dan riwayat Log 01-06
├── README.md                                             # Dokumentasi utama repositori
└── .gitignore                                            # Konfigurasi ignore file temporary
```

---

## 🚀 Cara Menjalankan Pipeline (Reproducibility)

Jalankan seluruh skrip secara berurutan:

```bash
# 1. Ekstraksi 140 mention unik
python src/01_extract_unique_mentions.py

# 2. Pembuatan berkas pemetaan berkolom location
python src/generate_location_mapping.py

# 3. Injeksi kolom label ke 3 berkas IndQEL
python src/02_add_label_to_indqel.py

# 4. Ekstraksi mention belum berlabel (missing entities)
python src/03_extract_unlabeled_mentions.py

# 5. Penyelarasan kontekstual dan pengayaan train.txt
python src/04_enrich_indqner_train.py

# 6. Audit integritas matematis & pembuktian zero-deletion
python src/05_audit_and_verification.py
```

---

## 📜 Lisensi & Atribusi

Dataset asli dirujuk dari:
1. **IndQNER**: *Indonesian Quranic Named Entity Recognition*
2. **IndQEL**: *Indonesian Quranic Entity Linking*
"# IndQNER-EL-Beta" 
