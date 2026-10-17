# Week 08: PyTorch from scratch

**Goal:** build a neural text classifier without a library doing the thinking for you.

## Brief

The ML lead wants the team to understand neural networks before buying into large pretrained ones. You will build the smallest useful one: learned word embeddings averaged into a sentence vector, then a hidden layer.

## Concepts

Tensors and shapes; vocabularies and unknown tokens; embeddings; `EmbeddingBag` and offsets; linear layers and ReLU; dropout; logits vs probabilities.

## Steps

1. Read `models/neural.py`. `features("my card")` returns unigrams and bigrams; why add bigrams?
2. Implement `Vocab.build(texts, min_freq, max_size)`: count features, keep those seen at least `min_freq` times, order by count then alphabetically, `[PAD, UNK]` first, cap at `max_size`.
3. Implement `Vocab.encode(text)`: ids of the features, unknown → 1, empty text → `[1]`.
4. Implement `BagOfEmbeddings.forward(ids, offsets)`: embed → dropout → hidden + ReLU → dropout → output.
5. `pytest tests/test_models.py -k "vocab or forward" -m exercise`.
6. In a Python shell, build a `Vocab` on Banking77 training texts and print its size with `min_freq=1` and `min_freq=2`. What does the model lose with a larger `min_freq`?

## Check

```bash
pytest tests/test_models.py -k "vocab or forward" -m exercise
```

## Evidence

Vocabulary sizes for two `min_freq` values, and a sketch (photo is fine) of the tensor shapes through `forward` for a batch of 3 texts.

## Stretch

Replace mean pooling with a learned attention pooling over token embeddings. Does validation macro-F1 change?
