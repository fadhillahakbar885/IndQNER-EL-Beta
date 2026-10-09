import csv
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

verses = {}
with open('data/indqel_labeled/train_per_mention.tsv', encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        key = (int(r['surah_id']), int(r['ayah']))
        if key not in verses:
            verses[key] = r['sentence'].strip()

tokens = []
with open('IndQNER/datasets/train.txt', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '\t' in line:
            tokens.append(line.split('\t')[0])

clean_tokens = [re.sub(r'[^\w]', '', w.lower()) for w in tokens]
clean_str = ' '.join(clean_tokens)

for (s, a), sent_text in list(verses.items())[:15]:
    sent_words = [re.sub(r'[^\w]', '', w.lower()) for w in sent_text.split() if re.sub(r'[^\w]', '', w.lower())]
    sub = ' '.join(sent_words[:4])
    is_in = sub in clean_str
    print(f'Surah {s}:{a} | sub: "{sub}" | in_train: {is_in}')
