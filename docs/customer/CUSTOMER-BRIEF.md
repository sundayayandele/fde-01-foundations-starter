# Customer brief: route complaints to the right team, first time

> Fictional engagement for the lab. "Northfield Bank" is an invented retail bank. Public data
> stands in for the bank's own: Banking77 for customer messages, CFPB complaints from fde-00.

## Situation

Northfield receives complaints and customer messages through web forms, email and chat. A triage team reads each one and assigns it to a product team. Triage takes up to a day at busy times; about one in ten messages lands in the wrong queue and is passed on again. Phase 0 (fde-00) gave the bank a clean, de-duplicated complaint feed. Now they want to automate triage without making it worse.

## What they asked for

1. Predict the right queue (product or intent) from the message text.
2. Never auto-route a message the model is unsure about; send it to a person instead.
3. A comparison of simple and advanced models, with costs, before choosing.
4. A service the platform team can run on OpenShift today and on a cloud for the pilot.
5. No message text stored or logged by the new service.

## Success criteria (agreed)

| Criterion | Target | How we show it |
| --- | --- | --- |
| Accuracy where the model auto-routes | ≥ 95% | Test-set "accuracy when auto-routed" |
| Share auto-routed | ≥ 80% | Test-set "auto-routed share" |
| Latency | p95 < 100 ms per message on 1 vCPU | Benchmark, then service metrics |
| Cost | Under USD 0.01 per 1,000 messages in compute | CPU-seconds per 1,000 × list price |
| Every queue matters | Macro-F1 reported, weakest classes listed | Per-class report |
| Privacy | No text in logs or storage | Code review; threat model |

Measured on Banking77 (2026-10-13), the baseline meets all of these: 96.2% accurate when auto-routed, 87.3% auto-routed, 2.2 ms p95, about USD 0.00004 compute per 1,000.

## Out of scope for this phase

Learning from reviewers' corrections (fde-03), LLM-generated replies (fde-02), fine-tuning on the bank's own labelled data at scale (fde-04).

## Stakeholders

| Role | Interest |
| --- | --- |
| Head of complaints operations | Faster first response; fewer bounced cases |
| Triage team lead | A queue of genuinely unclear cases, not more work |
| Model risk / compliance | Explainable choice, monitored behaviour, human in the loop |
| Platform team | Stateless container, no secrets, restricted security context |
