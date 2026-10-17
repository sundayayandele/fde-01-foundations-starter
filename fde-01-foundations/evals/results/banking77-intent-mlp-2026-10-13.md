# mlp on banking77 (intent)

Date 2026-10-13 (UTC) · package 1.0.0 · data git:57ec275d8078 · Linux x86_64, 2 CPUs, Python 3.13.16

| Metric | Value |
| --- | --- |
| Test examples | 3073 |
| Macro-F1 | 0.8490 |
| Accuracy | 0.8467 |
| Auto-routed share (threshold 0.5, margin 0.1) | 0.9307 |
| Accuracy on auto-routed | 0.8832 |
| Latency p50 / p95 (single text) | 0.129 ms / 0.206 ms |
| Batch throughput (256) | 41851.3 texts/s |
| CPU-seconds per 1,000 predictions | 0.278 |
| Compute cost per 1,000 predictions at USD 0.000024/vCPU-s (assumed price) | USD 0.000007 |
| Process RSS after load: total (framework + model) | 684.0 MB (617.5 + 38.9 MB) |
| Size on disk | 11.25 MB |
| Training time | 35.85 s |

## Weakest classes (F1)

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| card_linking | 0.4021 | 0.975 | 0.5693 | 40 |
| balance_not_updated_after_bank_transfer | 0.7179 | 0.7 | 0.7089 | 40 |
| compromised_card | 0.8571 | 0.6154 | 0.7164 | 39 |
| pin_blocked | 0.725 | 0.7436 | 0.7342 | 39 |
| card_not_working | 0.6875 | 0.825 | 0.75 | 40 |
| top_up_failed | 0.7111 | 0.8 | 0.7529 | 40 |
| why_verify_identity | 0.7561 | 0.775 | 0.7654 | 40 |
| fiat_currency_support | 0.9 | 0.675 | 0.7714 | 40 |
| failed_transfer | 0.6923 | 0.9 | 0.7826 | 40 |
| declined_card_payment | 0.6667 | 0.95 | 0.7835 | 40 |

## Top confusions

| True | Predicted | Count |
| --- | --- | --- |
| fiat_currency_support | exchange_via_app | 8 |
| compromised_card | card_linking | 6 |
| pending_top_up | top_up_failed | 6 |
| verify_my_identity | why_verify_identity | 6 |
| activate_my_card | card_linking | 5 |
| beneficiary_not_allowed | failed_transfer | 5 |
| card_arrival | card_delivery_estimate | 5 |
| contactless_not_working | card_not_working | 5 |
| declined_transfer | failed_transfer | 5 |
| lost_or_stolen_card | card_linking | 5 |
| why_verify_identity | verify_my_identity | 5 |
| balance_not_updated_after_bank_transfer | pending_transfer | 4 |
| card_not_working | declined_card_payment | 4 |
| compromised_card | cash_withdrawal_not_recognised | 4 |
| get_disposable_virtual_card | getting_virtual_card | 4 |
