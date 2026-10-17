# Cloud lab stacks

| Cloud | Compute | Registry | Secrets | Logs | Budget |
| --- | --- | --- | --- | --- | --- |
| [AWS](aws/README.md) | ECS Fargate 0.5 vCPU / 1 GB (public IP, no load balancer) | ECR | none needed | CloudWatch | AWS Budgets, email at 50/80/100% |
| [Azure](azure/README.md) | Container Apps 0.5 vCPU / 1 GiB, scale to zero | ACR Basic | none needed (managed identity pulls images) | Log Analytics | Consumption budget, email at 50/80/100% |
| [GCP](gcp/README.md) | Cloud Run 1 vCPU / 1 GiB, scale to zero | Artifact Registry | none needed | Cloud Logging | Billing budget at 50/80/100% |

The trained models are inside the image, so every stack deploys one stateless container.

Rules for every lab:

1. Use a sandbox account, subscription or project; never production.
2. Budget is USD 50 per month per cloud. Each stack creates its own budget alert.
3. `plan` is safe; CI runs `fmt`, `validate` and `tflint` without credentials. `apply` is a manual lab step.
4. Run `make tf-<cloud>-destroy` at the end of every lab.
5. Never commit state, plans or `.tfvars` (all ignored by `.gitignore`).
