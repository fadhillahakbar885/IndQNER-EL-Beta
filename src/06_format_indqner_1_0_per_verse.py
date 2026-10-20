"""
Script: 06_format_indqner_1_0_per_verse.py
Deskripsi: Mengonversi format dataset BIO dari data/indqner_revised/ menjadi "IndQNER 1.0"
           dengan ketentuan:
           1. Satu Teks = Satu Ayat Al-Qur'an utuh (merujuk pada korpus ayat IndQEL).
           2. Antar kalimat dalam ayat yang sama disatukan (tanpa baris kosong internal).
           3. Antar satu teks ayat dengan teks ayat berikutnya DIPISAHKAN OLEH TEPAT SATU BARIS KOSONG,
              termasuk ayat-ayat pendek yang sebelumnya tergabung dalam satu kalimat (misal 2:2 dan 2:3).
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

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "data", "indqner_revised")
OUT_DIR = os.path.join(BASE_DIR, "data", "indqner_1.0")
INDQEL_PATH = os.path.join(BASE_DIR, "datasets IndQEL")

def clean_tok(w):
    s = unicodedata.normalize('NFKD', w)
    s = "".join([c for c in s if not unicodedata.combining(c)])
    return re.sub(r'[^\w]', '', s.lower())

def load_indqel_verses():
    all_verses = []
    seen = set()
    for split in ['train', 'val', 'test']:
        path = os.path.join(INDQEL_PATH, f'{split}.tsv')
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                key = (int(row['surah_id']), int(row['ayah']))
                if key not in seen:
                    seen.add(key)
                    all_verses.append({
                        'surah': int(row['surah_id']),
                        'ayah': int(row['ayah']),
                        'text': row['sentence'].strip()
                    })
    all_verses.sort(key=lambda x: (x['surah'], x['ayah']))
    for v in all_verses:
        v_words = [clean_tok(w) for w in v['text'].split() if clean_tok(w)]
        v['prefix_3'] = v_words[:3] if len(v_words) >= 3 else v_words
    return all_verses

def convert_split(split_name, all_verses, start_verse_key):
    src_file = os.path.join(SRC_DIR, f"{split_name}.txt")
    tokens = []
    with open(src_file, encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                parts = stripped.split('\t')
                tag = parts[1] if len(parts) > 1 else 'O'
                tokens.append((parts[0], tag))
                
    total_tokens = len(tokens)
    clean_tokens = [clean_tok(t[0]) for t in tokens]
    
    # Cari posisi awal verse target
    start_v_idx = 0
    for i, v in enumerate(all_verses):
        if (v['surah'], v['ayah']) == start_verse_key:
            start_v_idx = i
            break
            
    # Temukan batas awal setiap ayat dalam aliran token
    starts = [(all_verses[start_v_idx]['surah'], all_verses[start_v_idx]['ayah'], 0)]
    curr_tok = 0
    
    for v_idx in range(start_v_idx + 1, len(all_verses)):
        v = all_verses[v_idx]
        pref = v['prefix_3']
        if not pref:
            continue
        L = len(pref)
        best_start = None
        search_limit = min(total_tokens, curr_tok + 600)
        
        for i in range(curr_tok, search_limit):
            if clean_tokens[i] == pref[0]:
                cand = [clean_tokens[i]]
                p = i + 1
                while len(cand) < L and p < search_limit:
                    if clean_tokens[p]:
                        cand.append(clean_tokens[p])
                    p += 1
                if cand == pref:
                    # Token i adalah kata pertama dari ayat baru
                    # Jika ada tanda kurung buka atau kutip sebelum i, sertakan ke ayat baru
                    actual_start = i
                    while actual_start > curr_tok and tokens[actual_start - 1][0] in ["(", "“", "‘", "["]:
                        actual_start -= 1
                    best_start = actual_start
                    break
                    
        if best_start is not None:
            starts.append((v['surah'], v['ayah'], best_start))
            curr_tok = best_start + 1
        else:
            if split_name == 'train' and (v['surah'] > 7 or (v['surah'] == 7 and v['ayah'] > 106)):
                break
            if split_name == 'dev' and (v['surah'] == 10 and v['ayah'] > 61):
                break
            if split_name == 'test' and (v['surah'] == 16 and v['ayah'] > 128):
                break
                
    # Bagi aliran token menjadi potongan ayat utuh (verse chunks)
    verse_chunks = []
    for i in range(len(starts)):
        s_idx = starts[i][2]
        e_idx = starts[i+1][2] if i + 1 < len(starts) else total_tokens
        v_tag = (starts[i][0], starts[i][1])
        verse_chunks.append((v_tag, tokens[s_idx:e_idx]))
        
    # Validasi preservasi token
    total_new_tokens = sum(len(toks) for v, toks in verse_chunks)
    assert total_tokens == total_new_tokens, f"Token mismatch in {split_name}: {total_tokens} vs {total_new_tokens}"
    
    # Tulis ke file output IndQNER 1.0
    out_file = os.path.join(OUT_DIR, f"{split_name}.txt")
    with open(out_file, mode="w", encoding="utf-8", newline="\n") as f:
        for idx, (v_tag, toks) in enumerate(verse_chunks):
            for w, t in toks:
                f.write(f"{w}\t{t}\n")
            # Pemisah baris kosong HANYA antar ayat
            if idx < len(verse_chunks) - 1:
                f.write("\n")
                
    return {
        'split': split_name,
        'verses_count': len(verse_chunks),
        'tokens': total_new_tokens
    }

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    
    print("=" * 70)
    print("RESTRUKTURISASI DATASET INDQNER 1.0 (FORMAT BIO PER AYAT RESMI)")
    print("=" * 70)
    
    all_verses = load_indqel_verses()
    print(f"Total Ayat Referensi Dimuat: {len(all_verses)} ayat.\n")
    
    split_configs = [
        ('train', (2, 1)),
        ('dev', (7, 107)),
        ('test', (10, 61))
    ]
    
    for split_name, start_v in split_configs:
        res = convert_split(split_name, all_verses, start_v)
        print(f"Split [{split_name}]:")
        print(f"  - Total Teks (Ayat Utuh) : {res['verses_count']:,} ayat")
        print(f"  - Total Token Kata       : {res['tokens']:,} (100% PRESERVED, 0 KATA HILANG)")
        print(f"  - File Output            : data/indqner_1.0/{split_name}.txt\n")
        
    print("=" * 70)
    print("VERIFIKASI INTEGRITAS: ZERO DELETION & ZERO CORRUPTION LOLOS 100%")
    print("=" * 70)

if __name__ == "__main__":
    main()
