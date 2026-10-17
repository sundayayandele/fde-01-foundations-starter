"""Classification metrics: macro-F1 from first principles, per-class report, confusions."""

from __future__ import annotations

from collections import Counter

import numpy as np
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def macro_f1(y_true: list[str], y_pred: list[str], labels: list[str] | None = None) -> float:
    """Unweighted mean of per-class F1 over `labels` (default: labels in y_true or y_pred).

    For each class c: precision = TP / (TP + FP), recall = TP / (TP + FN),
    F1 = 2PR / (P + R). Undefined precision, recall or F1 counts as 0.
    Every class counts equally, so rare classes matter as much as frequent ones.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    raise NotImplementedError("TODO week-07 macro-F1 from scratch: see labs/")


def accuracy(y_true: list[str], y_pred: list[str]) -> float:
    if not y_true:
        return 0.0
    return sum(t == p for t, p in zip(y_true, y_pred, strict=True)) / len(y_true)


def per_class(y_true: list[str], y_pred: list[str], labels: list[str]) -> list[dict]:
    """Precision, recall, F1 and support per class, worst F1 first."""
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    rows = [{"label": lbl, "precision": round(float(pi), 4), "recall": round(float(ri), 4),
             "f1": round(float(fi), 4), "support": int(si)}
            for lbl, pi, ri, fi, si in zip(labels, p, r, f, s, strict=True)]
    return sorted(rows, key=lambda row: (row["f1"], row["label"]))


def confusion(y_true: list[str], y_pred: list[str], labels: list[str]) -> np.ndarray:
    return confusion_matrix(y_true, y_pred, labels=labels)


def top_confusions(matrix: np.ndarray, labels: list[str], k: int = 10) -> list[dict]:
    """The k largest off-diagonal cells: which true class is most often predicted as which.

    Returns dicts {"true", "predicted", "count"} sorted by count (desc), then true, predicted.
    Cells with count 0 are never returned.
    """
    raise NotImplementedError("TODO week-07 top confusions: see labs/")
