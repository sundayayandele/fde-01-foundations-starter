# ADR-005: Bake trained models into the image; readiness does not require a model

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Sunday Ayandele (owner)

## Context

The same artefact must run on three desktops, Kubernetes, OpenShift and three serverless clouds, some of them air-gapped later in the series. Models are small (11–22 MB for the baseline and MLP).

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| A. Train during `docker build` and bake models into the image | One immutable artefact; no runtime downloads; works air-gapped | Image rebuild per model change; build needs network (or the offline fixture) |
| B. Download from a model registry (Hugging Face Hub, S3) at start-up | Swap models without rebuilding | Needs credentials and egress; start-up depends on another service |
| C. Mount a volume | Flexible on Kubernetes | Not available on Cloud Run/Container Apps without extra services |

## Decision

Option A by default, with C as an override (`MODEL_DIR` mount) for local experiments. The `train` stage downloads pinned Banking77 data and trains baseline and MLP with seed 42; `TRAIN_TRANSFORMER=true` adds DistilBERT.

`/health/ready` returns 200 when the process is up and reports the number of models; prediction endpoints return 503 while there are none. This keeps learner starter images (which cannot train until the exercises are done) deployable, at the cost of a pod that could receive traffic without a model.

## Consequences

- Egress from the pod can be denied (NetworkPolicy allows DNS only).
- Releases re-train: the image's `meta.json` records data version and metrics, and `/api/v1/models` exposes them.
- In production, set the platform's readiness to also check `default_available` from `/health/ready`, or switch the endpoint to fail without a model.
