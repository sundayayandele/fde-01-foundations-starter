# Deployment

Every path runs the same image: API + UI with trained models in `/app/models`.

| Path | Command | Details |
| --- | --- | --- |
| Local Python | `make run` / `make e2e` | Uses `models/` (run `make train` first) |
| Docker Desktop | `make up-docker`, `make k8s-docker` | [Desktop labs](learning/DESKTOP-LABS.md#1a-docker-desktop) |
| Podman Desktop | `make up-podman`, `make k8s-kind` | [Desktop labs](learning/DESKTOP-LABS.md#1b-podman-desktop) |
| Rancher Desktop | `make up-rancher`, `make k8s-rancher` | [Desktop labs](learning/DESKTOP-LABS.md#1c-rancher-desktop) |
| Managed Kubernetes | `kubectl apply -k deploy/kubernetes/overlays/cloud` | Set the image with `kustomize edit set image` |
| Helm | `helm upgrade --install router deploy/helm/fde-01-foundations` | `--set route.enabled=true` on OpenShift; `--set config.SERVE_MODEL=banking77/mlp` |
| OpenShift | `oc apply -k deploy/openshift` | Route with edge TLS |
| AWS / Azure / GCP | `make tf-<cloud>-plan`, then the stack README | [Cloud labs](learning/CLOUD-LABS.md) |

## Build options

| Build argument | Default | Effect |
| --- | --- | --- |
| `TRAIN_DATASET` | `banking77` | Dataset trained into the image; `fixture` builds offline |
| `TRAIN_TRANSFORMER` | `false` | Also fine-tune DistilBERT (needs Hugging Face access; slow) and install `transformers` |

## Release

1. Update `CHANGELOG.md`; bump the version in `pyproject.toml`, `src/complaint_router/__init__.py`, `Chart.yaml`, the cloud overlay tag and Terraform `image_tag` defaults.
2. Re-run `make train evaluate compare`; update the README results table and, if the ranking changed, the ADR.
3. Tag `vX.Y.Z`; the `publish-starter` workflow regenerates the starter repo.
4. Build and push the image to each registry, tagged with the same version.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `predict` returns 503 | No bundles in `MODEL_DIR`: `GET /api/v1/models`; rebuild the image or mount `models/` |
| `predict` returns 404 | `model` names a bundle that does not exist; use a name from `/api/v1/models` |
| `HumanReviewShareHigh` alert | Messages changed (new product, campaign, language) or a different model is serving. Sample recent human-routed cases, label them, retrain and re-evaluate |
| `ModelInferenceSlow` | Transformer on too little CPU, or `OMP_NUM_THREADS` too high for the CPU limit |
| OOMKilled | Transformer with a 1 GiB limit: raise to 2 GiB |
| 5xx after deploy | `HighErrorRate`; roll back the image tag |
