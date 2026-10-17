# Week 07: Evaluation that tells the truth

**Goal:** measure a model the way the business experiences it: every queue, the worst mistakes, and the cost.

## Brief

The baseline is "91% accurate". Operations want to know which queues suffer, what gets confused with what, and what it costs per thousand messages. Accuracy alone hides the small queues.

## Concepts

Precision, recall, F1; macro vs micro vs weighted averages; confusion matrices; reading the worst classes; latency percentiles (p50, p95); CPU time vs wall time; memory; cost per prediction.

## Steps

1. Implement `macro_f1(y_true, y_pred, labels)` in `metrics.py` from TP, FP and FN counts, without scikit-learn. The test compares your result with `sklearn.metrics.f1_score(average="macro")`.
2. Implement `top_confusions(matrix, labels, k)`: the largest off-diagonal cells, sorted by count, then true label, then predicted label.
3. `pytest tests/test_metrics.py -m exercise`.
4. `make evaluate`, then open `evals/results/banking77-intent-baseline-<date>.md`. Read the weakest classes and the top confusions.
5. Read `bench.py`: why measure CPU-seconds and not only wall-clock latency? Why load the model in a fresh process to measure memory?

## Check

```bash
pytest tests/test_metrics.py -m exercise && make evaluate
```

## Evidence

The evaluation report, plus a short note on the two most confused intents: are the labels genuinely ambiguous, or is the model missing something? Quote two test examples.

## Stretch

Bootstrap a 95% confidence interval for macro-F1 (resample the test set 1,000 times). Is the gap between two models larger than the interval?
