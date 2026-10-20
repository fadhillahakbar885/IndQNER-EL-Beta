# IndQNER 1.0: Indonesian Quranic Named Entity Recognition (Verse-Level Benchmark)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Format: CoNLL BIO](https://img.shields.io/badge/Format-CoNLL--BIO-blue.svg)](#format-data)
[![Status: Verified](https://img.shields.io/badge/Zero--Deletion-100%25%20Verified-brightgreen.svg)](#prinsip-integritas-dataset)

**IndQNER 1.0** adalah dataset *benchmark* untuk tugas **Named Entity Recognition (NER)** pada teks Terjemahan Al-Qur'an Bahasa Indonesia (Kementerian Agama RI). Dataset ini merupakan revisi dan penyempurnaan struktural tingkat lanjut dari dataset IndQNER awal dengan menerapkan standar segmentasi **Satu Ayat = Satu Teks (Verse-Level Annotation)** serta pengayaan entitas Qurani (*Entity Enrichment*) berbasis korpus **IndQEL** (*Indonesian Quranic Entity Linking*).

---

## 🌟 Fitur Utama & Keunggulan IndQNER 1.0

1. **Segmentasi Berbasis Ayat (1 Teks = 1 Ayat Al-Qur'an)**:
   * Pada versi awal, pemotongan teks dilakukan berbasis tanda titik (`.`) atau tanya (`?`), sehingga 1 ayat panjang terpecah menjadi 2–5 kalimat terfragmentasi.
   * Pada **IndQNER 1.0**, seluruh kalimat di dalam ayat yang sama disatukan secara sekuensial tanpa baris kosong pemisah. Baris kosong (`\n`) **hanya memisahkan antar satu teks ayat dengan teks ayat berikutnya**.
2. **Pengayaan Entitas Qurani (Entity Enrichment)**:
   * Melalui pemetaan terpadu dengan korpus IndQEL, entitas Qurani yang sebelumnya belum dianotasi (*False Negatives* / status `O`) telah diperkaya dengan penambahan entitas valid (seperti entitas bahasa Arab, para Rasul, dan konsep Qurani lainnya).
3. **Strict Zero Deletion & Zero Corruption Guarantee**:
   * **100% kata dan label asli dipertahankan**: Tidak ada satu pun kata atau label asli yang hilang atau tertimpa secara tidak sengaja.
4. **Validasi Resmi Kementerian Agama RI**:
   * Teks terjemahan telah divalidasi silang terhadap basis data resmi Al-Qur'an Kementerian Agama RI (`quran.kemenag.go.id`) dengan tingkat keselarasan leksikal rata-rata **97.7% – 99.3%**.

---

## 📊 Statistik Dataset

Dataset mencakup **8 Surah Utama** dalam Al-Qur'an: *Surah Al-Baqarah (2), Ali 'Imran (3), An-Nisa' (4), Al-Ma'idah (5), Al-An'am (6), Al-A'raf (7), Yunus (10), dan An-Nahl (16)*.

| Berkas Split | Jumlah Ayat (Teks) | Total Token Kata | Jumlah Entitas Qurani | Peruntukan Evaluasi |
| :--- | :---: | :---: | :---: | :--- |
| **`train.txt`** | **1.050 ayat** | **49.076 token** | **2.091 entitas** | Data Latih (*Training Set*) |
| **`dev.txt`** | **161 ayat** | **6.895 token** | **244 entitas** | Validasi & Tuning Hiperparameter |
| **`test.txt`** | **176 ayat** | **6.056 token** | **240 entitas** | Evaluasi Akhir (*Gold Standard Benchmark*) |
| **TOTAL** | **1.387 ayat** | **62.027 token** | **2.575 entitas** | **Korpus Lengkap** |

---

## 🏷️ Daftar Kelas Entitas Qurani (20 Classes)

Skema anotasi mengadopsi standar 20 kelas konsep Qurani:

1. `Allah`: Nama, Asmaul Husna, dan sebutan Allah Swt.
2. `Messenger`: Para Rasul utusan Allah (Nabi Muhammad, Musa, Isa, Ibrahim, dll.).
3. `Prophet`: Para Nabi Allah.
4. `Person`: Tokoh manusia, kaum, keluarga, atau figur bersejarah (Bani Israil, Fir'aun, Adam, Maryam, dll.).
5. `HolyBook`: Kitab suci samawi (Al-Qur'an, Taurat, Injil, Zabur).
6. `AstronomicalBody`: Benda langit (matahari, bulan, bintang, langit).
7. `Event`: Peristiwa besar Qurani (hari Kiamat, hari Akhir, Kiamat, dll.).
8. `AfterlifeLocation`: Tempat kehidupan akhirat (surga, neraka, Jahanam, 'Adn).
9. `GeographicalLocation`: Lokasi geografi di bumi (Mekah, Madinah, Mesir, dll.).
10. `Artifact`: Benda peninggalan bersejarah/suci (Ka'bah, Maqam Ibrahim, Tabut).
11. `Throne`: 'Arasy Allah Swt.
12. `Religion`: Agama yang disebutkan dalam Al-Qur'an (Islam, Yahudi, Nasrani, Majusi).
13. `Angel`: Malaikat Allah (Jibril, Mikail, dll.).
14. `Color`: Warna-warna spesifik (putih, hitam, kuning, hijau).
15. `Language`: Bahasa yang disebutkan (bahasa Arab, bahasa 'Ajam).
16. `Food`: Makanan yang disebutkan secara khusus.
17. `Fruit`: Buah-buahan Qurani.
18. `FalseDeity`: Berhala atau sesembahan selain Allah (Latta, Uzza, dll.).
19. `Sentient`: Makhluk gaib berakal (jin, setan, Iblis).
20. `TheBookOfAllah`: Lembaran-lembaran wahyu Allah (*Suhuf*).

---

## 📝 Format Data (CoNLL BIO)

Dataset disajikan dalam format standar industri **CoNLL BIO** (`word \t tag`), dengan ketentuan:
* Kolom 1: Kata / Token.
* Kolom 2: Tag BIO (`B-<Class>`, `I-<Class>`, atau `O`).
* **Pemisah Antar Teks**: Tepat **satu baris kosong (`\n`)** diletakkan sebagai batas antar teks ayat Al-Qur'an.

### Contoh Format (`Surah 2:7`):

```text
Allah	B-Allah
telah	O
mengunci	O
hati	O
dan	O
pendengaran	O
mereka	O
.	O
Pada	O
penglihatan	O
mereka	O
ada	O
penutup	O
,	O
dan	O
bagi	O
mereka	O
azab	O
yang	O
sangat	O
berat	O
.	O

Di	O
antara	O
manusia	O
ada	O
yang	O
berkata	O
...
```

---

## 💻 Cara Menggunakan Dataset

### 1. Membaca dengan Python murni:
```python
def load_indqner(file_path):
    sentences = []
    current_tokens, current_tags = [], []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_tokens:
                    sentences.append({"tokens": current_tokens, "tags": current_tags})
                    current_tokens, current_tags = [], []
            else:
                parts = line.split("\t")
                current_tokens.append(parts[0])
                current_tags.append(parts[1] if len(parts) > 1 else "O")
        if current_tokens:
            sentences.append({"tokens": current_tokens, "tags": current_tags})
    return sentences

train_data = load_indqner("train.txt")
print(f"Total Ayat Train: {len(train_data)}")
print("Ayat pertama:", " ".join(train_data[0]["tokens"]))
```

### 2. Membaca dengan Hugging Face `datasets`:
```python
from datasets import load_dataset

dataset = load_dataset(
    "conll2003",
    data_files={"train": "train.txt", "validation": "dev.txt", "test": "test.txt"}
)
print(dataset)
```

---

## 📜 Lisensi & Atribusi

Dataset ini didistribusikan di bawah lisensi **MIT License**.

Jika Anda menggunakan dataset ini dalam penelitian atau publikasi ilmiah, silakan mengutip:
```bibtex
@misc{indqner1.0_2026,
  author = {Akbar, Muhammad Fadhillah},
  title = {IndQNER 1.0: Indonesian Quranic Named Entity Recognition (Verse-Level Benchmark)},
  year = {2026},
  publisher = {GitHub},
  howpublished = {\url{https://github.com/fadhillahakbar885/IndQNER-1.0}}
}
```

Serta merujuk pada publikasi awal korpus IndQNER & IndQEL:
```bibtex
@inproceedings{gusmita2023indqner,
  title={IndQNER: Named Entity Recognition Benchmark Dataset from the Indonesian Translation of the Quran},
  author={Gusmita, Ria Hari and Firmansyah, Asep Fajar and Moussallem, Diego and Ngonga Ngomo, Axel-Cyrille},
  booktitle={Natural Language Processing and Information Systems (NLDB 2023)},
  pages={170--185},
  year={2023},
  publisher={Springer}
}
```
