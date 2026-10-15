"""
Script: train_eval_indobert.py
Deskripsi: Script komprehensif untuk melatih dan mengevaluasi model IndoBERT
           (indobenchmark/indobert-base-p1) pada tugas Named Entity Recognition (NER).
           Mendukung studi komparatif (Ablation Study):
           1. Model Baseline : Dilatih pada IndQNER Asli (train.txt)
           2. Model Enriched : Dilatih pada IndQNER-EL Revisi (train.txt)
           Keduanya diuji pada test.txt yang sama menggunakan metrik Strict Span Matching (seqeval).
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd

# Set encoding konsol UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# 27 Tag BIO Resmi IndQNER
LABEL_LIST = [
    'O',
    'B-AfterlifeLocation', 'I-AfterlifeLocation',
    'B-Allah', 'I-Allah',
    'B-Angel',
    'B-Artifact', 'I-Artifact',
    'B-AstronomicalBody',
    'B-Color', 'I-Color',
    'B-Event', 'I-Event',
    'B-Food',
    'B-GeographicalLocation', 'I-GeographicalLocation',
    'B-HolyBook',
    'B-Language', 'I-Language',
    'B-Messenger', 'I-Messenger',
    'B-Person', 'I-Person',
    'B-Prophet',
    'B-Religion', 'I-Religion',
    'B-Throne'
]
LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID2LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

def read_conll_file(filepath):
    """Membaca file CoNLL bertab (word \t tag) per kalimat."""
    sentences = []
    current_words = []
    current_tags = []

    with open(filepath, mode="r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                if current_words:
                    sentences.append({"words": current_words, "tags": current_tags})
                    current_words = []
                    current_tags = []
            else:
                parts = stripped.split("\t")
                word = parts[0]
                tag = parts[1] if len(parts) > 1 else "O"
                current_words.append(word)
                current_tags.append(tag)

    if current_words:
        sentences.append({"words": current_words, "tags": current_tags})

    return sentences

def prepare_dataset_dict(data_dir):
    """Membaca train, dev, dan test dari direktori target."""
    train_data = read_conll_file(os.path.join(data_dir, "train.txt"))
    dev_data = read_conll_file(os.path.join(data_dir, "dev.txt"))
    test_data = read_conll_file(os.path.join(data_dir, "test.txt"))
    return train_data, dev_data, test_data

def tokenize_and_align_labels(examples, tokenizer, max_length=256):
    """Tokenisasi subword Fast Tokenizer dan alignment tag BIO."""
    tokenized_inputs = tokenizer(
        [ex["words"] for ex in examples],
        padding="max_length",
        truncation=True,
        max_length=max_length,
        is_split_into_words=True
    )

    all_labels = []
    for i, ex in enumerate(examples):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        tags = ex["tags"]
        previous_word_idx = None
        label_ids = []

        for word_idx in word_ids:
            if word_idx is None:
                # [CLS], [SEP], [PAD] token diberi label -100 agar diabaikan oleh CrossEntropyLoss
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                # Subword pertama dari suatu kata mendapat tag asli kata tersebut
                tag = tags[word_idx] if word_idx < len(tags) else "O"
                label_ids.append(LABEL2ID.get(tag, LABEL2ID["O"]))
            else:
                # Subword lanjutan dari kata yang sama: jika B- diubah ke I-, jika O tetap O
                tag = tags[word_idx] if word_idx < len(tags) else "O"
                if tag.startswith("B-"):
                    sub_tag = "I-" + tag[2:]
                    label_ids.append(LABEL2ID.get(sub_tag, LABEL2ID.get(tag, LABEL2ID["O"])))
                else:
                    label_ids.append(LABEL2ID.get(tag, LABEL2ID["O"]))
            previous_word_idx = word_idx

        all_labels.append(label_ids)

    tokenized_inputs["labels"] = all_labels
    return tokenized_inputs

def extract_entities_from_tags(tags):
    """Mengekstrak entitas span [(start, end, label)] dari list tag BIO (Strict Span)."""
    entities = []
    current_entity = None
    for i, tag in enumerate(tags):
        if tag.startswith("B-"):
            if current_entity:
                entities.append(current_entity)
            current_entity = (i, i, tag[2:])
        elif tag.startswith("I-"):
            if current_entity and current_entity[2] == tag[2:]:
                current_entity = (current_entity[0], i, tag[2:])
            else:
                if current_entity:
                    entities.append(current_entity)
                current_entity = (i, i, tag[2:])
        else:
            if current_entity:
                entities.append(current_entity)
                current_entity = None
    if current_entity:
        entities.append(current_entity)
    return set(entities)

def compute_metrics(p, id2label):
    """Menghitung metrik evaluasi strict span matching via seqeval atau built-in CoNLL parser."""
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    try:
        import seqeval.metrics as seq_metrics
        p_score = float(seq_metrics.precision_score(true_labels, true_predictions))
        r_score = float(seq_metrics.recall_score(true_labels, true_predictions))
        f1_score = float(seq_metrics.f1_score(true_labels, true_predictions))
        report_dict = seq_metrics.classification_report(true_labels, true_predictions, output_dict=True)
    except (ImportError, Exception):
        # Fallback ke built-in CoNLL strict span evaluation (Zero external dependency)
        from collections import defaultdict
        tp_total, fp_total, fn_total = 0, 0, 0
        tp_class = defaultdict(int)
        fp_class = defaultdict(int)
        fn_class = defaultdict(int)
        all_classes = set()

        for t_tags, p_tags in zip(true_labels, true_predictions):
            t_ents = extract_entities_from_tags(t_tags)
            p_ents = extract_entities_from_tags(p_tags)

            for e in t_ents:
                all_classes.add(e[2])
            for e in p_ents:
                all_classes.add(e[2])

            tp = t_ents.intersection(p_ents)
            fp = p_ents - t_ents
            fn = t_ents - p_ents

            tp_total += len(tp)
            fp_total += len(fp)
            fn_total += len(fn)

            for _, _, cls in tp:
                tp_class[cls] += 1
            for _, _, cls in fp:
                fp_class[cls] += 1
            for _, _, cls in fn:
                fn_class[cls] += 1

        p_score = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0.0
        r_score = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0.0
        f1_score = 2 * p_score * r_score / (p_score + r_score) if (p_score + r_score) > 0 else 0.0

        report_dict = {}
        for cls in sorted(all_classes):
            c_tp = tp_class[cls]
            c_fp = fp_class[cls]
            c_fn = fn_class[cls]
            c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
            c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
            c_f1 = 2 * c_prec * c_rec / (c_prec + c_rec) if (c_prec + c_rec) > 0 else 0.0
            report_dict[cls] = {
                "precision": c_prec,
                "recall": c_rec,
                "f1-score": c_f1,
                "support": c_tp + c_fn
            }

    return {
        "precision": p_score,
        "recall": r_score,
        "f1": f1_score,
        "report_dict": report_dict,
        "true_preds": true_predictions,
        "true_labels": true_labels
    }

def train_and_evaluate(experiment_name, data_dir, test_dir, output_dir, args):
    """Menjalankan fine-tuning dan evaluasi model IndoBERT."""
    print(f"\n{'='*70}")
    print(f"MEMULAI EKSPERIMEN: {experiment_name.upper()}")
    print(f"Data Latih    : {data_dir}")
    print(f"Data Uji      : {test_dir}")
    print(f"Model Dasar   : {args.model_name}")
    print(f"{'='*70}")

    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForTokenClassification,
            TrainingArguments,
            Trainer,
            DataCollatorForTokenClassification
        )
    except ImportError as e:
        print(f"\n[ERROR] Dependensi belum terinstal: {e}")
        print("Silakan instal terlebih dahulu menggunakan: pip install torch transformers datasets seqeval accelerate")
        return None

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Menggunakan Perangkat Komputasi: {device.upper()}")
    if device == "cuda":
        print(f"Nama GPU: {torch.cuda.get_device_name(0)}")

    from transformers import (
        AutoConfig,
        AutoTokenizer,
        AutoModelForTokenClassification,
        TrainingArguments,
        Trainer,
        DataCollatorForTokenClassification
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Menggunakan Perangkat Komputasi: {device.upper()}")
    if device == "cuda":
        print(f"Nama GPU: {torch.cuda.get_device_name(0)}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    config = AutoConfig.from_pretrained(
        args.model_name,
        num_labels=len(LABEL_LIST),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )
    model = AutoModelForTokenClassification.from_pretrained(
        args.model_name,
        config=config,
        ignore_mismatched_sizes=True
    ).to(device)

    # 1. Muat data
    train_raw, dev_raw, _ = prepare_dataset_dict(data_dir)
    _, _, test_raw = prepare_dataset_dict(test_dir)

    print(f"Jumlah Kalimat: Train={len(train_raw):,}, Dev={len(dev_raw):,}, Test={len(test_raw):,}")

    # Buat dataset PyTorch sederhana
    class NERDataset(torch.utils.data.Dataset):
        def __init__(self, raw_data, tokenizer, max_length):
            self.encoded = tokenize_and_align_labels(raw_data, tokenizer, max_length)

        def __len__(self):
            return len(self.encoded["input_ids"])

        def __getitem__(self, idx):
            item = {
                k: torch.tensor(v[idx], dtype=torch.long)
                for k, v in self.encoded.items()
            }
            return item

    train_dataset = NERDataset(train_raw, tokenizer, args.max_length)
    dev_dataset = NERDataset(dev_raw, tokenizer, args.max_length)
    test_dataset = NERDataset(test_raw, tokenizer, args.max_length)

    exp_output_dir = os.path.join(output_dir, experiment_name)
    os.makedirs(exp_output_dir, exist_ok=True)

    tr_args_dict = dict(
        output_dir=exp_output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        report_to="none",
        fp16=(device == "cuda")
    )

    # Kompatibilitas versi Transformers (eval_strategy untuk v4.41+, evaluation_strategy untuk versi lama)
    try:
        training_args = TrainingArguments(eval_strategy="epoch", **tr_args_dict)
    except TypeError:
        training_args = TrainingArguments(evaluation_strategy="epoch", **tr_args_dict)

    # Inisialisasi Trainer (processing_class untuk transformers v4.46+, fallback ke tokenizer untuk versi lama)
    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": train_dataset,
        "eval_dataset": dev_dataset,
        "data_collator": DataCollatorForTokenClassification(tokenizer),
        "compute_metrics": lambda p: compute_metrics(p, ID2LABEL),
    }
    try:
        trainer = Trainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError:
        trainer = Trainer(tokenizer=tokenizer, **trainer_kwargs)

    print("\nMenjalankan Fine-Tuning...")
    trainer.train()

    print("\nMenjalankan Evaluasi pada Test Set...")
    test_results = trainer.predict(test_dataset)
    metrics_result = compute_metrics((test_results.predictions, test_results.label_ids), ID2LABEL)

    print(f"\n--- HASIL EVALUASI TEST SET [{experiment_name.upper()}] ---")
    print(f"Precision : {metrics_result['precision']:.4f}")
    print(f"Recall    : {metrics_result['recall']:.4f}")
    print(f"F1-Score  : {metrics_result['f1']:.4f}")

    return {
        "experiment": experiment_name,
        "precision": metrics_result["precision"],
        "recall": metrics_result["recall"],
        "f1": metrics_result["f1"],
        "report_dict": metrics_result["report_dict"]
    }

def main():
    parser = argparse.ArgumentParser(description="IndoBERT NER Benchmarking: Baseline vs Enriched")
    parser.add_argument("--mode", type=str, default="both", choices=["baseline", "enriched", "both"],
                        help="Mode eksperimen: 'baseline', 'enriched', atau 'both' (default)")
    parser.add_argument("--model_name", type=str, default="indobenchmark/indobert-base-p1",
                        help="Nama pretrained model HuggingFace")
    parser.add_argument("--epochs", type=int, default=10, 
                        help="Jumlah epoch training sesuai benchmark IndQNER README (default: 10, opsi: 20, 40)")
    parser.add_argument("--batch_size", type=int, default=16, 
                        help="Batch size sesuai benchmark IndQNER README (default: 16)")
    parser.add_argument("--learning_rate", type=float, default=2e-5, 
                        help="Learning rate sesuai benchmark IndQNER README (default: 2e-5)")
    parser.add_argument("--max_length", type=int, default=256, 
                        help="Maksimal token sequence length sesuai IndQNER README (default: 256, opsi: 512)")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    orig_dir = os.path.join(base_dir, "IndQNER", "datasets")
    revised_dir = os.path.join(base_dir, "data", "indqner_revised")
    output_dir = os.path.join(base_dir, "reports", "evaluation_results")
    os.makedirs(output_dir, exist_ok=True)

    results = {}

    if args.mode in ["baseline", "both"]:
        results["baseline"] = train_and_evaluate(
            experiment_name="baseline_indqner_original",
            data_dir=orig_dir,
            test_dir=orig_dir,
            output_dir=output_dir,
            args=args
        )

    if args.mode in ["enriched", "both"]:
        results["enriched"] = train_and_evaluate(
            experiment_name="proposed_indqner_el_revised",
            data_dir=revised_dir,
            test_dir=revised_dir,
            output_dir=output_dir,
            args=args
        )

    # Buat tabel perbandingan jika kedua model dijalankan
    if "baseline" in results and "enriched" in results and results["baseline"] and results["enriched"]:
        b = results["baseline"]
        e = results["enriched"]

        summary_file = os.path.join(output_dir, "benchmark_comparison.md")
        with open(summary_file, mode="w", encoding="utf-8") as f:
            f.write("# Laporan Hasil Komparasi Benchmarking Model IndoBERT\n\n")
            f.write("Studi Ablasi: **Model Baseline (IndQNER Asli)** vs **Model Proposed (IndQNER-EL Revisi)**\n\n")
            f.write("| Metrik Evaluasi | Model Baseline (Asli) | Model Proposed (Revisi) | Peningkatan (Delta) |\n")
            f.write("| :--- | :---: | :---: | :---: |\n")
            f.write(f"| **Overall Precision** | {b['precision']:.4f} | {e['precision']:.4f} | **{(e['precision'] - b['precision'])*100:+.2f}%** |\n")
            f.write(f"| **Overall Recall** | {b['recall']:.4f} | {e['recall']:.4f} | **{(e['recall'] - b['recall'])*100:+.2f}%** |\n")
            f.write(f"| **Overall F1-Score** | {b['f1']:.4f} | {e['f1']:.4f} | **{(e['f1'] - b['f1'])*100:+.2f}%** |\n\n")

            f.write("## Perbandingan F1-Score Per-Kelas Entitas\n\n")
            f.write("| Kelas Entitas | F1 Baseline | F1 Proposed | Delta F1 |\n")
            f.write("| :--- | :---: | :---: | :---: |\n")

            all_classes = sorted(set(list(b["report_dict"].keys()) + list(e["report_dict"].keys())))
            for cls in all_classes:
                if cls in ["macro avg", "weighted avg"]:
                    continue
                b_f1 = b["report_dict"].get(cls, {}).get("f1-score", 0.0)
                e_f1 = e["report_dict"].get(cls, {}).get("f1-score", 0.0)
                delta = (e_f1 - b_f1) * 100
                f.write(f"| `{cls}` | {b_f1:.4f} | {e_f1:.4f} | **{delta:+.2f}%** |\n")

        print(f"\nTabel komparasi komprehensif berhasil disimpan di: {summary_file}")

if __name__ == "__main__":
    main()
