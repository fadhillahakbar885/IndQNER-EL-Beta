# Laporan Audit dan Statistik Pengayaan Dataset IndQNER

> **Status Integritas**: **100% TERVERIFIKASI (PASSED)**  
> **Strict Zero Deletion**: **0 Label Terhapus / 0 Label Tertimpa**  
> **Preservasi Split Dev & Test**: **100% Murni (Identik Bit-by-Bit)**

---

## 1. Ringkasan Eksekutif Perubahan Dataset

| Metrik Dataset | IndQNER Asli (`train.txt`) | IndQNER Revisi (`train.txt`) | Perubahan (Delta) | Catatan Integritas |
| :--- | :---: | :---: | :---: | :--- |
| **Total Baris File** | 51,570 | 51,570 | 0 | Identik 100% |
| **Total Token Kata** | 49,076 | 49,076 | 0 | Preservasi korpus |
| **Total Entitas (Span `B-*`)** | 2,007 | 2,095 | **+88** | Entitas baru terinjeksi |
| **Total Token Berlabel Entitas** | 2,305 | 2,410 | **+105** | Mutasi dari tag `O` |
| **Token Non-Entitas (`O`)** | 46,771 | 46,666 | **-105** | Berkurang proporsional |
| **Label Ground-Truth Terhapus** | 0 | 0 | **0** | **Strict Zero Deletion Guaranteed** |
| **Label Ground-Truth Tertimpa** | 0 | 0 | **0** | **Strict Preservation Guaranteed** |

## 2. Perbandingan Frekuensi Tag Per Kelas Entitas

| Label / Kelas Entitas | Frekuensi Asli | Frekuensi Revisi | Delta (Penambahan) | Persentase Kenaikan |
| :--- | :---: | :---: | :---: | :---: |
| `B-AfterlifeLocation` | 16 | 16 | 0 | 0.0% |
| `B-Allah` | 1,138 | 1,146 | **+8** | +0.7% |
| `B-Angel` | 13 | 13 | 0 | 0.0% |
| `B-Artifact` | 20 | 20 | 0 | 0.0% |
| `B-AstronomicalBody` | 96 | 155 | **+59** | +61.5% |
| `B-Color` | 1 | 5 | **+4** | +400.0% |
| `B-Event` | 84 | 84 | 0 | 0.0% |
| `B-Food` | 2 | 2 | 0 | 0.0% |
| `B-GeographicalLocation` | 23 | 23 | 0 | 0.0% |
| `B-HolyBook` | 106 | 106 | 0 | 0.0% |
| `B-Language` | 1 | 1 | 0 | 0.0% |
| `B-Messenger` | 307 | 307 | 0 | 0.0% |
| `B-Person` | 138 | 155 | **+17** | +12.3% |
| `B-Prophet` | 48 | 48 | 0 | 0.0% |
| `B-Religion` | 13 | 13 | 0 | 0.0% |
| `B-Throne` | 1 | 1 | 0 | 0.0% |
| `I-AfterlifeLocation` | 1 | 1 | 0 | 0.0% |
| `I-Allah` | 127 | 144 | **+17** | +13.4% |
| `I-Artifact` | 2 | 2 | 0 | 0.0% |
| `I-Color` | 1 | 1 | 0 | 0.0% |
| `I-Event` | 56 | 56 | 0 | 0.0% |
| `I-GeographicalLocation` | 3 | 3 | 0 | 0.0% |
| `I-Language` | 1 | 1 | 0 | 0.0% |
| `I-Messenger` | 29 | 29 | 0 | 0.0% |
| `I-Person` | 73 | 73 | 0 | 0.0% |
| `I-Religion` | 5 | 5 | 0 | 0.0% |
| `O` (Non-Entity) | 46,771 | 46,666 | **-105** | -0.22% |

## 3. Verifikasi Kemurnian Split Evaluasi (`dev.txt` & `test.txt`)

| File Split | MD5 Checksum Asli | MD5 Checksum Revisi | Status Integritas |
| :--- | :---: | :---: | :--- |
| `dev.txt` | `58e215d6b8c1c8187eedd875da194ff5` | `58e215d6b8c1c8187eedd875da194ff5` | ✅ 100% Identik (Tidak dimodifikasi) |
| `test.txt` | `748389f59c44a48a8fec5ff0a7f98769` | `748389f59c44a48a8fec5ff0a7f98769` | ✅ 100% Identik (Tidak dimodifikasi) |

## 4. Log Sampel Token yang Berhasil Diperkaya

| No | Baris Line | Kata / Token | Tag Asli | Tag Revisi |
| :-: | :-: | :--- | :-: | :-: |
| 1 | 453 | **langit** | `O` | `B-AstronomicalBody` |
| 2 | 581 | **langit** | `O` | `B-AstronomicalBody` |
| 3 | 594 | **langit** | `O` | `B-AstronomicalBody` |
| 4 | 957 | **langit** | `O` | `B-AstronomicalBody` |
| 5 | 964 | **langit** | `O` | `B-AstronomicalBody` |
| 6 | 1,141 | **langit** | `O` | `B-AstronomicalBody` |
| 7 | 2,052 | **langit** | `O` | `B-AstronomicalBody` |
| 8 | 2,183 | **putih** | `O` | `B-Color` |
| 9 | 4,357 | **Ahlulkitab** | `O` | `B-Person` |
| 10 | 4,441 | **langit** | `O` | `B-AstronomicalBody` |
| 11 | 4,503 | **Ahlulkitab** | `O` | `B-Person` |
| 12 | 4,852 | **langit** | `O` | `B-AstronomicalBody` |
| 13 | 4,867 | **langit** | `O` | `B-AstronomicalBody` |
| 14 | 6,245 | **langit** | `O` | `B-AstronomicalBody` |
| 15 | 7,026 | **langit** | `O` | `B-AstronomicalBody` |
| 16 | 7,054 | **langit** | `O` | `B-AstronomicalBody` |
| 17 | 7,086 | **langit** | `O` | `B-AstronomicalBody` |
| 18 | 8,048 | **bulan** | `O` | `B-AstronomicalBody` |
| 19 | 8,094 | **bulan** | `O` | `B-AstronomicalBody` |
| 20 | 8,270 | **putih** | `O` | `B-Color` |
| 21 | 8,273 | **hitam** | `O` | `B-Color` |
| 22 | 8,386 | **bulan** | `O` | `B-AstronomicalBody` |
| 23 | 10,397 | **bulan** | `O` | `B-AstronomicalBody` |
| 24 | 12,392 | **langit** | `O` | `B-AstronomicalBody` |
| 25 | 12,453 | **langit** | `O` | `B-AstronomicalBody` |
| ... | ... | *(Total 105 token diperkaya)* | ... | ... |
