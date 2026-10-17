# ADR-006: Which model ships

- **Status:** Accepted (revisit when the transformer's measured quality is in)
- **Date:** 2026-10-13
- **Deciders:** Sunday Ayandele (owner)

## Context

Three model families were trained and evaluated under ADR-004 on Banking77 (77 intents, 3,073 test examples). The routing service must be accurate where it auto-routes, cheap to run on a scale-to-zero container, and simple to operate.

<!-- >>> SOLUTION: week-10 ADR on which model ships -->
## Options considered (measured 2026-10-13, see README and `evals/results/`)

| Option | Macro-F1 | Accuracy when auto-routed (share) | p50 latency | CPU-s / 1k | Memory | Disk |
| --- | --- | --- | --- | --- | --- | --- |
| TF-IDF + logistic regression | **0.911** | **96.2%** (87.3%) | 1.66 ms | 1.75 | 35 MB + scikit-learn | 22 MB |
| PyTorch bag of embeddings | 0.849 | 88.3% (93.1%) | 0.13 ms | 0.28 | 39 MB + PyTorch | 11 MB |
| DistilBERT (fine-tuned) | pending (evals workflow) | pending | 28.7 ms* | 56.3* | 395 MB* + PyTorch | 256 MB* |

\* Architecture-only measurement with random weights; quality not yet measured.

## Decision

Serve the **baseline** (`SERVE_MODEL=banking77/baseline`). It has the best quality measured so far, and its confidence is the most trustworthy for routing: 96% correct when it auto-routes, versus 88% for the MLP, whose over-confidence would send wrong answers straight to queues. Its latency (under 3 ms p95) is far below any user-visible budget, and it needs no GPU and no PyTorch at serving time.

The transformer stays a candidate. It would need at least about 3 points of macro-F1 over the baseline, measured on the same test set, to justify ~17× the latency, ~32× the CPU per prediction and a model about 12× larger on disk.

## Consequences

- The image still carries the MLP for comparison; `model` can be chosen per request.
- Watch `HumanReviewShareHigh`: about 13% human review is expected on Banking77-like traffic.
- Revisit when (a) the transformer result arrives, (b) CFPB-trained models are evaluated (longer texts favour contextual models), or (c) calibration (week-10 stretch) changes the routing trade-off.
<!-- <<< SOLUTION -->
