# Model card: complaint router, baseline (`banking77/baseline`)

| Field | Value |
| --- | --- |
| Model | TF-IDF (word 1–2-grams + character 2–5-grams, sublinear TF) + multinomial logistic regression, C = 10 |
| Version | Package 1.0.0; bundle `models/banking77/baseline/meta.json` |
| Task | Single-label text classification into 77 banking intents, with a route-to-human decision |
| Training data | Banking77, commit `57ec275d8078`, 9,003 training examples (official train set minus a stratified 1,000-example validation split), seed 42 |
| Evaluation data | Official Banking77 test set minus 7 texts that duplicate training texts: 3,073 examples |
| Results (2026-10-13) | Macro-F1 0.911, accuracy 0.911; auto-routes 87.3% at 96.2% accuracy (threshold 0.5, margin 0.1) |
| Weakest classes | `balance_not_updated_after_bank_transfer` (F1 0.73), `top_up_failed` (0.77), `card_not_working` (0.81) |
| Common confusions | `pending_top_up` → `top_up_failed`, `verify_my_identity` → `why_verify_identity` (5 each) |
| Serving | 1.66 ms p50 / 2.16 ms p95 per message on one 2.1 GHz vCPU; 35 MB model in memory; 22 MB on disk |
| Intended use | Suggest or assign a queue for short customer messages in English; send unclear messages to people |
| Not intended for | Decisions about a customer (credit, fraud, eligibility); languages other than English; messages unlike banking queries without retraining |
| Known limitations | Bag-of-n-grams: no deep understanding of negation or long context; probabilities are not calibrated; Banking77 messages are short, single-intent and English, unlike long CFPB narratives |
| Fairness | No demographic attributes are used or available. Error rates may still differ by writing style, dialect or language proficiency; review per-class errors with operations before go-live |
| Human oversight | Low-confidence and close-call predictions go to a person; human-review share is monitored |
| Retraining | On label taxonomy changes, when `HumanReviewShareHigh` fires, or monthly with newly labelled cases |

The MLP and transformer bundles have the same card fields in their `meta.json` and evaluation reports.
