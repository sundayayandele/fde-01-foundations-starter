# GCP lab stack

Artifact Registry, Cloud Run (1 vCPU, 1 GiB, scale to zero, CPU only during requests), a
dedicated runtime service account with no roles, and an optional billing budget with alerts at
50, 80 and 100 percent of USD 50. No secrets: the image carries its trained models.

```bash
gcloud auth application-default login && gcloud config set project <sandbox-project>
make tf-gcp-init

# 1) APIs, registry, service account, budget
terraform -chdir=terraform/gcp apply -var project_id=<project> -var billing_account=<id>

# 2) Push the image
REPO=$(terraform -chdir=terraform/gcp output -raw image_repository)
gcloud auth configure-docker ${REPO%%/*}
docker tag fde-01-foundations:local $REPO/fde-01-foundations:1.0.0
docker push $REPO/fde-01-foundations:1.0.0

# 3) Deploy Cloud Run, smoke test, destroy
terraform -chdir=terraform/gcp apply -var project_id=<project> -var billing_account=<id> -var deploy_app=true
python scripts/smoke_test.py --base-url $(terraform -chdir=terraform/gcp output -raw app_url)
make tf-gcp-destroy
```

Budget alerts go to the billing account's admins by default. Build for `linux/amd64` on Apple
silicon.
