# ADR-007: Route to a person on low confidence or a close call

- **Status:** Accepted
- **Date:** 2026-10-13
- **Deciders:** Sunday Ayandele (owner)

## Context

A misrouted complaint costs more than a short wait for a person: it bounces between teams, delays the response and can breach complaint-handling time limits. The model must be able to say "I don't know".

## Options considered

| Option | Pros | Cons |
| --- | --- | --- |
| Always auto-route the top class | Maximum automation | Every model error reaches a queue |
| Threshold on top probability only | Simple | Accepts near-ties (0.51 vs 0.49) |
| Threshold + margin between top two | Catches low confidence and near-ties | Two parameters to tune |
| Separate "unknown" class | Learns out-of-scope | Needs labelled out-of-scope data |

## Decision

Threshold 0.5 and margin 0.1 (`ROUTE_THRESHOLD`, `ROUTE_MARGIN`). Responses carry `reason`: `confident`, `low_confidence` or `ambiguous`. On Banking77 the baseline auto-routes 87.3% of messages at 96.2% accuracy.

## Consequences

- Both parameters are configuration, tuned per deployment on validation data, never on test.
- Probabilities must be checked for calibration before trusting a threshold; the MLP shows why.
- The share sent to people is a business number: agree it with the operations lead and alert on it (`HumanReviewShareHigh`).
