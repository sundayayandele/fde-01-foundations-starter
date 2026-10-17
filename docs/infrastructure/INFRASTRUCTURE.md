# Infrastructure

One stateless container on every target. Trained models live in the image (`/app/models`), so no database, volume or secret is needed.

| Target | Runtime | Size | Manifests |
| --- | --- | --- | --- |
| Local Python | `make run` | — | — |
| Docker / Rancher Desktop | Compose service | 1 CPU, 1 GiB limit | `deploy/compose/compose.yaml` |
| Podman Desktop | Pod | 1 CPU, 1 GiB | `deploy/podman/pod.yaml` |
| Desktop Kubernetes (Docker, Rancher, kind) | Deployment (1 replica) + HPA 1–2 + PDB + NetworkPolicy | requests 250m/384Mi, limits 1/1Gi | `deploy/kubernetes/overlays/*` |
| Managed Kubernetes | Deployment (2 replicas) + HPA 2–5 + Ingress | same | `deploy/kubernetes/overlays/cloud` |
| OpenShift | Deployment + Route (edge TLS) | same | `deploy/openshift` |
| Helm | Deployment (+ Ingress or Route) | same | `deploy/helm/fde-01-foundations` |
| AWS | ECS Fargate service | 0.5 vCPU / 1 GB | `terraform/aws` |
| Azure | Container App, scale to zero | 0.5 vCPU / 1 GiB | `terraform/azure` |
| GCP | Cloud Run, scale to zero | 1 vCPU / 1 GiB | `terraform/gcp` |

Configuration (environment variables): `SERVE_MODEL` (default `banking77/baseline`), `ROUTE_THRESHOLD` (0.5), `ROUTE_MARGIN` (0.1), `MODEL_DIR` (`/app/models`), `MAX_TEXT_CHARS`, `MAX_BATCH`, `OMP_NUM_THREADS` (1 in the image, so one request uses one core).

Monitoring: Prometheus scrapes `/metrics/`. Alerts: `ServiceDown`, `HighErrorRate`, `HighLatencyP95`, `HumanReviewShareHigh` (> 30% for 2 h), `ModelInferenceSlow` (p95 > 250 ms). Grafana adds human-review share, median confidence and inference p95 per model.
