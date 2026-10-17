# ADR-004: Evaluation protocol

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Sunday Ayandele (owner)

## Context

Three model families will be compared and one shipped. A comparison is only worth something if every model sees the same data, the test set stays untouched until the end, and the metric reflects what the business needs: every queue matters, not only the busy ones.

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| Accuracy on a random split | Simple | Hides weak small classes; random split can leak near-duplicates |
| Macro-F1 on a stratified split with leakage removal | Every class counts equally; shares preserved; no duplicate texts across splits | Slightly more code |
| k-fold cross-validation | Lower variance | k times the training cost; awkward for the transformer |

## Decision

- Data pinned by version (Banking77 Git commit + SHA-256; CFPB file hash or row count).
- Use the source's official test set when there is one; otherwise stratified 80/10/10. Validation is always carved from training data with `stratified_split`, seed 42.
- Remove validation and test rows whose normalised text appears in training (`find_leakage`). Banking77: 7 test rows removed.
- Primary metric: **macro-F1** on test. Also: accuracy, per-class F1, top confusions, auto-routed share and accuracy when auto-routed.
- Serving metrics on the same machine: single-text latency p50/p95 over 1,000 calls after warm-up, CPU-seconds per 1,000 predictions, memory split into framework and model, size on disk.
- Model selection (early stopping, hyper-parameters) uses validation only.

## Consequences

- Numbers are comparable across models and reproducible from `meta.json`.
- One test-set evaluation per model per release; repeated peeking would turn the test set into a validation set.
- Revisit with cross-validation if test sets get small (e.g. a single CFPB issue subset).
