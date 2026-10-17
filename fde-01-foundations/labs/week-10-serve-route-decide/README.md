# Week 10: Serve, route and decide

**Goal:** put the chosen model behind an API that knows when to hand over to a person, run it in a container, and write the decision down.

## Brief

The head of complaints will not accept a model that is "usually right". They want it to act alone only when it is confident, and to send everything else to the triage team, with numbers to prove it.

## Concepts

Confidence thresholds and margins; human-in-the-loop design; calibration; serving with FastAPI; metrics for model behaviour (not only HTTP); containers; ADRs and decision memos.

## Steps

1. Implement `route(probs, labels, threshold, margin, top_k)` in `routing.py` as its docstring says.
2. `make exercises` (all green) and `make e2e`, then `make run` and try the UI at http://127.0.0.1:8000/ with clear and vague messages.
3. Re-run `make evaluate`. Compare "auto-routed share" and "accuracy when auto-routed" across models. Which model's confidence can you trust?
4. Build and run the image on your desktop: `make up-docker` (or Podman/Rancher). Open `/metrics/` and find `predictions_total`.
5. Fill the README results table with your numbers (command, data version, date).
6. Write `docs/adr/ADR-006-which-model-ships.md` in your own words, and update `docs/customer/DECISION-MEMO.md`.

## Check

```bash
make exercises && make e2e && make up-docker
```

## Evidence

The results table, the ADR, a UI screenshot showing one auto-routed and one human-routed message, and the container's smoke-test output.

## Stretch

Calibrate the MLP with temperature scaling on the validation set (fit one scalar T that minimises validation log-loss, divide logits by T). Re-run the routing numbers: does it now deserve its confidence?

## Phase 1 exit check

From a fresh clone: `make test`, `make exercises` and `make e2e` pass; three model families compared on the same test set with quality and cost; the chosen model runs in a container on a desktop engine; an ADR records the choice.
