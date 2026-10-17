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
    # >>> SOLUTION: week-07 macro-F1 from scratch
    classes = labels if labels is not None else sorted(set(y_true) | set(y_pred))
    if not classes:
        return 0.0
    tp: Counter[str] = Counter()
    fp: Counter[str] = Counter()
    fn: Counter[str] = Counter()
    for t, p in zip(y_true, y_pred, strict=True):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1
    total = 0.0
    for c in classes:
        precision = tp[c] / (tp[c] + fp[c]) if tp[c] + fp[c] else 0.0
        recall = tp[c] / (tp[c] + fn[c]) if tp[c] + fn[c] else 0.0
        total += 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return total / len(classes)
    # <<< SOLUTION


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
    # >>> SOLUTION: week-07 top confusions
    cells = []
    for i, true_label in enumerate(labels):
        for j, pred_label in enumerate(labels):
            if i != j and matrix[i, j] > 0:
                cells.append({"true": true_label, "predicted": pred_label,
                              "count": int(matrix[i, j])})
    cells.sort(key=lambda c: (-c["count"], c["true"], c["predicted"]))
    return cells[:k]
    # <<< SOLUTION
