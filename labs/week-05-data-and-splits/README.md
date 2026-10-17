# Week 05: Data, splits and leakage

**Goal:** turn a labelled dataset into train, validation and test splits you can trust.

## Brief

Northfield's triage team has labelled thousands of messages. Before any model, the ML lead asks two questions: "Does every queue appear in every split in the same proportion?" and "Could the test set contain messages the model has already seen?" A wrong answer to either makes every later number meaningless.

## Concepts

Supervised learning; features and labels; train/validation/test roles; stratification; random seeds; data leakage; class imbalance; data provenance (version, checksum, licence).

## Steps

1. Set up: `python3.12 -m venv .venv && source .venv/bin/activate && make install && make test`. Read `src/complaint_router/data.py` from the top.
2. `make download`. Open `data/banking77/train.csv`: how many intents, how many examples per intent? (`python -c "import csv,collections;print(collections.Counter(r['category'] for r in csv.DictReader(open('data/banking77/train.csv'))).most_common(5))"`)
3. Implement `stratified_split(labels, fractions, seed)`: group indices by label, shuffle each group with `random.Random(seed)`, give each part `round(fraction × n)` items (the last part takes the remainder), return sorted index lists.
4. Implement `find_leakage(train_texts, other_texts)`: indices of `other_texts` whose `normalise(text)` is in the training set.
5. `pytest tests/test_data.py -m exercise`.
6. Run `python -c "from complaint_router.data import load; s = load('banking77', 'data'); print(s.summary(), s.test.notes)"`. How many test rows were removed as leaks? Look at two of them.

## Check

```bash
pytest tests/test_data.py -m exercise && make lint
```

## Evidence

Split sizes and the number of leaked rows, with two example duplicates and one sentence on what would have happened to your test score if you had kept them.

## Stretch

Exact-match leakage misses near-duplicates ("my card hasn't arrived" vs "my card has not arrived"). Write `find_near_duplicates` using character 3-gram Jaccard similarity above 0.9 and report how many it finds.
