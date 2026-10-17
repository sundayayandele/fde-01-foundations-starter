# Capacity planning

## Measured inputs (Banking77, 2026-10-13, 2.1 GHz vCPU, single-text calls)

| Model | p95 latency | CPU-s per 1,000 | Model memory | Batch throughput |
| --- | --- | --- | --- | --- |
| Baseline | 2.2 ms | 1.75 | 35 MB (+ scikit-learn) | see `evals/results` |
| MLP | 0.2 ms | 0.28 | 39 MB (+ PyTorch) | see `evals/results` |
| DistilBERT (architecture) | 38.6 ms | 56.3 | 395 MB (+ PyTorch) | about 53 texts/s at batch 64 |

## Sizing (estimates from the measurements above, not load-tested)

- **Baseline:** one vCPU can serve roughly 1 / 1.75 ms ≈ 500 predictions per second of pure model time; HTTP overhead will lower that. A bank receiving 10,000 complaints a day needs a tiny fraction of one core. Size for availability (2 replicas), not throughput.
- **Memory:** 1 GiB limit leaves headroom for the baseline and MLP together. The transformer needs about 1.5–2 GiB including PyTorch; raise limits before setting `SERVE_MODEL` to a transformer bundle.
- **Cold start on scale-to-zero (Container Apps, Cloud Run):** image pull plus Python and framework import plus model load. Measure it in your lab (`time curl .../health/ready` after idle); set minimum instances to 1 if the first-request delay matters.

Load-test before production (e.g. `hey` or `k6` against `/api/v1/predict`) and replace these estimates with measured numbers.
