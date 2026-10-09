"""
Script: 01_extract_unique_mentions.py
Deskripsi: Mengekstrak seluruh kombinasi unik (mention, uri) dari ketiga file
           dataset IndQEL (train, val, test per_mention.tsv), menghitung frekuensi
           kemunculan, serta memberikan usulan awal kelas IndQNER sesuai konvensi
           anotasi dataset aslinya.
"""

import csv
import os
import re
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDQEL_DIR = os.path.join(BASE_DIR, "datasets IndQEL")
MAPPINGS_DIR = os.path.join(BASE_DIR, "data", "mappings")
OUTPUT_CSV = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping.csv")

FILES = {
    "train": os.path.join(INDQEL_DIR, "train_per_mention.tsv"),
    "val": os.path.join(INDQEL_DIR, "val_per_mention.tsv"),
    "test": os.path.join(INDQEL_DIR, "test_per_mention.tsv"),
}

def propose_initial_label(mention: str, uri: str) -> str:
    """Pemetaan berbasis ontologi dan pola terverifikasi dari dataset IndQNER asli."""
    m_lower = mention.lower().strip()
    u = uri.strip()

    # 1. Allah & Asmaul Husna / Sifat
    if u == "http://www.wikidata.org/entity/Q2095353" or m_lower in ["allah", "tuhan", "rabb"]:
        return "Allah"
    if any(m_lower.startswith(p) for p in ["yang maha", "tuhan yang maha", "tuhan semesta alam", "yang menghidupkan"]):
        return "Allah"

    # 2. Arasy (Allah's Throne)
    if "ʻarasy" in m_lower or "arasy" in m_lower:
        return "Throne"

    # 3. Kitab Suci (HolyBook)
    if u in ["http://www.wikidata.org/entity/Q428", "http://www.wikidata.org/entity/Q2383104", "http://www.wikidata.org/entity/Q1762323", "http://www.wikidata.org/entity/Q1369122"]:
        return "HolyBook"
    if m_lower in ["al-qur’an", "al-qur'an", "qur'an", "taurat", "injil", "zabur", "aż-żikr"]:
        return "HolyBook"

    # 4. Rasul (Messenger) - Berdasarkan konvensi IndQNER: Rasul Ulul Azmi & pembawa risalah
    messengers = ["muhammad", "musa", "ibrahim", "isa", "nuh", "ismail", "ishaq", "ya‘qub", "harun", "daud", "sulaiman", "saleh", "hud", "syuʻaib", "lut", "yunus"]
    for msg in messengers:
        if re.search(r'\b' + re.escape(msg) + r'\b', m_lower):
            # Kecuali jika context-nya agama atau maqam
            if "agama" in m_lower:
                return "Religion"
            if "maqam" in m_lower:
                return "Artifact"
            return "Messenger"

    # 5. Nabi (Prophet) - Nabi yang bukan rasul di IndQNER
    prophets = ["adam", "zakaria", "yahya", "ayyub", "ilyas", "ilyasa‘", "ilyasa’", "idris", "yusuf", "israil"]
    for pr in prophets:
        if re.search(r'\b' + re.escape(pr) + r'\b', m_lower):
            if "anak cucu" in m_lower:
                return "Person"
            return "Prophet"

    # 6. Malaikat (Angel)
    if any(a in m_lower for a in ["jibril", "mikail", "harut", "marut", "ruhulkudus"]) or u in ["http://www.wikidata.org/entity/Q3467762", "http://www.wikidata.org/entity/Q45581", "http://www.wikidata.org/entity/Q37946368", "http://www.wikidata.org/entity/Q37946376"]:
        return "Angel"

    # 7. Lokasi Akhirat (AfterlifeLocation)
    if any(af in m_lower for af in ["surga", "neraka", "jahanam", "‘adn"]):
        return "AfterlifeLocation"

    # 8. Artefak (Artifact)
    if any(art in m_lower for art in ["ka‘bah", "ka'bah", "tabut", "baitullah", "baitulharam", "maqam ibrahim"]):
        return "Artifact"

    # 9. Benda Langit / Astronomi (AstronomicalBody)
    if m_lower in ["bumi", "langit", "matahari", "bulan"] or u in ["http://www.wikidata.org/entity/Q2", "http://www.wikidata.org/entity/Q527", "http://www.wikidata.org/entity/Q525", "http://www.wikidata.org/entity/Q405"]:
        if "bulan ramadan" not in m_lower:
            return "AstronomicalBody"

    # 10. Peristiwa (Event)
    if any(ev in m_lower for ev in ["haji", "umrah", "kiamat", "hari akhir", "hari kiamat", "perang badar", "perang uhud", "hari sabat", "sabat", "sabtu", "hari sabtu"]):
        return "Event"

    # 11. Lokasi Geografis Dunia (GeographicalLocation)
    if any(loc in m_lower for loc in ["masjidilharam", "baitulmaqdis", "makkah", "bakkah", "sinai", "gunung sinai", "babilonia", "negeri babilonia", "negeri makkah", "ummul qura", "mesir", "safa", "marwah", "arafah", "mina", "masyarilharam", "laut merah"]):
        return "GeographicalLocation"

    # 12. Warna (Color)
    if m_lower in ["putih", "hitam", "kuning", "merah", "hijau"]:
        return "Color"

    # 13. Bahasa (Language)
    if "bahasa" in m_lower:
        return "Language"

    # 14. Agama (Religion)
    if any(rel in m_lower for rel in ["islam", "nasrani", "yahudi", "agama ibrahim"]) and not any(p in m_lower for p in ["orang", "orang-orang", "penganut", "pengikut"]):
        return "Religion"

    # 15. Tokoh / Kelompok Manusia (Person)
    if any(p in m_lower for p in ["bani israil", "ahlulkitab", "fir‘aun", "maryam", "talut", "jalut", "qabil", "habil", "hawa", "azar", "quraisy", "‘ad", "samud", "orang yahudi", "orang nasrani", "orang-orang yahudi", "orang-orang nasrani", "orang-orang sabiin", "sabiin", "penganut yahudi", "pengikut injil", "pengikut allah", "anak cucu adam", "umat islam"]):
        return "Person"

    return "Person"

