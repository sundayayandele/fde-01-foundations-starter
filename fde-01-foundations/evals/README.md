# Evals

| What | Command | Output |
| --- | --- | --- |
| Train | `make download && make train` (`make train-transformer` for DistilBERT) | `models/<dataset>/<kind>/` with `meta.json` |
| Evaluate | `make evaluate` | `evals/results/<dataset>-<target>-<model>-<date>.json` and `.md` |
| Compare | `make compare` | Comparison table (also `evals/results/comparison-banking77.md`) |
| Transformer serving cost without weights | `make probe-transformer` | `evals/results/<dataset>-transformer-architecture-probe-<date>.json` |
| On GitHub | Actions → evals (weekly; or by hand with `transformer: true`) | `eval-results` artefact and a job summary table |

The protocol is in [ADR-004](../docs/adr/ADR-004-evaluation-protocol.md); how to read the numbers is in [EVALUATION](../docs/mlops/EVALUATION.md).
