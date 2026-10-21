# Changelog

All notable changes. Versions follow semantic versioning; the starter repo is republished on every `v*` tag.

## [Unreleased]

### Fixed
- `.gitignore`: anchor `models/` to the repository root so it no longer matches source folders such as `src/*/models/`.

## [1.1.0] - 2026-10-21

Repository and CI fixes; no change to the system's behaviour.

### Fixed
- Restored the files dropped on the first upload: GitHub Actions workflows, `.gitignore`, `.dockerignore`, `.env.example` and the starter configuration.
- Security workflow: `aquasecurity/trivy-action` pinned to the v0.36.0 commit (the `0.28.0` tag no longer resolves).
- setuptools upgraded to 83+ in the image and the dependency audit; the PyTorch index ships 78.1.0 with CVE-2025-47273 and a vendored jaraco.context with CVE-2026-23949.

## [1.0.0] - 2026-10-13

### Added
- `complaint_router` package and `complaint-router` CLI (`download`, `train`, `evaluate`, `compare`, `predict`, `list`).
- Data: Banking77 loader pinned to a Git commit with SHA-256 checks; CFPB loaders for the bulk CSV and for fde-00's `complaints` table; fixture dataset; stratified splits; leakage removal.
- Models behind one `Classifier` interface: TF-IDF + logistic regression; a PyTorch bag-of-embeddings network with its own vocabulary, training loop and early stopping; a fine-tuned Hugging Face transformer (optional extra).
- Evaluation: macro-F1 from scratch, per-class report, top confusions, routing share and accuracy, latency p50/p95, CPU-seconds and compute cost per 1,000, framework vs model memory, size on disk; JSON and Markdown reports; comparison table; DistilBERT serving-cost probe.
- Confidence-and-margin routing to human review.
- FastAPI service with web UI, single and batch prediction, model listing; metrics `predictions_total`, `prediction_confidence`, `model_inference_seconds`; alerts `HumanReviewShareHigh` and `ModelInferenceSlow`; Grafana panels.
- Image that trains the models during `docker build` (`TRAIN_DATASET`, `TRAIN_TRANSFORMER`); deployment matrix without secrets; egress-to-DNS-only NetworkPolicy.
- `evals` workflow with an optional DistilBERT fine-tune on the GitHub runner.
- Measured Banking77 results (2026-10-13), ADR-004 to ADR-007, model card, customer brief and decision memo, labs weeks 5–10.

### Changed
- Created from `fde-template` 0.1.0; hello endpoint removed; LLM secrets removed from all deployment paths (the LLM client is kept for later phases and is not used here).
