# Week 06: A strong baseline

**Goal:** build the model every other model has to beat, in under 30 seconds of training.

## Brief

Before anyone mentions transformers, the head of complaints wants to know what a simple, explainable model can do. If it is good enough, the project ships sooner and costs less.

## Concepts

Bag-of-words; TF-IDF; word and character n-grams; sparse matrices; logistic regression; regularisation (C); scikit-learn pipelines; why the same `normalise` must run at training and serving time.

## Steps

1. Read `src/complaint_router/text.py`. What happens to `XX/XX/2026` and `{$45.00}`? Why does that help a model?
2. Implement `build_pipeline(c, max_features, seed)` in `models/baseline.py` exactly as its docstring says: a `FeatureUnion` of a word (1–2-gram) and a character (`char_wb`, 2–5-gram) TF-IDF vectoriser, then `LogisticRegression`.
3. `pytest tests/test_models.py -k "pipeline or baseline" -m exercise`.
4. Train on Banking77: `complaint-router train --dataset banking77 --model baseline`. Note macro-F1 and training time.
5. Try `complaint-router predict --bundle models/banking77/baseline "I still have not received my card" "can I get a refund"`.

## Check

```bash
pytest tests/test_models.py -k "pipeline or baseline" -m exercise
complaint-router train --dataset banking77 --model baseline
```

## Evidence

The training line (macro-F1, accuracy, seconds) and the two predictions with their confidence.

## Stretch

Tune `C` on the **validation** split only (try 1, 3, 10, 30). Plot validation macro-F1 against C, pick one, and only then check test. Why must you not pick C by looking at the test score?
