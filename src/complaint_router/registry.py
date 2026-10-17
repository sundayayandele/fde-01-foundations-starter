"""Model bundles on disk: <model_dir>/<dataset>/<kind>/ with model files and meta.json.

meta.json records what a bundle is and how it was made, so the API and the results table
can always say which data and which code produced a prediction.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from complaint_router import __version__
from complaint_router.models.base import Classifier


def model_class(kind: str) -> type[Classifier]:
    if kind == "baseline":
        from complaint_router.models.baseline import BaselineClassifier
        return BaselineClassifier
    if kind == "mlp":
        from complaint_router.models.neural import MLPClassifier
        return MLPClassifier
    if kind == "transformer":
        from complaint_router.models.transformer import TransformerClassifier
        return TransformerClassifier
    raise ValueError(f"unknown model kind {kind!r}; use baseline, mlp or transformer")


def save_bundle(model: Classifier, directory: Path, *, dataset: str, target: str,
                dataset_version: str, splits: dict[str, int], metrics: dict | None = None,
                train_seconds: float | None = None) -> Path:
    directory = Path(directory)
    model.save(directory)
    meta = {
        "kind": model.kind,
        "dataset": dataset,
        "target": target,
        "dataset_version": dataset_version,
        "labels": model.labels,
        "splits": splits,
        "params": model.params(),
        "metrics": metrics or {},
        "train_seconds": round(train_seconds, 2) if train_seconds is not None else None,
        "package_version": __version__,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (directory / "meta.json").write_text(json.dumps(meta, indent=2))
    return directory


def read_meta(directory: Path) -> dict:
    return json.loads((Path(directory) / "meta.json").read_text())


def load_bundle(directory: Path) -> tuple[Classifier, dict]:
    meta = read_meta(directory)
    return model_class(meta["kind"]).load(Path(directory)), meta


def list_bundles(model_dir: Path) -> list[dict]:
    """Every bundle under model_dir, as {"name": "<dataset>/<kind>", "path", meta...}."""
    root = Path(model_dir)
    if not root.exists():
        return []
    out = []
    for meta_path in sorted(root.glob("*/*/meta.json")):
        meta = json.loads(meta_path.read_text())
        out.append({"name": f"{meta_path.parent.parent.name}/{meta_path.parent.name}",
                    "path": str(meta_path.parent), **meta})
    return out
