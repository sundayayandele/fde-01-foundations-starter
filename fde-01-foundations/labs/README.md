# Labs

Phase 1 runs weeks 5–10. Each lab has a goal, a brief, concepts, steps (naming files and TODOs), a check, evidence for your portfolio, and a stretch task.

| Week | Lab | Exercises |
| --- | --- | --- |
| 5 | [Data, splits and leakage](week-05-data-and-splits/README.md) | `stratified_split`, `find_leakage` |
| 6 | [A strong baseline](week-06-baseline/README.md) | `build_pipeline` |
| 7 | [Evaluation that tells the truth](week-07-evaluation/README.md) | `macro_f1`, `top_confusions` |
| 8 | [PyTorch from scratch](week-08-pytorch-from-scratch/README.md) | `Vocab.build`, `Vocab.encode`, `BagOfEmbeddings.forward` |
| 9 | [The training loop](week-09-training-loop/README.md) | `train_epoch` |
| 10 | [Serve, route and decide](week-10-serve-route-decide/README.md) | `route`, results table |

`make exercises` lists what is left. Exercise tests carry `@pytest.mark.exercise`; the starter's `make test` and CI skip them, so your build stays green while you work.
