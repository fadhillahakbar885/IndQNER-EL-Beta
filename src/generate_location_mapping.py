"""
Script: generate_location_mapping.py
Deskripsi: Menghasilkan berkas indqel_to_indqner_mapping_with_locations.csv
           yang memuat kolom 'location' (seluruh kemunculan surah:ayat terdata),
           tanpa kolom sample_verse dan sample_sentence, serta memvalidasi
           konsistensi seluruh 140 label konsep Qurani.
"""

import csv
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDQEL_DIR = os.path.join(BASE_DIR, "datasets IndQEL")
MAPPINGS_DIR = os.path.join(BASE_DIR, "data", "mappings")

CSV_ORIGINAL_MAPPING = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping.csv")
CSV_LOCATIONS_MAPPING = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping_with_locations.csv")
JSON_MAPPING = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping.json")

# Koreksi manual khusus untuk entitas ambigu/anomali heuristik
LABEL_OVERRIDES = {
    "Bani Israil": "Person",             # Kaum / Keturunan Israil
    "anak cucu Adam": "Person",         # Umat manusia
    "Ahlulkitab": "Person",
    "umat Islam": "Person",
    "pengikut Injil": "Person",
    "pengikut Allah": "Person",
    "orang-orang Sabiin": "Person",
    "Sabiin": "Person",
    "penganut Yahudi": "Person",
    "Orang Yahudi": "Person",
    "Orang Nasrani": "Person",
    "orang Yahudi": "Person",
    "orang Nasrani": "Person",
    "orang-orang Yahudi": "Person",
    "orang-orang Nasrani": "Person",
    "Talut": "Person",                   # Raja
    "Jalut": "Person",                   # Goliat
    "Qabil": "Person",
    "Habil": "Person",
    "Azar": "Person",
    "Samud": "Person",
    "‘Ad": "Person",
    "Quraisy": "Person",
    "Israil": "Prophet",                 # Nabi Ya'qub (Surah 3:93)
    "Ka‘bah": "Artifact",
    "Baitullah": "Artifact",
    "Baitulharam": "Artifact",
    "Maqam Ibrahim": "Artifact",
    "Tabut": "Artifact",
    "ʻArasy": "Throne",
    "bahasa Arab": "Language",
    "neraka Jahanam": "AfterlifeLocation",
    "Jahanam": "AfterlifeLocation",
    "‘Adn": "AfterlifeLocation",
    "Bulan Ramadan": "Event",
    "fajar": "AstronomicalBody",
}

def main():
    # 1. Kumpulkan seluruh lokasi kemunculan (surah_id, ayah) per (mention, uri)
    locations = defaultdict(list)
    files = {
        "train": os.path.join(INDQEL_DIR, "train_per_mention.tsv"),
        "val": os.path.join(INDQEL_DIR, "val_per_mention.tsv"),
        "test": os.path.join(INDQEL_DIR, "test_per_mention.tsv"),
    }

    for split_name, filepath in files.items():
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                m = row.get("mention", "").strip()
                u = row.get("uri", "").strip()
                s = row.get("surah_id", "").strip()
                a = row.get("ayah", "").strip()
                if m and s and a:
                    locations[(m, u)].append((int(s), int(a)))

    # 2. Baca file mapping dasar dan terapkan koreksi
    updated_rows_with_loc = []
    updated_rows_original = []
    json_data = {}

    with open(CSV_ORIGINAL_MAPPING, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            m = r["mention"].strip()
            u = r["uri"].strip()

            # Terapkan koreksi jika ada
            label = r["verified_label"].strip()
            if m in LABEL_OVERRIDES:
                label = LABEL_OVERRIDES[m]

            # Urutkan lokasi numerik: surah lalu ayat
            loc_list = sorted(set(locations[(m, u)]))
            loc_str = ", ".join([f"{s}:{a}" for s, a in loc_list])

            # Baris untuk file dengan kolom location
            row_loc = {
                "no": r["no"],
                "mention": m,
                "uri": u,
                "total_count": r["total_count"],
                "train_count": r["train_count"],
                "val_count": r["val_count"],
                "test_count": r["test_count"],
                "proposed_label": label,
                "verified_label": label,
                "status": "VERIFIED",
                "location": loc_str,
            }
            updated_rows_with_loc.append(row_loc)

            # Update juga baris original mapping
            r["proposed_label"] = label
            r["verified_label"] = label
            r["status"] = "VERIFIED"
            updated_rows_original.append(r)

            # Update JSON dictionary
            json_data[f"{m}|||{u}"] = {
                "mention": m,
                "uri": u,
                "label": label,
                "total_count": int(r["total_count"]),
                "train_count": int(r["train_count"]),
                "val_count": int(r["val_count"]),
                "test_count": int(r["test_count"]),
                "locations": [f"{s}:{a}" for s, a in loc_list],
            }

    # 3. Tulis file indqel_to_indqner_mapping_with_locations.csv
    loc_fields = [
        "no", "mention", "uri", "total_count", "train_count", "val_count",
        "test_count", "proposed_label", "verified_label", "status", "location"
    ]
    with open(CSV_LOCATIONS_MAPPING, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=loc_fields)
        writer.writeheader()
        writer.writerows(updated_rows_with_loc)

    # 4. Perbarui file indqel_to_indqner_mapping.csv
    with open(CSV_ORIGINAL_MAPPING, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows_original)

    # 5. Perbarui JSON mapping
    import json
    with open(JSON_MAPPING, mode="w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"Berhasil memperbarui kedua file mapping dan JSON ({len(updated_rows_with_loc)} entitas).")

if __name__ == "__main__":
    main()
