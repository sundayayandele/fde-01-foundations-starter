# Cost and total cost of ownership

> **Prices are assumptions.** Unit prices below are approximate on-demand list prices as
> remembered for EU regions in mid-2026, written without live access to pricing pages.
> Check each provider's pricing page before relying on them and note the date you checked.
> The CPU-seconds are measured; the dollar figures are those measurements times the prices.

## Compute cost per prediction (measured CPU × assumed price)

Assumed price: USD 0.000024 per vCPU-second (serverless container list price, tier-1 region).

| Model | CPU-seconds per 1,000 (measured) | Compute USD per 1,000 | Compute USD per 1 million |
| --- | --- | --- | --- |
| Baseline | 1.75 | 0.000042 | 0.042 |
| MLP | 0.28 | 0.000007 | 0.007 |
| DistilBERT (architecture) | 56.3 | 0.001351 | 1.35 |

At complaint volumes (thousands a day) the compute per prediction is negligible for every model. What costs money is keeping containers available, and engineering time.

## Lab stack per month if left running (estimates)

| Cloud | Item | Approximate monthly |
| --- | --- | --- |
| AWS | Fargate 0.5 vCPU + 1 GB, 24×7 (~USD 0.04/vCPU-h, ~0.0045/GB-h) + public IPv4 (~USD 3.6) + logs | ~USD 22 |
| Azure | Container Apps 0.5 vCPU / 1 GiB, scale to zero (free monthly grant covers light use) + ACR Basic (~USD 5) | ~USD 5–8 |
| GCP | Cloud Run 1 vCPU / 1 GiB, scale to zero (free tier covers light use) + Artifact Registry | ~USD 0–2 |

All well under the USD 50 per-cloud budget. Destroy after each lab.

## Total cost of ownership: what actually differs between the models

| Cost driver | Baseline | MLP | Transformer |
| --- | --- | --- | --- |
| Training | 23 s CPU | 36 s CPU | 30–60 min CPU or minutes on a GPU (≤ USD 1 on a serverless GPU) |
| Serving hardware | Any small CPU container | Any small CPU container (+ PyTorch) | 2 GiB memory; GPU if volume is high |
| Image size | Small (scikit-learn) | + PyTorch CPU | + PyTorch + transformers + 256 MB weights |
| Explainability | Feature weights per class | Hard | Hard |
| Retraining | Seconds, anywhere | Seconds, anywhere | GPU or long CPU run |

## Three scenarios for the customer

| Scenario | Fit |
| --- | --- |
| Existing OpenShift / on-prem | Best for regulated message text: one small pod, nothing leaves the cluster |
| Self-hosted VPS | Fine for a pilot; you patch and monitor it |
| Hyperscaler serverless | Lowest effort; pay mostly for idle-to-warm behaviour (cold starts vs minimum instances) |
