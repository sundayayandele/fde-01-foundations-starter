import numpy as np
import pytest
from sklearn.metrics import f1_score

from complaint_router.metrics import accuracy, confusion, macro_f1, per_class, top_confusions

TRUE = ["a", "a", "a", "b", "b", "c", "c", "c", "c", "d"]
PRED = ["a", "b", "a", "b", "c", "c", "c", "a", "c", "c"]


@pytest.mark.exercise
def test_macro_f1_matches_sklearn():
    labels = sorted(set(TRUE) | set(PRED))
    expected = f1_score(TRUE, PRED, labels=labels, average="macro", zero_division=0)
    assert macro_f1(TRUE, PRED) == pytest.approx(expected)
    assert macro_f1(TRUE, PRED, labels=["a", "b"]) == pytest.approx(
        f1_score(TRUE, PRED, labels=["a", "b"], average="macro", zero_division=0))


@pytest.mark.exercise
def test_macro_f1_edge_cases():
    assert macro_f1(["a", "b"], ["a", "b"]) == 1.0
    assert macro_f1(["a"], ["b"]) == 0.0
    assert macro_f1([], []) == 0.0
    with pytest.raises(ValueError):
        macro_f1(["a"], [])


@pytest.mark.exercise
def test_top_confusions():
    labels = ["a", "b", "c", "d"]
    cm = confusion(TRUE, PRED, labels)
    assert top_confusions(cm, labels, k=2) == [
        {"true": "a", "predicted": "b", "count": 1},
        {"true": "b", "predicted": "c", "count": 1},
    ]
    assert len(top_confusions(cm, labels)) == 4
    assert top_confusions(np.eye(2, dtype=int), ["x", "y"]) == []


def test_accuracy_and_per_class():
    assert accuracy(TRUE, PRED) == 0.6
    assert accuracy([], []) == 0.0
    rows = per_class(TRUE, PRED, ["a", "b", "c", "d"])
    assert rows[0]["label"] == "d" and rows[0]["f1"] == 0.0
    assert {r["label"]: r["support"] for r in rows} == {"a": 3, "b": 2, "c": 4, "d": 1}
