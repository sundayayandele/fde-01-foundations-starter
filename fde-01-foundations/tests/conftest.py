"""Shared fixtures. MODEL_DIR points at an empty temp dir before the app is imported."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_EMPTY = Path(tempfile.mkdtemp(prefix="router-empty-"))
os.environ["MODEL_DIR"] = str(_EMPTY)

from complaint_router.data import Splits, load  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def splits() -> Splits:
    return load("fixture", Path("unused"), seed=1)


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory, splits) -> Path:
    """Baseline and MLP bundles trained on the fixture dataset (needs the exercises)."""
    from complaint_router.models.baseline import BaselineClassifier
    from complaint_router.models.neural import MLPClassifier
    from complaint_router.registry import save_bundle

    root = tmp_path_factory.mktemp("models")
    for model in (BaselineClassifier(), MLPClassifier(epochs=15, patience=15)):
        model.fit(splits.train.texts, splits.train.labels,
                  val=(splits.val.texts, splits.val.labels))
        save_bundle(model, root / "fixture" / model.kind, dataset="fixture", target="intent",
                    dataset_version="seed:7", splits=splits.summary(),
                    metrics={"spec": "fixture", "seed": 1, "test_macro_f1": 1.0},
                    train_seconds=0.1)
    return root
