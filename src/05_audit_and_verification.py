"""
Script: 05_audit_and_verification.py
Deskripsi: Melakukan audit matematis dan verifikasi integritas penuh antara
           dataset asli (IndQNER/datasets/) dengan dataset hasil revisi (data/indqner_revised/).
           Menguji dan membuktikan:
           1. STRICT ZERO DELETION GUARANTEE (0 label ground-truth yang terhapus/berubah).
           2. Preservasi token kata 100% (tidak ada penambahan/pengurangan token kata).
           3. Validitas skema penandaan BIO (tidak ada invalid transition).
           4. Kemurnian split dev.txt dan test.txt (100% identik).
           5. Menghasilkan laporan Markdown komprehensif di reports/stats_enrichment_summary.md.
"""

import hashlib
import os
import sys
from collections import Counter, defaultdict

# Set UTF-8 encoding untuk Windows Console
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL_DIR = os.path.join(BASE_DIR, "IndQNER", "datasets")
REVISED_DIR = os.path.join(BASE_DIR, "data", "indqner_revised")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

SUMMARY_MD = os.path.join(REPORTS_DIR, "stats_enrichment_summary.md")
AUDIT_LOG = os.path.join(REPORTS_DIR, "audit_verification.log")

def get_file_md5(filepath):
    hasher = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def audit_file_pair(orig_path, rev_path, split_name):
    print(f"\n=======================================================")
    print(f"AUDIT INTEGRITAS SPLIT: {split_name.upper()}")
    print(f"=======================================================")
    
    with open(orig_path, mode="r", encoding="utf-8") as f:
        orig_lines = f.readlines()
        
    with open(rev_path, mode="r", encoding="utf-8") as f:
        rev_lines = f.readlines()
        
    total_orig_lines = len(orig_lines)
    total_rev_lines = len(rev_lines)
    
    print(f"Jumlah Baris Asli   : {total_orig_lines:,}")
    print(f"Jumlah Baris Revisi : {total_rev_lines:,}")
    
    assert total_orig_lines == total_rev_lines, f"ERROR: Jumlah baris berbeda pada {split_name}!"
    print("  [PASSED] Jumlah baris identik 100%.")

    orig_tokens = []
    rev_tokens = []
    
    deleted_labels = []
    mutated_labels = []
    word_mismatches = []
    enriched_from_o = []
    
    for idx, (o_line, r_line) in enumerate(zip(orig_lines, rev_lines), start=1):
        o_strip = o_line.strip()
        r_strip = r_line.strip()
        
        # Cek baris kosong pemisah kalimat
        if not o_strip and not r_strip:
            continue
        elif not o_strip or not r_strip:
            raise AssertionError(f"Baris kosong tidak cocok pada line {idx}!")
            
        o_parts = o_strip.split("\t")
        r_parts = r_strip.split("\t")
        
        o_word = o_parts[0]
        o_tag = o_parts[1] if len(o_parts) > 1 else "O"
        
        r_word = r_parts[0]
        r_tag = r_parts[1] if len(r_parts) > 1 else "O"
        
        if o_word != r_word:
            word_mismatches.append((idx, o_word, r_word))
            
        orig_tokens.append((o_word, o_tag))
        rev_tokens.append((r_word, r_tag))
        
        if o_tag != r_tag:
            if o_tag != "O" and r_tag == "O":
                deleted_labels.append((idx, o_word, o_tag, r_tag))
            elif o_tag != "O" and r_tag != "O" and o_tag != r_tag:
                mutated_labels.append((idx, o_word, o_tag, r_tag))
            elif o_tag == "O" and r_tag != "O":
                enriched_from_o.append((idx, o_word, o_tag, r_tag))

    # Verifikasi kata tidak berubah
    assert len(word_mismatches) == 0, f"ERROR: Ditemukan {len(word_mismatches)} kata yang tidak cocok!"
    print("  [PASSED] 100% kata/token tidak mengalami perubahan sedikitpun.")

    # Verifikasi STRICT ZERO DELETION
    assert len(deleted_labels) == 0, f"PELANGGARAN ZERO DELETION: {len(deleted_labels)} label ground truth terhapus!"
    print(f"  [PASSED] STRICT ZERO DELETION: 0 label ground-truth yang terhapus.")

    assert len(mutated_labels) == 0, f"PELANGGARAN ZERO MODIFICATION: {len(mutated_labels)} label ground truth diubah!"
    print(f"  [PASSED] STRICT PRESERVATION: 0 label entitas asli yang tertimpa label lain.")

    print(f"  [STATUS] Token berhasil diperkaya dari 'O' ke Label Entitas: {len(enriched_from_o):,}")
    
    # Validasi Skema BIO (cek I- tag liar)
    bio_errors = []
    prev_tag = "O"
    for idx, (word, tag) in enumerate(rev_tokens, start=1):
        if tag.startswith("I-"):
            cls = tag[2:]
            valid_prev = {f"B-{cls}", f"I-{cls}"}
            if prev_tag not in valid_prev:
                bio_errors.append((idx, word, tag, prev_tag))
        prev_tag = tag
        
    assert len(bio_errors) == 0, f"ERROR BIO TAGGING: Ditemukan {len(bio_errors)} tag I- tanpa B-!"
    print(f"  [PASSED] Skema BIO valid 100%: Tidak ada tag 'I-' yang yatim/invalid.")

    return {
        "split": split_name,
        "total_lines": total_orig_lines,
        "total_tokens": len(orig_tokens),
        "deleted_labels": len(deleted_labels),
        "mutated_labels": len(mutated_labels),
        "enriched_tokens": len(enriched_from_o),
        "orig_counter": Counter(t[1] for t in orig_tokens),
        "rev_counter": Counter(t[1] for t in rev_tokens),
        "enriched_items": enriched_from_o
    }

