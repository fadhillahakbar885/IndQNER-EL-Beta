"""
Script: 04_enrich_indqner_train.py
Deskripsi: Memperkaya dataset IndQNER train.txt menggunakan mention-mention dari
           IndQEL yang terbukti belum berlabel (missing entities / False Negatives),
           dengan menerapkan STRICT ZERO DELETION POLICY (preservasi 100% label asli).
           Juga menyalin dev.txt dan test.txt asli ke data/indqner_revised/ agar lengkap dan murni.
"""

import csv
import os
import re
import shutil
import sys
from collections import Counter

# Set UTF-8 encoding untuk Windows Console
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_NER_DIR = os.path.join(BASE_DIR, "IndQNER", "datasets")
REVISED_NER_DIR = os.path.join(BASE_DIR, "data", "indqner_revised")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

INDQEL_LABELED_TRAIN = os.path.join(BASE_DIR, "data", "indqel_labeled", "train_per_mention.tsv")
DIFF_LOG = os.path.join(REPORTS_DIR, "diff_inspection.log")

def main():
    os.makedirs(REVISED_NER_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print("=== TAHAP 1: PRESERVASI SPLIT EVALUASI (DEV & TEST) ===")
    for split_file in ["dev.txt", "test.txt"]:
        src_path = os.path.join(ORIGINAL_NER_DIR, split_file)
        dst_path = os.path.join(REVISED_NER_DIR, split_file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, dst_path)
            print(f"Disalin utuh (preservasi 100%): {split_file} -> {dst_path}")

    print("\n=== TAHAP 2: MEMUAT INDQNER TRAIN.TXT ASLI ===")
    train_src_path = os.path.join(ORIGINAL_NER_DIR, "train.txt")
    raw_lines = []
    tokens = []  # list of dict: {line_idx, word, tag, is_token}

    with open(train_src_path, mode="r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            raw_lines.append(line)
            stripped = line.strip()
            if not stripped:
                tokens.append({"line_idx": line_idx, "word": "", "tag": "", "is_token": False})
            else:
                parts = stripped.split("\t")
                if len(parts) == 2:
                    tokens.append({"line_idx": line_idx, "word": parts[0], "tag": parts[1], "is_token": True})
                else:
                    tokens.append({"line_idx": line_idx, "word": stripped, "tag": "O", "is_token": True})

    token_count = sum(1 for t in tokens if t["is_token"])
    print(f"IndQNER train.txt dimuat: {len(raw_lines)} baris ({token_count} token kata).")

    # Indeks token kata yang dinormalisasi untuk pencarian efisien
    norm_tokens = [re.sub(r"[^\w]", "", t["word"].lower()) if t["is_token"] else "" for t in tokens]
    word_index = {}
    for idx, nw in enumerate(norm_tokens):
        if nw:
            if nw not in word_index:
                word_index[nw] = []
            word_index[nw].append(idx)

    # Catat statistik tag sebelum pengayaan
    counter_before = Counter(t["tag"] for t in tokens if t["is_token"])

    print("\n=== TAHAP 3: MEMUAT MENTION INDQEL TRAIN ===")
    indqel_rows = []
    with open(INDQEL_LABELED_TRAIN, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            m = row.get("mention", "").strip()
            l = row.get("label", "").strip()
            if m and l:
                indqel_rows.append(row)

    print(f"Total baris mention berlabel di IndQEL train: {len(indqel_rows)}")

    print("\n=== TAHAP 4: PENCOCOKAN KONTEKSTUAL & PENGAYAAN ENTITAS ===")
    used_spans = set()
    enriched_spans = 0
    enriched_tokens = 0
    preserved_labeled = 0
    preserved_conflict = 0
    outside_train_split = 0
    diff_logs = []

    for row_idx, row in enumerate(indqel_rows):
        m = row["mention"].strip()
        l = row["label"].strip()
        s = row["surah_id"].strip()
        a = row["ayah"].strip()
        sentence = row["sentence"].strip()

        m_words = [re.sub(r"[^\w]", "", w.lower()) for w in m.split() if re.sub(r"[^\w]", "", w.lower())]
        if not m_words:
            continue

        sent_words = [re.sub(r"[^\w]", "", w.lower()) for w in sentence.split() if re.sub(r"[^\w]", "", w.lower())]
        candidate_indices = word_index.get(m_words[0], [])

        # Cari semua kemunculan yang urutan katanya sama persis
        candidates = []
        for c_idx in candidate_indices:
            if norm_tokens[c_idx:c_idx + len(m_words)] == m_words:
                window = set(norm_tokens[max(0, c_idx - 30):min(len(norm_tokens), c_idx + 30 + len(m_words))])
                overlap = len(window.intersection(set(sent_words)))
                candidates.append((c_idx, overlap))

        # Urutkan berdasarkan skor tumpang-tindih (overlap) tertinggi
        candidates.sort(key=lambda x: x[1], reverse=True)

        chosen = None
        for c_idx, score in candidates:
            # Overlap minimal 5 kata atau minimal 30% dari panjang kalimat ayat
            if score >= min(5, len(sent_words)) and score >= len(sent_words) * 0.25:
                span_tuple = (c_idx, c_idx + len(m_words))
                if span_tuple not in used_spans:
                    chosen = (c_idx, score)
                    break

        if chosen:
            c_idx, score = chosen
            span_indices = list(range(c_idx, c_idx + len(m_words)))
            current_tags = [tokens[i]["tag"] for i in span_indices]
            words_str = " ".join([tokens[i]["word"] for i in span_indices])

            # KASUS A: Seluruh token berstatus 'O' (Missing Entity -> DIPERKAYA!)
            if all(t == "O" for t in current_tags):
                used_spans.add((c_idx, c_idx + len(m_words)))
                new_tags = []
                for idx_in_span, tok_idx in enumerate(span_indices):
                    prefix = "B-" if idx_in_span == 0 else "I-"
                    new_tag = f"{prefix}{l}"
                    tokens[tok_idx]["tag"] = new_tag
                    new_tags.append(new_tag)
                    enriched_tokens += 1

                enriched_spans += 1
                diff_logs.append(
                    f"[ENRICHED] Surah {s}:{a} | Token #{c_idx} | Text: '{words_str}' | Tags: {current_tags} -> {new_tags}"
                )

            # KASUS B: Seluruh token sudah memiliki label entitas (Zero Deletion / Dipertahankan)
            elif all(t != "O" for t in current_tags):
                used_spans.add((c_idx, c_idx + len(m_words)))
                preserved_labeled += 1

            # KASUS C: Konflik parsial (sebagian sudah berlabel, sebagian O)
            else:
                preserved_conflict += 1
                diff_logs.append(
                    f"[CONFLICT_PRESERVED] Surah {s}:{a} | Token #{c_idx} | Text: '{words_str}' | Tags Lama: {current_tags} (Preserved)"
                )
        else:
            outside_train_split += 1

    print("\n=== TAHAP 5: MENYIMPAN HASIL REVISI KE DATA/INDQNER_REVISED/ ===")
    train_dst_path = os.path.join(REVISED_NER_DIR, "train.txt")
    counter_after = Counter(t["tag"] for t in tokens if t["is_token"])

    with open(train_dst_path, mode="w", encoding="utf-8") as f:
        for t in tokens:
            if t["is_token"]:
                f.write(f"{t['word']}\t{t['tag']}\n")
            else:
                f.write("\n")

    print(f"Berkas revisi berhasil ditulis: {train_dst_path}")

    # Simpan log perbedaan lengkap
    with open(DIFF_LOG, mode="w", encoding="utf-8") as f:
        f.write("====================================================================\n")
        f.write("LOG AUDIT PENGAYAAN INDQNER TRAIN.TXT DENGAN MENTION INDQEL\n")
        f.write("====================================================================\n\n")
        f.write(f"Total Span Entitas Baru Diperkaya        : {enriched_spans}\n")
        f.write(f"Total Token Diperkaya (dari 'O' ke Label): {enriched_tokens}\n")
        f.write(f"Total Mention Sudah Berlabel (Preserved) : {preserved_labeled}\n")
        f.write(f"Total Konflik Parsial (Preserved)        : {preserved_conflict}\n")
        f.write(f"Total di Luar Rentang Split train.txt    : {outside_train_split}\n\n")
        f.write("--- RINCIAN SETIAP SPAN YANG DIPERKAYA ---\n")
        f.write("\n".join(diff_logs))

    print(f"Log audit detail disimpan di: {DIFF_LOG}")

    print("\n=== RINGKASAN HASIL PENGAYAAN ===")
    print(f"Total Entitas Mention Baru yang Ditambahkan (Span) : {enriched_spans}")
    print(f"Total Token yang Berubah dari 'O' ke Label         : {enriched_tokens}")
    print(f"Label Asli yang Dipertahankan (Preserved)          : {preserved_labeled}")
    print(f"Konflik Parsial Dipertahankan (Strict Zero Del)    : {preserved_conflict}")

    print("\nPerbandingan Frekuensi Tag Sebelum vs Sesudah:")
    all_classes = sorted(set(list(counter_before.keys()) + list(counter_after.keys())))
    for cls in all_classes:
        if cls != "O":
            before = counter_before[cls]
            after = counter_after[cls]
            diff = after - before
            if diff > 0:
                print(f"  + {cls:<25}: {before:>4} -> {after:>4} (+{diff})")
            else:
                print(f"    {cls:<25}: {before:>4} -> {after:>4} (tetap)")
    print(f"  - {'O (Non-entity)':<25}: {counter_before['O']:>4} -> {counter_after['O']:>4} (-{counter_before['O'] - counter_after['O']})")

if __name__ == "__main__":
    main()
