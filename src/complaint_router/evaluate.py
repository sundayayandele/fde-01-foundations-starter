"""Full evaluation of a trained bundle: quality on the test split plus serving costs."""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from complaint_router import __version__, bench
from complaint_router.data import Splits
from complaint_router.metrics import accuracy, confusion, macro_f1, per_class, top_confusions
from complaint_router.models.base import Classifier
from complaint_router.routing import route


def quality(model: Classifier, splits: Splits, threshold: float = 0.5,
            margin: float = 0.1) -> dict:
    texts, truth = splits.test.texts, splits.test.labels
    probs = model.predict_proba(texts)
    labels = model.labels
    pred = [labels[i] for i in probs.argmax(axis=1)]
    matrix = confusion(truth, pred, labels)
    decisions = [route(p, labels, threshold, margin) for p in probs]
    auto = [i for i, d in enumerate(decisions) if d["route"] == "auto"]
    auto_acc = accuracy([truth[i] for i in auto], [pred[i] for i in auto]) if auto else None
    return {
        "test_size": len(texts),
        "macro_f1": round(macro_f1(truth, pred, labels=labels), 4),
        "accuracy": round(accuracy(truth, pred), 4),
        "per_class": per_class(truth, pred, labels),
        "top_confusions": top_confusions(matrix, labels, k=15),
        "routing": {
            "threshold": threshold,
            "margin": margin,
            "auto_share": round(len(auto) / len(texts), 4) if texts else None,
            "auto_accuracy": round(auto_acc, 4) if auto_acc is not None else None,
        },
    }


def full_report(model: Classifier, meta: dict, bundle_dir: Path, splits: Splits, *,
                vcpu_second_usd: float, threshold: float = 0.5, margin: float = 0.1) -> dict:
    q = quality(model, splits, threshold, margin)
    lat = bench.latency(model, splits.test.texts, n=1000)
    return {
        "date": datetime.now(UTC).date().isoformat(),
        "package_version": __version__,
        "model": meta["kind"],
        "dataset": meta["dataset"],
        "target": meta["target"],
        "dataset_version": meta["dataset_version"],
        "splits": meta["splits"],
        "params": meta["params"],
        "train_seconds": meta.get("train_seconds"),
        "quality": q,
        "serving": {
            **lat,
            **bench.batch_throughput(model, splits.test.texts),
            **bench.load_memory(bundle_dir),
            "size_on_disk_mb": bench.dir_size_mb(bundle_dir),
            "vcpu_second_usd_assumed": vcpu_second_usd,
            "cost_per_1k_usd": bench.cost_per_1k(lat["cpu_seconds_per_1k"], vcpu_second_usd),
        },
        "machine": f"{platform.system()} {platform.machine()}, {_cpus()} CPUs, "
                   f"Python {platform.python_version()}",
    }


def _cpus() -> int:
    import os
    return os.cpu_count() or 1


def write_report(report: dict, out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{report['dataset']}-{report['target']}-{report['model']}-{report['date']}"
    json_path = out_dir / f"{stem}.json"
    json_path.write_text(json.dumps(report, indent=2, default=_np_default) + "\n")
    md_path = out_dir / f"{stem}.md"
    md_path.write_text(to_markdown(report))
    return json_path, md_path


def _np_default(value):
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serialisable: {type(value)}")


def to_markdown(r: dict) -> str:
    q, s = r["quality"], r["serving"]
    lines = [
        f"# {r['model']} on {r['dataset']} ({r['target']})",
        "",
        f"Date {r['date']} (UTC) · package {r['package_version']} · data {r['dataset_version']}"
        f" · {r['machine']}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Test examples | {q['test_size']} |",
        f"| Macro-F1 | {q['macro_f1']:.4f} |",
        f"| Accuracy | {q['accuracy']:.4f} |",
        f"| Auto-routed share (threshold {q['routing']['threshold']}, margin "
        f"{q['routing']['margin']}) | {q['routing']['auto_share']} |",
        f"| Accuracy on auto-routed | {q['routing']['auto_accuracy']} |",
        f"| Latency p50 / p95 (single text) | {s['p50_ms']} ms / {s['p95_ms']} ms |",
        f"| Batch throughput ({s['batch_size']}) | {s['texts_per_second']} texts/s |",
        f"| CPU-seconds per 1,000 predictions | {s['cpu_seconds_per_1k']} |",
        f"| Compute cost per 1,000 predictions at USD {s['vcpu_second_usd_assumed']:.6f}/vCPU-s"
        f" (assumed price) | USD {s['cost_per_1k_usd']:.6f} |",
        f"| Process RSS after load: total (framework + model) | {s['rss_mb']} MB "
        f"({s.get('framework_rss_mb', '?')} + {s['model_rss_mb']} MB) |",
        f"| Size on disk | {s['size_on_disk_mb']} MB |",
        f"| Training time | {r['train_seconds']} s |",
        "",
        "## Weakest classes (F1)",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [f"| {c['label']} | {c['precision']} | {c['recall']} | {c['f1']} | {c['support']} |"
              for c in q["per_class"][:10]]
    lines += ["", "## Top confusions", "", "| True | Predicted | Count |", "| --- | --- | --- |"]
    lines += [f"| {c['true']} | {c['predicted']} | {c['count']} |" for c in q["top_confusions"]]
    return "\n".join(lines) + "\n"


def compare(reports: list[dict]) -> str:
    """Markdown comparison table across models (one row per report)."""
    header = ("| Dataset | Model | Macro-F1 | Accuracy | Auto share | Auto accuracy | p50 ms | "
              "p95 ms | CPU-s / 1k | USD / 1k | RSS MB (model) | Disk MB | Train s |")
    rows = [header, "| " + " | ".join(["---"] * 13) + " |"]
    for r in sorted(reports, key=lambda x: (x["dataset"], -x["quality"]["macro_f1"])):
        q, s = r["quality"], r["serving"]
        rt = q["routing"]
        rows.append(f"| {r['dataset']}/{r['target']} | {r['model']} | {q['macro_f1']:.4f} | "
                    f"{q['accuracy']:.4f} | {rt['auto_share']} | {rt['auto_accuracy']} | "
                    f"{s['p50_ms']} | {s['p95_ms']} | {s['cpu_seconds_per_1k']} | "
                    f"{s['cost_per_1k_usd']:.6f} | {s['rss_mb']} ({s['model_rss_mb']}) | "
                    f"{s['size_on_disk_mb']} | {r['train_seconds']} |")
    return "\n".join(rows) + "\n"
