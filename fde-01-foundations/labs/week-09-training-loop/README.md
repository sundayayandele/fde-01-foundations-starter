# Week 09: The training loop, then a pretrained transformer

**Goal:** train your network with your own loop, then fine-tune a pretrained transformer and compare.

## Brief

Your network exists; now it must learn. Then the obvious question from the business: "Would one of those big pretrained models be better, and what would it cost?"

## Concepts

Cross-entropy loss; backpropagation; optimisers (AdamW); gradient clipping; epochs and batches; early stopping on validation; overfitting; transfer learning; tokenisers; fine-tuning schedules (warm-up, decay); CPU vs GPU training.

## Steps

1. Implement `train_epoch(model, batch_iter, optimizer, loss_fn)` in `models/neural.py`: train mode, zero grads, forward, loss, backward, clip to 1.0, step; return mean loss per example.
2. `pytest tests/test_models.py -m exercise` (all model tests should pass now).
3. `complaint-router train --dataset banking77 --model mlp`, then look at `models/banking77/mlp/model.json` → `history`. Where does validation macro-F1 peak? When did early stopping kick in?
4. Transformer serving cost without downloading anything: `make probe-transformer`.
5. Transformer quality (pick one):
   - Locally with internet: `pip install -e ".[transformer]" && make train-transformer` (30–60 minutes on a laptop CPU).
   - On GitHub: push your repo, then Actions → **evals** → Run workflow with `transformer: true`; download the `eval-results` artefact.
6. `make evaluate && make compare`.

## Check

```bash
make exercises       # everything except week 10 should pass
make compare
```

## Evidence

The comparison table with all three model families, and one paragraph: which model is best on quality, which on cost, and what surprised you.

## Stretch

Run the transformer fine-tune on a serverless GPU (the GPU setup arrives in fde-04; Modal and RunPod both run a plain Python script) and compare training time and cost with the CPU run.