def main():
    os.makedirs(MAPPINGS_DIR, exist_ok=True)
    stats = defaultdict(lambda: {"train": 0, "val": 0, "test": 0, "sample_sentence": "", "surah_ayah": ""})

    for split_name, filepath in FILES.items():
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            continue

        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                mention = row.get("mention", "").strip()
                uri = row.get("uri", "").strip()
                sentence = row.get("sentence", "").strip()
                surah_id = row.get("surah_id", "").strip()
                ayah = row.get("ayah", "").strip()

                if not mention:
                    continue

                key = (mention, uri)
                stats[key][split_name] += 1
                if not stats[key]["sample_sentence"]:
                    stats[key]["sample_sentence"] = sentence
                    stats[key]["surah_ayah"] = f"Surah {surah_id}:{ayah}"

    sorted_pairs = sorted(
        stats.items(),
        key=lambda item: (item[1]["train"] + item[1]["val"] + item[1]["test"]),
        reverse=True
    )

    print(f"Total kombinasi unik (mention, uri): {len(sorted_pairs)}")

    with open(OUTPUT_CSV, mode="w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "no",
            "mention",
            "uri",
            "total_count",
            "train_count",
            "val_count",
            "test_count",
            "proposed_label",
            "verified_label",
            "status",
            "sample_verse",
            "sample_sentence"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, ((mention, uri), counts) in enumerate(sorted_pairs, start=1):
            total = counts["train"] + counts["val"] + counts["test"]
            label = propose_initial_label(mention, uri)

            writer.writerow({
                "no": idx,
                "mention": mention,
                "uri": uri,
                "total_count": total,
                "train_count": counts["train"],
                "val_count": counts["val"],
                "test_count": counts["test"],
                "proposed_label": label,
                "verified_label": label,
                "status": "AUTO_PROPOSED",
                "sample_verse": counts["surah_ayah"],
                "sample_sentence": counts["sample_sentence"]
            })

    print(f"Berhasil menyimpan file mapping berkualitas tinggi ke: {OUTPUT_CSV}")

    # Simpan juga ke format JSON untuk kemudahan lookup skrip berikutnya
    OUTPUT_JSON = os.path.join(MAPPINGS_DIR, "indqel_to_indqner_mapping.json")
    json_data = {}
    for (mention, uri), counts in sorted_pairs:
        label = propose_initial_label(mention, uri)
        json_data[f"{mention}|||{uri}"] = {
            "mention": mention,
            "uri": uri,
            "label": label,
            "total_count": counts["train"] + counts["val"] + counts["test"],
            "train_count": counts["train"],
            "val_count": counts["val"],
            "test_count": counts["test"],
            "sample_verse": counts["surah_ayah"]
        }

    import json
    with open(OUTPUT_JSON, mode="w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"Berhasil menyimpan file mapping JSON ke: {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
