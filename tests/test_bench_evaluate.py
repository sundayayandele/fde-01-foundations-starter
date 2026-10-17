import json
from pathlib import Path

import numpy as np
import pytest

from complaint_router import bench
from complaint_router.evaluate import compare, full_report, quality, to_markdown, write_report
from complaint_router.models.base import Classifier


class Constant(Classifier):
    kind = "constant"

    def __init__(self):
        self.labels = ["a", "b"]

    def fit(self, texts, labels, val=None):
        return self

    def predict_proba(self, texts):
        return np.tile([0.7, 0.3], (len(texts), 1))

    def save(self, directory):
        pass

    @classmethod
    def load(cls, directory):
        return cls()


def test_latency_and_throughput_shapes():
    lat = bench.latency(Constant(), ["x", "y"], n=50, warmup=5)
    assert lat["n"] == 50 and lat["p95_ms"] >= lat["p50_ms"] >= 0
    assert lat["cpu_seconds_per_1k"] >= 0
    assert bench.batch_throughput(Constant(), ["x"], batch_size=8)["batch_size"] == 8


def test_cost_and_size(tmp_path):
    assert bench.cost_per_1k(2.0, 0.000024) == 0.000048
    (tmp_path / "f.bin").write_bytes(b"0" * 1_048_576)
    assert bench.dir_size_mb(tmp_path) == 1.0


REPORT = {
    "date": "2026-10-13", "package_version": "1.0.0", "model": "baseline",
    "dataset": "banking77", "target": "intent", "dataset_version": "git:abc",
    "splits": {}, "params": {}, "train_seconds": 1.5, "machine": "Linux",
    "quality": {"test_size": 10, "macro_f1": 0.9, "accuracy": 0.91,
                "per_class": [{"label": "a", "precision": 1, "recall": 1, "f1": 1, "support": 3}],
                "top_confusions": [{"true": "a", "predicted": "b", "count": 2}],
                "routing": {"threshold": 0.5, "margin": 0.1, "auto_share": 0.8,
                            "auto_accuracy": 0.95}},
    "serving": {"p50_ms": 1.0, "p95_ms": 2.0, "batch_size": 256, "texts_per_second": 900.0,
                "cpu_seconds_per_1k": 1.2, "vcpu_second_usd_assumed": 0.000024,
                "cost_per_1k_usd": 0.0000288, "rss_mb": 300.0, "model_rss_mb": 50.0,
                "framework_rss_mb": 250.0,
                "size_on_disk_mb": 4.2},
}


def test_markdown_and_compare(tmp_path):
    md = to_markdown(REPORT)
    assert "| Macro-F1 | 0.9000 |" in md and "| a | b | 2 |" in md
    other = json.loads(json.dumps(REPORT))
    other["model"], other["quality"]["macro_f1"] = "mlp", 0.8
    table = compare([other, REPORT]).splitlines()
    assert table[2].startswith("| banking77/intent | baseline | 0.9000")
    assert table[3].startswith("| banking77/intent | mlp | 0.8000")
    json_path, md_path = write_report(REPORT, tmp_path)
    assert json_path.name == "banking77-intent-baseline-2026-10-13.json"
    assert json.loads(json_path.read_text())["model"] == "baseline" and md_path.exists()


@pytest.mark.exercise
def test_quality_and_full_report(model_dir, splits):
    from complaint_router.registry import load_bundle

    bundle = model_dir / "fixture" / "baseline"
    model, meta = load_bundle(bundle)
    q = quality(model, splits)
    assert q["macro_f1"] > 0.9 and q["test_size"] == len(splits.test)
    assert 0 <= q["routing"]["auto_share"] <= 1
    report = full_report(model, meta, Path(bundle), splits, vcpu_second_usd=0.000024)
    assert report["serving"]["rss_mb"] > 0 and report["serving"]["size_on_disk_mb"] > 0
    assert report["serving"]["cost_per_1k_usd"] >= 0