def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print("=======================================================")
    print("MEMULAI AUDIT DAN VERIFIKASI INTEGRITAS DATASET")
    print("=======================================================")

    # 1. Audit dev.txt dan test.txt (Harus 100% Identik bit-by-bit)
    dev_orig = os.path.join(ORIGINAL_DIR, "dev.txt")
    dev_rev = os.path.join(REVISED_DIR, "dev.txt")
    dev_orig_md5 = get_file_md5(dev_orig)
    dev_rev_md5 = get_file_md5(dev_rev)
    assert dev_orig_md5 == dev_rev_md5, "ERROR: dev.txt mengalami perubahan!"
    print(f"\n[VALIDASI DEV] MD5 Asli ({dev_orig_md5}) == Revisi ({dev_rev_md5}) -> 100% IDENTIK!")

    test_orig = os.path.join(ORIGINAL_DIR, "test.txt")
    test_rev = os.path.join(REVISED_DIR, "test.txt")
    test_orig_md5 = get_file_md5(test_orig)
    test_rev_md5 = get_file_md5(test_rev)
    assert test_orig_md5 == test_rev_md5, "ERROR: test.txt mengalami perubahan!"
    print(f"[VALIDASI TEST] MD5 Asli ({test_orig_md5}) == Revisi ({test_rev_md5}) -> 100% IDENTIK!")

    # 2. Audit train.txt
    train_orig = os.path.join(ORIGINAL_DIR, "train.txt")
    train_rev = os.path.join(REVISED_DIR, "train.txt")
    train_stats = audit_file_pair(train_orig, train_rev, "train")

    # 3. Tulis Laporan Rinci ke Markdown
    orig_c = train_stats["orig_counter"]
    rev_c = train_stats["rev_counter"]
    all_tags = sorted(set(list(orig_c.keys()) + list(rev_c.keys())))

    # Hitung entity mentions (span B-*)
    orig_entities = sum(v for k, v in orig_c.items() if k.startswith("B-"))
    rev_entities = sum(v for k, v in rev_c.items() if k.startswith("B-"))
    added_entities = rev_entities - orig_entities

    with open(SUMMARY_MD, mode="w", encoding="utf-8") as f:
        f.write("# Laporan Audit dan Statistik Pengayaan Dataset IndQNER\n\n")
        f.write("> **Status Integritas**: **100% TERVERIFIKASI (PASSED)**  \n")
        f.write("> **Strict Zero Deletion**: **0 Label Terhapus / 0 Label Tertimpa**  \n")
        f.write("> **Preservasi Split Dev & Test**: **100% Murni (Identik Bit-by-Bit)**\n\n")
        f.write("---\n\n")

        f.write("## 1. Ringkasan Eksekutif Perubahan Dataset\n\n")
        f.write("| Metrik Dataset | IndQNER Asli (`train.txt`) | IndQNER Revisi (`train.txt`) | Perubahan (Delta) | Catatan Integritas |\n")
        f.write("| :--- | :---: | :---: | :---: | :--- |\n")
        f.write(f"| **Total Baris File** | {train_stats['total_lines']:,} | {train_stats['total_lines']:,} | 0 | Identik 100% |\n")
        f.write(f"| **Total Token Kata** | {train_stats['total_tokens']:,} | {train_stats['total_tokens']:,} | 0 | Preservasi korpus |\n")
        f.write(f"| **Total Entitas (Span `B-*`)** | {orig_entities:,} | {rev_entities:,} | **+{added_entities:,}** | Entitas baru terinjeksi |\n")
        f.write(f"| **Total Token Berlabel Entitas** | {sum(v for k, v in orig_c.items() if k != 'O'):,} | {sum(v for k, v in rev_c.items() if k != 'O'):,} | **+{train_stats['enriched_tokens']:,}** | Mutasi dari tag `O` |\n")
        f.write(f"| **Token Non-Entitas (`O`)** | {orig_c['O']:,} | {rev_c['O']:,} | **-{train_stats['enriched_tokens']:,}** | Berkurang proporsional |\n")
        f.write(f"| **Label Ground-Truth Terhapus** | 0 | 0 | **0** | **Strict Zero Deletion Guaranteed** |\n")
        f.write(f"| **Label Ground-Truth Tertimpa** | 0 | 0 | **0** | **Strict Preservation Guaranteed** |\n\n")

        f.write("## 2. Perbandingan Frekuensi Tag Per Kelas Entitas\n\n")
        f.write("| Label / Kelas Entitas | Frekuensi Asli | Frekuensi Revisi | Delta (Penambahan) | Persentase Kenaikan |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: |\n")

        for tag in all_tags:
            if tag == "O":
                continue
            o_cnt = orig_c[tag]
            r_cnt = rev_c[tag]
            delta = r_cnt - o_cnt
            pct = f"+{(delta / o_cnt * 100):.1f}%" if o_cnt > 0 and delta > 0 else ("0.0%" if delta == 0 else "Baru")
            delta_str = f"**+{delta}**" if delta > 0 else "0"
            f.write(f"| `{tag}` | {o_cnt:,} | {r_cnt:,} | {delta_str} | {pct} |\n")

        f.write(f"| `O` (Non-Entity) | {orig_c['O']:,} | {rev_c['O']:,} | **-{train_stats['enriched_tokens']}** | -{(train_stats['enriched_tokens'] / orig_c['O'] * 100):.2f}% |\n\n")

        f.write("## 3. Verifikasi Kemurnian Split Evaluasi (`dev.txt` & `test.txt`)\n\n")
        f.write("| File Split | MD5 Checksum Asli | MD5 Checksum Revisi | Status Integritas |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        f.write(f"| `dev.txt` | `{dev_orig_md5}` | `{dev_rev_md5}` | ✅ 100% Identik (Tidak dimodifikasi) |\n")
        f.write(f"| `test.txt` | `{test_orig_md5}` | `{test_rev_md5}` | ✅ 100% Identik (Tidak dimodifikasi) |\n\n")

        f.write("## 4. Log Sampel Token yang Berhasil Diperkaya\n\n")
        f.write("| No | Baris Line | Kata / Token | Tag Asli | Tag Revisi |\n")
        f.write("| :-: | :-: | :--- | :-: | :-: |\n")
        for idx, (l_no, w, ot, rt) in enumerate(train_stats["enriched_items"][:25], start=1):
            f.write(f"| {idx} | {l_no:,} | **{w}** | `{ot}` | `{rt}` |\n")
        if len(train_stats["enriched_items"]) > 25:
            f.write(f"| ... | ... | *(Total {len(train_stats['enriched_items'])} token diperkaya)* | ... | ... |\n")

    print(f"\nLaporan Markdown lengkap berhasil dibuat di: {SUMMARY_MD}")

    # Tulis Audit Log
    with open(AUDIT_LOG, mode="w", encoding="utf-8") as f:
        f.write("AUDIT VERIFICATION FULL LOG\n")
        f.write("===========================\n")
        f.write(f"Total Enriched Tokens: {len(train_stats['enriched_items'])}\n")
        for l_no, w, ot, rt in train_stats["enriched_items"]:
            f.write(f"Line {l_no}: '{w}' | {ot} -> {rt}\n")

    print(f"Log rincian audit disimpan di: {AUDIT_LOG}")

if __name__ == "__main__":
    main()
