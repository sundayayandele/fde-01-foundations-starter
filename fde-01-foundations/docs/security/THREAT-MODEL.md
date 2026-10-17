# Threat model (STRIDE)

## Assets

Message text in transit, model bundles, routing decisions (they decide who sees a complaint), the data used to train.

## Threats

| STRIDE | Threat | Mitigation | Residual |
| --- | --- | --- | --- |
| Spoofing | Unauthenticated callers use the API | Lab only; production sits behind the platform's ingress auth or API gateway | Medium in labs |
| Tampering | Poisoned or altered training data | Pinned commit + SHA-256 check; download fails on mismatch | Low for Banking77; CFPB data trust comes from fde-00's quality report |
| Tampering | Malicious model file (pickle) | Bundles only from our build; never load user-supplied bundles; `weights_only=True` for PyTorch | Low |
| Tampering | Adversarial text to force auto-routing to a chosen queue | Margin rule; human review for low confidence; monitoring | Medium: text classifiers can be gamed; fde-03 adds red-team tests |
| Repudiation | Unknown which model made a decision | Response and metrics carry the model name; `meta.json` records data version and metrics | Low |
| Information disclosure | Message text in logs | Text never logged; access logs record paths only | Low |
| Information disclosure | Training data memorised and exposed | Models return labels and probabilities only, not text | Low |
| Denial of service | Large or many requests | 5,000 characters max, 256 texts per batch, HPA; p95 inference alert | Medium without rate limiting; add at the gateway |
| Elevation of privilege | Container escape | Non-root, no capabilities, read-only FS, seccomp, egress DNS only | Low |

## Accepted lab trade-offs (Trivy misconfiguration findings are non-blocking for these)

| Trade-off | Production fix |
| --- | --- |
| API without authentication | Ingress auth, mTLS or an API gateway with keys and rate limits |
| AWS task with public IP, no load balancer | ALB with TLS, private subnets |
| No customer-managed keys | KMS / Key Vault / Cloud KMS for registries and logs |
