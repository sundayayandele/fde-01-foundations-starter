# AWS lab stack

ECR, ECS Fargate (0.5 vCPU, 1 GB, one task, public IP, no load balancer), CloudWatch Logs and
a monthly budget with alerts at 50, 80 and 100 percent of USD 50. The image carries its trained
models, so there are no secrets and no database.

```bash
make tf-aws-init
terraform -chdir=terraform/aws plan -out=tfplan -var alert_email=you@example.com \
  -var allowed_cidr=$(curl -s ifconfig.me)/32
make tf-aws-apply

# Push the image, then roll the service
REPO=$(terraform -chdir=terraform/aws output -raw ecr_repository_url)
aws ecr get-login-password | docker login --username AWS --password-stdin ${REPO%/*}
docker tag fde-01-foundations:local $REPO:1.0.0 && docker push $REPO:1.0.0
aws ecs update-service --cluster fde-01-foundations --service fde-01-foundations --force-new-deployment

# Smoke test (and open http://$IP:8000/ for the UI), then destroy
IP=$(eval "$(terraform -chdir=terraform/aws output -raw find_public_ip)")
python scripts/smoke_test.py --base-url http://$IP:8000
make tf-aws-destroy
```

Build for `linux/amd64` on Apple silicon: `docker build --platform linux/amd64 ...`. Serve a
different bundle with `-var serve_model=banking77/mlp`. Costs: `docs/COST-TCO.md`.
