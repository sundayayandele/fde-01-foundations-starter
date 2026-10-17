# Security

## Reporting

Open a private security advisory on the GitHub repository. Do not file public issues for vulnerabilities.

## Controls in this repo

| Area | Control |
| --- | --- |
| Data in requests | Message text is processed in memory only. It is never logged, stored or sent anywhere; metrics carry counts and timings only. |
| Secrets | None needed: models are baked into the image. The optional Secret reference is kept for later phases. |
| Model artefacts | Bundles are built by our own pipeline from pinned, checksummed data. `joblib` and `torch` files can execute code when loaded, so bundles are never loaded from untrusted sources; the MLP is loaded with `weights_only=True`. |
| Input validation | Text 1–5,000 characters, batch ≤ 256, blank text rejected (422). |
| Least privilege | UID 10001, no capabilities, no privilege escalation, read-only root filesystem, seccomp RuntimeDefault, restricted Pod Security Standard. |
| Network | Desktop ports bind to 127.0.0.1. NetworkPolicy: ingress on 8000 only, egress limited to DNS. |
| Supply chain | Data pinned by commit and SHA-256; `security` workflow runs pip-audit, gitleaks and Trivy. |

See [THREAT-MODEL](THREAT-MODEL.md).
