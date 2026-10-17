# Evaluation

The protocol is fixed in [ADR-004](../adr/ADR-004-evaluation-protocol.md). In short:

1. Pinned data; validation carved from training with a stratified split; leakage removed.
2. Model selection on validation only (early stopping for the neural models).
3. One evaluation per model on the test set, recorded in `evals/results/<dataset>-<target>-<model>-<date>.json` and `.md`.

## What every report contains

| Section | Metrics |
| --- | --- |
| Quality | Macro-F1, accuracy, per-class precision/recall/F1/support (weakest first), top 15 confusions |
| Routing | Share auto-routed and accuracy on that share, at the configured threshold and margin |
| Serving | Single-text latency p50/p95/mean over 1,000 calls after 20 warm-up calls; batch throughput (256); CPU-seconds per 1,000 predictions; compute cost at a stated vCPU-second price; RSS of a fresh process split into framework import and model; size on disk |
| Provenance | Date (UTC), package version, dataset version, split sizes, hyper-parameters, training time, machine |

## Reproduce

```bash
make download && make train && make evaluate && make compare
make probe-transformer                     # DistilBERT serving cost without weights
make train-transformer && make evaluate     # needs Hugging Face access; slow on CPU
```

On GitHub, run the `evals` workflow (Actions → evals → Run workflow, `transformer: true`) to fine-tune DistilBERT on the runner and download the reports as an artefact.

## Reading the numbers

- Compare models only within one report set (same machine, same date).
- Macro-F1 differences under about 1 point on 3,000 examples are within noise; check per-class results before claiming a win.
- "Accuracy when auto-routed" is the number operations feel. A model with a lower overall score but better-calibrated confidence can be the better product.
