# baseline on banking77 (intent)

Date 2026-10-13 (UTC) · package 1.0.0 · data git:57ec275d8078 · Linux x86_64, 2 CPUs, Python 3.13.16

| Metric | Value |
| --- | --- |
| Test examples | 3073 |
| Macro-F1 | 0.9110 |
| Accuracy | 0.9108 |
| Auto-routed share (threshold 0.5, margin 0.1) | 0.8728 |
| Accuracy on auto-routed | 0.9616 |
| Latency p50 / p95 (single text) | 1.663 ms / 2.162 ms |
| Batch throughput (256) | 7288.6 texts/s |
| CPU-seconds per 1,000 predictions | 1.753 |
| Compute cost per 1,000 predictions at USD 0.000024/vCPU-s (assumed price) | USD 0.000042 |
| Process RSS after load: total (framework + model) | 151.9 MB (89.1 + 35.1 MB) |
| Size on disk | 22.28 MB |
| Training time | 23.12 s |

## Weakest classes (F1)

| Class | Precision | Recall | F1 | Support |
| --- | --- | --- | --- | --- |
| balance_not_updated_after_bank_transfer | 0.6889 | 0.775 | 0.7294 | 40 |
| top_up_failed | 0.7561 | 0.775 | 0.7654 | 40 |
| card_not_working | 0.7255 | 0.925 | 0.8132 | 40 |
| failed_transfer | 0.766 | 0.9 | 0.8276 | 40 |
| pending_transfer | 0.8649 | 0.8 | 0.8312 | 40 |
| verify_my_identity | 0.8462 | 0.825 | 0.8354 | 40 |
| why_verify_identity | 0.8293 | 0.85 | 0.8395 | 40 |
| virtual_card_not_working | 1.0 | 0.725 | 0.8406 | 40 |
| wrong_exchange_rate_for_cash_withdrawal | 0.8684 | 0.825 | 0.8462 | 40 |
| pending_top_up | 0.8919 | 0.825 | 0.8571 | 40 |

## Top confusions

| True | Predicted | Count |
| --- | --- | --- |
| pending_top_up | top_up_failed | 5 |
| verify_my_identity | why_verify_identity | 5 |
| balance_not_updated_after_bank_transfer | transfer_not_received_by_recipient | 4 |
| top_up_failed | top_up_reverted | 4 |
| virtual_card_not_working | get_disposable_virtual_card | 4 |
| why_verify_identity | unable_to_verify_identity | 4 |
| card_acceptance | card_not_working | 3 |
| card_arrival | card_delivery_estimate | 3 |
| disposable_card_limits | getting_virtual_card | 3 |
| fiat_currency_support | exchange_via_app | 3 |
| fiat_currency_support | supported_cards_and_currencies | 3 |
| pending_transfer | balance_not_updated_after_bank_transfer | 3 |
| pending_transfer | failed_transfer | 3 |
| pin_blocked | card_not_working | 3 |
| top_up_reverted | top_up_failed | 3 |
