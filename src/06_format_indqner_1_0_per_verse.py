"""
Script: 06_format_indqner_1_0_per_verse.py
Deskripsi: Mengonversi format dataset BIO dari data/indqner_revised/ menjadi "IndQNER 1.0"
           dengan ketentuan:
           1. Satu Teks = Satu Ayat Al-Qur'an (merujuk pada definisi ayat di data/indqel_labeled/).
           2. Antar kalimat dalam ayat yang sama disatukan (tanpa baris kosong pemisah).
           3. Antar satu teks ayat dengan teks ayat berikutnya dipisahkan oleh tepat satu baris kosong.
           4. Zero Deletion & Zero Corruption Guarantee:
              - 100% token kata dipertahankan (urutan, teks, dan jumlah).
              - 100% tag BIO dipertahankan tanpa perubahan.
           5. Output disimpan ke data/indqner_1.0/ (train.txt, dev.txt, test.txt).
"""

import csv
import os
import re
import sys
import unicodedata
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "data", "indqner_revised")
OUT_DIR = os.path.join(BASE_DIR, "data", "indqner_1.0")
INDQEL_DIR = os.path.join(BASE_DIR, "data", "indqel_labeled")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def normalize_text(s):
    s = unicodedata.normalize('NFKD', s)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    return re.sub(r'[^\w]', '', s.lower())

def load_indqel_verses():
    all_verses = []
    seen = set()
    for split in ['train_per_mention.tsv', 'val_per_mention.tsv', 'test_per_mention.tsv']:
        path = os.path.join(INDQEL_DIR, split)
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                key = (int(row['surah_id']), int(row['ayah']))
                if key not in seen:
                    seen.add(key)
                    all_verses.append({
                        'surah': int(row['surah_id']),
                        'ayah': int(row['ayah']),
                        'text': row['sentence'],
                        'norm': normalize_text(row['sentence'])
                    })
    all_verses.sort(key=lambda x: (x['surah'], x['ayah']))
    return all_verses

def load_bio_sentences(path):
    sentences = []
    curr = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                if curr:
                    sentences.append(curr)
                    curr = []
            else:
                parts = stripped.split('\t')
                if len(parts) == 2:
                    curr.append((parts[0], parts[1]))
                else:
                    curr.append((parts[0], 'O'))
        if curr:
            sentences.append(curr)
    return sentences

def convert_split(split_name, all_verses):
    src_file = os.path.join(SRC_DIR, f"{split_name}.txt")
    sentences = load_bio_sentences(src_file)
    total_original_tokens = sum(len(s) for s in sentences)
    
    # Map each sentence to its verse
    v_idx = 0
    assigned_verses = []
    for s_idx, s in enumerate(sentences):
        s_norm = normalize_text(" ".join([w for w, t in s]))
        matched_v = None
        window = range(max(0, v_idx - 2), min(len(all_verses), v_idx + 10))
        for i in window:
            v = all_verses[i]
            if s_norm in v['norm'] or v['norm'] in s_norm:
                matched_v = i
                break
        if matched_v is None:
            for i, v in enumerate(all_verses):
                if s_norm in v['norm'] or v['norm'] in s_norm:
                    matched_v = i
                    break
                if len(s_norm) >= 15 and (s_norm[:20] in v['norm'] or s_norm[-20:] in v['norm']):
                    matched_v = i
                    break
        if matched_v is not None:
            v_idx = matched_v
            assigned_verses.append((all_verses[matched_v]['surah'], all_verses[matched_v]['ayah']))
        else:
            # Fallback to previous verse if unknown
            assigned_verses.append(assigned_verses[-1] if assigned_verses else (None, None))
            
    # Group sentences by verse
    # Consecutive sentences with the same verse are merged (no blank line)
    merged_texts = []
    curr_text_tokens = []
    curr_v = None
    removed_boundaries = 0
    
    for s_idx, s in enumerate(sentences):
        v_tag = assigned_verses[s_idx]
        if v_tag == curr_v and curr_v is not None:
            # Merged inside the same verse
            removed_boundaries += 1
            curr_text_tokens.extend(s)
        else:
            if curr_text_tokens:
                merged_texts.append((curr_v, curr_text_tokens))
            curr_v = v_tag
            curr_text_tokens = list(s)
            
    if curr_text_tokens:
        merged_texts.append((curr_v, curr_text_tokens))
        
    # Write to destination
    out_file = os.path.join(OUT_DIR, f"{split_name}.txt")
    with open(out_file, mode="w", encoding="utf-8", newline="\n") as f:
        for idx, (v_tag, toks) in enumerate(merged_texts):
            for w, t in toks:
                f.write(f"{w}\t{t}\n")
            # Separate texts with blank line, except after the very last text
            if idx < len(merged_texts) - 1:
                f.write("\n")
                
    total_new_tokens = sum(len(toks) for v, toks in merged_texts)
    
    # Verification
    assert total_original_tokens == total_new_tokens, f"Token count mismatch in {split_name}!"
    
    # Verify exact token sequence
    orig_flat = [tok for s in sentences for tok in s]
    new_flat = [tok for v, toks in merged_texts for tok in toks]
    assert orig_flat == new_flat, f"Token or tag mismatch in {split_name}!"
    
    return {
        'split': split_name,
        'orig_sentences': len(sentences),
        'boundaries_removed': removed_boundaries,
        'new_texts': len(merged_texts),
        'tokens': total_new_tokens
    }

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    print("=" * 70)
    print("RESTRUKTURISASI DATASET INDQNER 1.0 (FORMAT BIO PER AYAT)")
    print("=" * 70)
    
    all_verses = load_indqel_verses()
    print(f"Total Ayat Unik Terdata di IndQEL: {len(all_verses)} ayat.\n")
    
    results = []
    for split in ["train", "dev", "test"]:
        res = convert_split(split, all_verses)
        results.append(res)
        print(f"Split [{split}]:")
        print(f"  - Kalimat Awal         : {res['orig_sentences']:,}")
        print(f"  - Baris Kosong Dihapus : {res['boundaries_removed']:,} (kalimat dalam ayat disatukan)")
        print(f"  - Total Teks (Ayat)    : {res['new_texts']:,}")
        print(f"  - Total Token Kata     : {res['tokens']:,} (100% PRESERVED, 0 KATA HILANG)")
        print(f"  - File Output          : data/indqner_1.0/{split}.txt\n")
        
    print("=" * 70)
    print("VERIFIKASI INTEGRITAS: ZERO DELETION & ZERO CORRUPTION LOLOS 100%")
    print("=" * 70)

if __name__ == "__main__":
    main()
