"""
Script: 03_extract_unlabeled_mentions.py
Deskripsi: Mengidentifikasi seluruh mention dari dataset IndQEL yang belum terlabeli
           (berstatus tag 'O' / missing entities) di dalam dataset IndQNER asli.
           Menghasilkan berkas rekapitulasi data_mappings/mentions_unlabeled_in_indqner.csv
           dan laporan rincian reports/unlabeled_mentions_instances.csv.
"""

import csv
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDQNER_TRAIN = os.path.join(BASE_DIR, "IndQNER", "datasets", "train.txt")
INDQEL_LABELED_TRAIN = os.path.join(BASE_DIR, "data", "indqel_labeled", "train_per_mention.tsv")

SUMMARY_CSV = os.path.join(BASE_DIR, "data", "mappings", "mentions_unlabeled_in_indqner.csv")
DETAIL_CSV = os.path.join(BASE_DIR, "reports", "unlabeled_mentions_instances.csv")

def main():
    print("Memuat dataset IndQNER train.txt...")
    tokens = []
    with open(INDQNER_TRAIN, mode="r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                parts = line.split("\t")
                if len(parts) == 2:
                    tokens.append((parts[0], parts[1]))

    token_words = [t[0] for t in tokens]
    token_tags = [t[1] for t in tokens]
    norm_tokens = [re.sub(r"[^\w]", "", w.lower()) for w in token_words]

    # Buat indeks kata untuk pencarian cepat
    word_index = defaultdict(list)
    for idx, nw in enumerate(norm_tokens):
        if nw:
            word_index[nw].append(idx)

    print(f"IndQNER dimuat: {len(tokens)} token.")

    # Baca data IndQEL yang sudah berlabel
    print("Menganalisis mention dari IndQEL train_per_mention.tsv...")
    indqel_rows = []
    with open(INDQEL_LABELED_TRAIN, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            m = row.get("mention", "").strip()
            l = row.get("label", "").strip()
            if m and l:
                indqel_rows.append(row)

    print(f"Total baris mention yang dianalisis: {len(indqel_rows)}")

    unlabeled_instances = []
    summary_dict = defaultdict(lambda: {
        "uri": "",
        "label": "",
        "locations": set(),
        "count": 0
    })

    already_labeled_count = 0
    not_in_train_split = 0

    for row in indqel_rows:
        m = row["mention"].strip()
        u = row["uri"].strip()
        l = row["label"].strip()
        s = int(row["surah_id"].strip())
        a = int(row["ayah"].strip())
        sentence = row["sentence"].strip()

        m_words = [re.sub(r"[^\w]", "", w.lower()) for w in m.split() if re.sub(r"[^\w]", "", w.lower())]
        if not m_words:
            continue

        candidate_indices = word_index.get(m_words[0], [])
        sent_words = [re.sub(r"[^\w]", "", w.lower()) for w in sentence.split() if re.sub(r"[^\w]", "", w.lower())]

        found_match = None
        for c_idx in candidate_indices:
            if norm_tokens[c_idx:c_idx + len(m_words)] == m_words:
                window = set(norm_tokens[max(0, c_idx - 25):min(len(norm_tokens), c_idx + 25 + len(m_words))])
                overlap = len(window.intersection(set(sent_words)))
                if overlap >= min(4, len(sent_words)):
                    found_match = list(range(c_idx, c_idx + len(m_words)))
                    break

        if found_match:
            tags = [token_tags[i] for i in found_match]
            # Jika semua token bernilai 'O', maka ini entitas yang terlewat di IndQNER!
            if all(t == "O" for t in tags):
                loc_str = f"{s}:{a}"
                summary_dict[(m, u)]["uri"] = u
                summary_dict[(m, u)]["label"] = l
                summary_dict[(m, u)]["locations"].add((s, a))
                summary_dict[(m, u)]["count"] += 1

                unlabeled_instances.append({
                    "surah_id": s,
                    "ayah": a,
                    "location": loc_str,
                    "mention": m,
                    "uri": u,
                    "label": l,
                    "original_ner_tags": " ".join(tags),
                    "sentence": sentence
                })
            else:
                already_labeled_count += 1
        else:
            not_in_train_split += 1

    print("\n--- STATISTIK IDENTIFIKASI ---")
    print(f"Mention sudah berlabel di IndQNER: {already_labeled_count}")
    print(f"Mention BELUM BERLABEL (Missing / 'O') di IndQNER: {len(unlabeled_instances)}")
    print(f"Mention di luar rentang train.txt IndQNER: {not_in_train_split}")
    print(f"Jumlah jenis mention unik yang terlewat: {len(summary_dict)}")

    # 1. Simpan berkas ringkasan (Summary)
    os.makedirs(os.path.dirname(SUMMARY_CSV), exist_ok=True)
    summary_rows = []
    # Urutkan berdasarkan missing_count tertinggi
    sorted_summary = sorted(summary_dict.items(), key=lambda x: x[1]["count"], reverse=True)

    for idx, ((m, u), data) in enumerate(sorted_summary, start=1):
        sorted_locs = sorted(data["locations"])
        locs_str = ", ".join([f"{s}:{a}" for s, a in sorted_locs])
        summary_rows.append({
            "no": idx,
            "mention": m,
            "uri": u,
            "label": data["label"],
            "missing_count": data["count"],
            "locations": locs_str
        })

    with open(SUMMARY_CSV, mode="w", encoding="utf-8", newline="") as f:
        fieldnames = ["no", "mention", "uri", "label", "missing_count", "locations"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"\nBerhasil menyimpan berkas rekapitulasi ke: {SUMMARY_CSV}")

    # 2. Simpan berkas rincian per kejadian (Detail Instances)
    os.makedirs(os.path.dirname(DETAIL_CSV), exist_ok=True)
    with open(DETAIL_CSV, mode="w", encoding="utf-8", newline="") as f:
        detail_fields = ["no", "surah_id", "ayah", "location", "mention", "uri", "label", "original_ner_tags", "sentence"]
        writer = csv.DictWriter(f, fieldnames=detail_fields)
        writer.writeheader()
        for idx, inst in enumerate(unlabeled_instances, start=1):
            inst_row = {"no": idx}
            inst_row.update(inst)
            writer.writerow(inst_row)

    print(f"Berhasil menyimpan rincian per kemunculan ke: {DETAIL_CSV}")

if __name__ == "__main__":
    main()
