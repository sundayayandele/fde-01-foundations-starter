# Azure lab stack

Container Registry (Basic), Container Apps (0.5 vCPU, 1 GiB, scale to zero), a user-assigned
managed identity for image pulls, Log Analytics, and a monthly budget with alerts at 50, 80 and
100 percent of USD 50. No secrets: the image carries its trained models.

```bash
az login && az account set -s <sandbox-subscription-id>
make tf-azure-init

# 1) Registry, identity and budget (no app yet)
terraform -chdir=terraform/azure apply -var subscription_id=<id> -var alert_email=you@example.com

# 2) Push the image
ACR=$(terraform -chdir=terraform/azure output -raw registry_name)
az acr login -n $ACR
docker tag fde-01-foundations:local $ACR.azurecr.io/fde-01-foundations:1.0.0
docker push $ACR.azurecr.io/fde-01-foundations:1.0.0

# 3) Create the Container App, smoke test, destroy
terraform -chdir=terraform/azure apply -var subscription_id=<id> -var alert_email=you@example.com \
  -var deploy_app=true
python scripts/smoke_test.py --base-url $(terraform -chdir=terraform/azure output -raw app_url)
make tf-azure-destroy
```

Scale to zero means the first request after idle waits for a cold start (image pull and model
load); see `docs/infrastructure/CAPACITY-PLANNING.md`. Set `budget_start_date` to the first day
of the current month. Build for `linux/amd64` on Apple silicon.
