#!/usr/bin/env python3
"""Measure the SERVING cost of a DistilBERT-sized classifier without downloading weights.

Latency, memory and size depend on the architecture, not on the trained weights, so this
builds `distilbert-base-uncased`'s architecture (6 layers, 768 hidden, 66M parameters) with
random weights and a WordPiece vocabulary trained on the dataset, and measures it exactly
like a trained bundle. It says nothing about quality: get that from
`complaint-router train --model transformer` (or the `train-transformer` workflow).

    python scripts/transformer_serving_probe.py --dataset banking77
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from complaint_router import __version__, bench
from complaint_router.data import load
from complaint_router.models.transformer import TransformerClassifier
from complaint_router.registry import save_bundle
from complaint_router.text import normalise

ROOT = Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="banking77")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--max-length", type=int, default=64)
    parser.add_argument("--out", type=Path, default=ROOT / "evals" / "results")
    parser.add_argument("--vcpu-second-usd", type=float, default=0.000024)
    args = parser.parse_args(argv)

    from tokenizers import BertWordPieceTokenizer
    from transformers import (
        DistilBertConfig,
        DistilBertForSequenceClassification,
        PreTrainedTokenizerFast,
    )

    splits = load(args.dataset, args.data_dir)
    labels = splits.train.label_names
    wp = BertWordPieceTokenizer(lowercase=True)
    wp.train_from_iterator([normalise(t) for t in splits.train.texts], vocab_size=30522)
    tok = PreTrainedTokenizerFast(tokenizer_object=wp._tokenizer, pad_token="[PAD]",
                                  unk_token="[UNK]", cls_token="[CLS]", sep_token="[SEP]",
                                  mask_token="[MASK]")
    config = DistilBertConfig(num_labels=len(labels), id2label=dict(enumerate(labels)),
                              label2id={n: i for i, n in enumerate(labels)})  # 30522 vocab
    model = DistilBertForSequenceClassification(config)
    clf = TransformerClassifier(max_length=args.max_length, model=model, tokenizer=tok)
    clf.labels = labels
    params = sum(p.numel() for p in model.parameters())
    with tempfile.TemporaryDirectory() as tmp:
        bundle = Path(tmp) / "probe"
        save_bundle(clf, bundle, dataset=splits.train.name, target=splits.train.target,
                    dataset_version=splits.train.version, splits=splits.summary())
        lat = bench.latency(clf, splits.test.texts, n=300)
        report = {
            "date": datetime.now(UTC).date().isoformat(),
            "package_version": __version__,
            "model": "transformer-architecture-probe",
            "what": "distilbert-base-uncased architecture, RANDOM weights: serving cost only, "
                    "no quality",
            "dataset": splits.train.name,
            "dataset_version": splits.train.version,
            "parameters": params,
            "max_length": args.max_length,
            "serving": {**lat, **bench.batch_throughput(clf, splits.test.texts, batch_size=64),
                        **bench.load_memory(bundle),
                        "size_on_disk_mb": bench.dir_size_mb(bundle),
                        "vcpu_second_usd_assumed": args.vcpu_second_usd,
                        "cost_per_1k_usd": bench.cost_per_1k(lat["cpu_seconds_per_1k"],
                                                             args.vcpu_second_usd)},
            "machine": f"{platform.system()} {platform.machine()}, Python "
                       f"{platform.python_version()}",
        }
    args.out.mkdir(parents=True, exist_ok=True)
    path = args.out / f"{report['dataset']}-transformer-architecture-probe-{report['date']}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["serving"], indent=2))
    print(f"written {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
