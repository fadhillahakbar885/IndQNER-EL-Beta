"""
Script: 02_add_label_to_indqel.py
Deskripsi: Menambahkan kolom 'label' pada ketiga berkas IndQEL
           (train_per_mention.tsv, val_per_mention.tsv, test_per_mention.tsv)
           menggunakan kamus pemetaan terverifikasi indqel_to_indqner_mapping.json.
           Hasil disimpan ke folder data/indqel_labeled/.
"""

import csv
import json
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDQEL_DIR = os.path.join(BASE_DIR, "datasets IndQEL")
MAPPINGS_DIR = os.path.join(BASE_DIR, "data", "mappings")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "indqel_labeled")

MAPPING_JSON = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping.json")

FILES = [
    "train_per_mention.tsv",
    "val_per_mention.tsv",
    "test_per_mention.tsv"
]

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Muat kamus pemetaan
    with open(MAPPING_JSON, mode="r", encoding="utf-8") as f:
        mapping = json.load(f)
    print(f"Berhasil memuat {len(mapping)} entitas dari {MAPPING_JSON}")

    # 2. Proses tiap berkas IndQEL
    for filename in FILES:
        input_path = os.path.join(INDQEL_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)

        if not os.path.exists(input_path):
            print(f"Warning: Berkas tidak ditemukan: {input_path}")
            continue

        total_rows = 0
        labeled_mentions = 0
        empty_mentions = 0
        unmapped_mentions = 0
        label_counter = Counter()

        rows_to_write = []
        with open(input_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            fieldnames = list(reader.fieldnames)
            if "label" not in fieldnames:
                fieldnames.append("label")

            for row in reader:
                total_rows += 1
                mention = row.get("mention", "").strip()
                uri = row.get("uri", "").strip()

                if not mention:
                    row["label"] = ""
                    empty_mentions += 1
                else:
                    key = f"{mention}|||{uri}"
                    if key in mapping:
                        label = mapping[key]["label"]
                        row["label"] = label
                        labeled_mentions += 1
                        label_counter[label] += 1
                    else:
                        print(f"Warning: Mention tidak ditemukan di mapping: '{mention}' ({uri})")
                        row["label"] = "O"
                        unmapped_mentions += 1

                rows_to_write.append(row)

        # Tulis ke file keluaran di data/indqel_labeled/
        with open(output_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows_to_write)

        print(f"\n==========================================")
        print(f"File: {filename}")
        print(f"Output: {output_path}")
        print(f"Total Baris: {total_rows}")
        print(f"Mention Berlabel: {labeled_mentions}")
        print(f"Baris Tanpa Mention: {empty_mentions}")
        print(f"Mention Tidak Terpetakan: {unmapped_mentions}")
        print("Distribusi Label:")
        for lbl, count in label_counter.most_common():
            print(f"  - {lbl}: {count}")

if __name__ == "__main__":
    main()
