import numpy as np
import pytest
import torch
from torch import nn

from complaint_router.models.baseline import BaselineClassifier, build_pipeline
from complaint_router.models.neural import (
    PAD,
    UNK,
    BagOfEmbeddings,
    MLPClassifier,
    Vocab,
    batches,
    collate,
    features,
    train_epoch,
)

ex = pytest.mark.exercise


def test_features_adds_bigrams():
    assert features("My card") == ["my", "card", "my_card"]


def test_collate_offsets():
    ids, offsets = collate([[5, 6], [7], [8, 9, 10]])
    assert ids.tolist() == [5, 6, 7, 8, 9, 10]
    assert offsets.tolist() == [0, 2, 3]


@ex
def test_build_pipeline_steps():
    pipe = build_pipeline(c=2.0, max_features=100)
    assert [name for name, _ in pipe.steps] == ["features", "clf"]
    word, char = (t for _, t in pipe.named_steps["features"].transformer_list)
    assert word.ngram_range == (1, 2) and char.analyzer == "char_wb"
    assert pipe.named_steps["clf"].C == 2.0


@ex
def test_baseline_learns_fixture_and_round_trips(splits, tmp_path):
    model = BaselineClassifier().fit(splits.train.texts, splits.train.labels)
    acc = np.mean([p == t for p, t in zip(model.predict(splits.test.texts),
                                          splits.test.labels, strict=True)])
    assert acc > 0.9
    probs = model.predict_proba(splits.test.texts[:3])
    assert probs.shape == (3, 4) and np.allclose(probs.sum(axis=1), 1)
    model.save(tmp_path / "b")
    again = BaselineClassifier.load(tmp_path / "b")
    assert np.allclose(again.predict_proba(splits.test.texts[:3]), probs)
    assert again.params()["c"] == 10.0


def test_untrained_models_refuse_to_predict():
    with pytest.raises(RuntimeError):
        BaselineClassifier().predict_proba(["x"])
    with pytest.raises(RuntimeError):
        MLPClassifier().predict_proba(["x"])
    assert BaselineClassifier().predict([]) == []


@ex
def test_vocab_build_and_encode():
    vocab = Vocab.build(["my card", "my card is lost", "lost"], min_freq=2, max_size=10)
    assert vocab.itos[:2] == [PAD, UNK]
    assert vocab.itos[2:] == ["card", "lost", "my", "my_card"]
    assert vocab.encode("my card") == [4, 2, 5]
    assert vocab.encode("my phone") == [4, 1, 1]
    assert vocab.encode("") == [1]
    assert len(Vocab.build(["a b c d e f"] * 3, min_freq=1, max_size=4)) == 4


@ex
def test_forward_shape():
    net = BagOfEmbeddings(vocab_size=20, n_classes=3, dim=8, hidden=16)
    ids, offsets = collate([[2, 3], [4], [5, 6, 7]])
    assert net(ids, offsets).shape == (3, 3)


@ex
def test_train_epoch_reduces_loss():
    torch.manual_seed(0)
    net = BagOfEmbeddings(vocab_size=10, n_classes=2, dim=8, hidden=16, dropout=0.0)
    encoded = [[2, 3], [2], [4, 5], [5]] * 8
    targets = [0, 0, 1, 1] * 8
    opt = torch.optim.AdamW(net.parameters(), lr=0.05)
    first = train_epoch(net, batches(encoded, targets, 8, None), opt, nn.CrossEntropyLoss())
    for _ in range(10):
        last = train_epoch(net, batches(encoded, targets, 8, None), opt, nn.CrossEntropyLoss())
    assert last < first / 2


@ex
def test_mlp_learns_fixture_and_round_trips(splits, tmp_path):
    model = MLPClassifier(epochs=20, patience=20, seed=3)
    model.fit(splits.train.texts, splits.train.labels, val=(splits.val.texts, splits.val.labels))
    assert model.history[-1]["val_macro_f1"] > 0.9
    probs = model.predict_proba(splits.test.texts)
    assert np.allclose(probs.sum(axis=1), 1, atol=1e-5)
    model.save(tmp_path / "m")
    again = MLPClassifier.load(tmp_path / "m")
    assert np.allclose(again.predict_proba(splits.test.texts), probs, atol=1e-6)
    assert again.history == model.history


@ex
def test_mlp_early_stopping_restores_best(splits):
    model = MLPClassifier(epochs=30, patience=2, seed=1)
    model.fit(splits.train.texts, splits.train.labels, val=(splits.val.texts, splits.val.labels))
    best = max(h["val_macro_f1"] for h in model.history)
    assert len(model.history) <= 30
    from complaint_router.metrics import macro_f1
    assert macro_f1(splits.val.labels, model.predict(splits.val.texts),
                    labels=model.labels) == pytest.approx(best, abs=1e-4)
