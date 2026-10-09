import csv
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. Baca semua token dan tag dari IndQNER train.txt
tokens = []
current_sent = []
sentences = []

with open('IndQNER/datasets/train.txt', mode='r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            if current_sent:
                sentences.append(current_sent)
                current_sent = []
        else:
            parts = line.split('\t')
            if len(parts) == 2:
                tok = (parts[0], parts[1], len(tokens))
                tokens.append(tok)
                current_sent.append(tok)
    if current_sent:
        sentences.append(current_sent)

print(f"Loaded {len(tokens)} tokens across {len(sentences)} sentences from IndQNER train.txt")

# Buat teks kontinu dari token IndQNER dengan pencatatan index token
token_words = [t[0] for t in tokens]
token_tags = [t[1] for t in tokens]

# Normalisasi token untuk pencarian cepat
norm_tokens = [re.sub(r'[^\w]', '', w.lower()) for w in token_words]

# Bangun index kata untuk pencarian cepat: word -> list of token indices
word_index = {}
for idx, nw in enumerate(norm_tokens):
    if nw:
        if nw not in word_index:
            word_index[nw] = []
        word_index[nw].append(idx)

print(f"Unique normalized words in index: {len(word_index)}")

# 2. Baca baris IndQEL train_per_mention.tsv
indqel_rows = []
with open('data/indqel_labeled/train_per_mention.tsv', mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        m = row['mention'].strip()
        u = row['uri'].strip()
        l = row['label'].strip()
        s = row['surah_id'].strip()
        a = row['ayah'].strip()
        sent = row['sentence'].strip()
        if m and l:
            indqel_rows.append({
                'surah': int(s),
                'ayah': int(a),
                'mention': m,
                'uri': u,
                'label': l,
                'sentence': sent
            })

print(f"Loaded {len(indqel_rows)} labeled mention rows from IndQEL train")

# 3. Cari kemunculan setiap mention dalam teks ayat pada token IndQNER
already_labeled = 0
unlabeled_in_ner = 0
not_found = 0

sample_unlabeled = []

for r in indqel_rows:
    m = r['mention']
    m_words = [re.sub(r'[^\w]', '', w.lower()) for w in m.split() if re.sub(r'[^\w]', '', w.lower())]
    if not m_words:
        continue

    # Cari kandidat posisi awal mention
    first_w = m_words[0]
    candidate_indices = word_index.get(first_w, [])

    # Filter kandidat: harus berada di dalam konteks kalimat ayat tersebut
    found_match = None
    sent_words = [re.sub(r'[^\w]', '', w.lower()) for w in r['sentence'].split() if re.sub(r'[^\w]', '', w.lower())]
    # Ambil 3 kata unik sebelum / sesudah untuk memastikan konteks ayat yang benar
    
    for c_idx in candidate_indices:
        # Cek apakah sequence m_words cocok
        if norm_tokens[c_idx:c_idx + len(m_words)] == m_words:
            # Cek konteks jendela 30 token sekitar c_idx
            window = set(norm_tokens[max(0, c_idx - 25):min(len(norm_tokens), c_idx + 25 + len(m_words))])
            # Hitung overlap dengan kata kalimat ayat
            overlap = len(window.intersection(set(sent_words)))
            if overlap >= min(4, len(sent_words)):
                found_match = list(range(c_idx, c_idx + len(m_words)))
                break

    if found_match:
        # Periksa tag di IndQNER
        tags = [token_tags[i] for i in found_match]
        if all(t == 'O' for t in tags):
            unlabeled_in_ner += 1
            if len(sample_unlabeled) < 5:
                sample_unlabeled.append((r['surah'], r['ayah'], m, r['label'], tags))
        else:
            already_labeled += 1
    else:
        not_found += 1

print("\n--- HASIL PENELUSURAN ALIGNMENT ---")
print(f"Total Mention Diproses: {len(indqel_rows)}")
print(f"Sudah Berlabel di IndQNER: {already_labeled}")
print(f"BELUM BERLABEL di IndQNER (Status 'O' / Missing): {unlabeled_in_ner}")
print(f"Tidak Ditemukan di train.txt IndQNER (di luar split): {not_found}")

print("\nContoh Mention yang BELUM BERLABEL di IndQNER:")
for s, a, m, l, tags in sample_unlabeled:
    print(f"  - Surah {s}:{a} | Mention: '{m}' | Label Target: {l} | Tag Asli IndQNER: {tags}")
