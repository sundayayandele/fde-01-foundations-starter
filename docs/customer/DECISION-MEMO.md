# Decision memo: automated complaint triage pilot

**To:** Head of Complaints Operations, Northfield Bank (fictional) · **From:** Forward-deployed engineer · **Date:** 2026-10-13

## Recommendation

Pilot the complaint router with the **TF-IDF + logistic regression** model in "assist" mode for two weeks (prediction shown to the triage team, not acted on), then switch to auto-routing for confident predictions only. Low-confidence and close-call messages keep going to the triage team.

## Why

- **Accurate where it acts.** On the public Banking77 benchmark it is right 96% of the time on the 87% of messages it auto-routes. The rest go to a person.
- **The simple model won.** A neural network we built from scratch was faster but over-confident (88% right when auto-routing). A transformer costs about 17 times more per prediction; its quality is being measured and must beat the baseline clearly to be worth it.
- **Cheap and portable.** Under 3 ms per message on one CPU, about USD 0.00004 of compute per 1,000 messages, one stateless container with no secrets. Runs on the bank's OpenShift as is.
- **Observable.** The share of messages sent to people is tracked and alerts if it rises above 30%, which is the first sign that incoming messages have changed.

## Options considered

| Option | Verdict |
| --- | --- |
| Keep manual triage | Rejected: slow at peaks, about 10% misrouted |
| Keyword rules | Rejected: brittle, unmaintained after the first product change |
| Baseline model with human fallback | **Recommended** |
| Transformer model | Deferred until it shows a clear quality gain on our data |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Bank's messages differ from the benchmark | Assist mode first; retrain on Northfield's labelled history (`make train DATASET=cfpb-db:...`) |
| Rare complaint types misrouted | Per-class F1 reviewed with each product team before go-live |
| Model drifts after launch | `HumanReviewShareHigh` alert; monthly evaluation on newly labelled cases |

## Decision needed

Approve a four-week pilot: two weeks assist mode, two weeks auto-routing of confident predictions, with a go/no-go review on measured accuracy.
