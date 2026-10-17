# Learning guide: Phase 1, ML foundations (weeks 5–10)

## Outcomes

By the end of this phase you can:

1. Split data correctly (stratified, seeded, no leakage) and explain why a model that looks great can be lying.
2. Build a strong classical baseline and know when it is good enough.
3. Evaluate with macro-F1, per-class results and confusions, and measure latency, memory and cost.
4. Write a neural network and its training loop in PyTorch without a framework doing it for you.
5. Fine-tune a pretrained transformer and judge whether it is worth its cost.
6. Serve a model behind an API that knows when to hand over to a person, and defend the choice in an ADR.

## Weekly plan

| Week | Lab | Concepts | Exercises |
| --- | --- | --- | --- |
| 5 | [Data, splits and leakage](../../labs/week-05-data-and-splits/README.md) | supervised learning, train/val/test, stratification, leakage, class balance | `stratified_split`, `find_leakage` |
| 6 | [A strong baseline](../../labs/week-06-baseline/README.md) | features, TF-IDF, n-grams, logistic regression, regularisation | `build_pipeline` |
| 7 | [Evaluation that tells the truth](../../labs/week-07-evaluation/README.md) | precision, recall, F1, macro vs micro, confusion matrices, latency and cost | `macro_f1`, `top_confusions` |
| 8 | [PyTorch from scratch](../../labs/week-08-pytorch-from-scratch/README.md) | tensors, embeddings, layers, vocabularies | `Vocab.build`, `Vocab.encode`, `BagOfEmbeddings.forward` |
| 9 | [The training loop](../../labs/week-09-training-loop/README.md) | loss, backprop, optimisers, early stopping, transformers and fine-tuning | `train_epoch` |
| 10 | [Serve, route and decide](../../labs/week-10-serve-route-decide/README.md) | confidence, calibration, human in the loop, serving, ADRs | `route`, results table |

Budget about 10–12 hours per week. Week 9's transformer run needs internet access to Hugging Face and 30–60 minutes of CPU, or use the GitHub `evals` workflow.

## Exit check

```bash
make install && make test && make exercises && make e2e
make download && make train && make evaluate && make compare
make up-docker        # or up-podman / up-rancher; open http://127.0.0.1:8000/
```

…plus your README results table (three model families, same test set) and an ADR that chooses one with your numbers.

## Portfolio evidence a hiring manager will look for

- A comparison table with quality **and** cost, not just accuracy.
- A clear decision, including when you would change it.
- The routing rule and what it does to accuracy where the model acts alone.
- The service running in a container, with a screenshot of the UI and of the Grafana human-review panel.
