# Cloud labs: AWS, Azure, GCP

Each cloud stack runs the router image on that cloud's cheapest managed container service with a budget alert. The image carries its models, so there is nothing else to provision.

- [AWS: ECS Fargate](../../terraform/aws/README.md)
- [Azure: Container Apps](../../terraform/azure/README.md)
- [GCP: Cloud Run](../../terraform/gcp/README.md)

## Rules

1. **Sandbox only.** Use a dedicated sandbox account, subscription or project.
2. **Budget:** USD 50 per month per cloud, alerts at 50, 80 and 100 percent (created by the stack).
3. **Plan first.** `terraform plan` is free and safe. Read it before `apply`.
4. **Destroy every time.** `make tf-<cloud>-destroy` at the end of the lab.
5. **Never commit** state files, plans or `.tfvars`.

## Typical lab flow (about 30–45 minutes)

```bash
docker build -t fde-01-foundations:local .          # add --platform linux/amd64 on Apple silicon
make tf-<cloud>-init
# apply 1: registry, identity, budget  ·  push the image  ·  apply 2: the service
python scripts/smoke_test.py --base-url <url printed by terraform output>
open <url>/                                         # the UI
make tf-<cloud>-destroy
```

## Measure while you are there

Cold start on scale-to-zero: wait 15 minutes, then `time curl -s <url>/health/ready`. Warm latency: `for i in $(seq 20); do curl -s -o /dev/null -w "%{time_total}\n" -X POST <url>/api/v1/predict -H 'Content-Type: application/json' -d '{"text":"my card has not arrived"}'; done`. Record both with the region and date: they belong in your decision memo.

## Evidence for your portfolio

The plan summary, smoke-test output, the cold-start and warm-latency numbers, a screenshot of the UI on the cloud URL, and the destroy output.
