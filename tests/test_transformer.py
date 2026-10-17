"""Transformer path with a tiny, randomly initialised BERT: no download, runs offline."""

import numpy as np
import pytest

transformers = pytest.importorskip("transformers")
tokenizers = pytest.importorskip("tokenizers")

from complaint_router.models.transformer import TransformerClassifier  # noqa: E402


def _tiny(texts, labels):
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    from transformers import BertConfig, BertForSequenceClassification, PreTrainedTokenizerFast

    tok = Tokenizer(models.WordLevel(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.train_from_iterator(texts, trainers.WordLevelTrainer(
        special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]"]))
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, pad_token="[PAD]", unk_token="[UNK]",
                                   cls_token="[CLS]", sep_token="[SEP]")
    names = sorted(set(labels))
    cfg = BertConfig(vocab_size=fast.vocab_size, hidden_size=32, num_hidden_layers=1,
                     num_attention_heads=2, intermediate_size=64, num_labels=len(names),
                     id2label=dict(enumerate(names)), label2id={n: i for i, n in enumerate(names)})
    return BertForSequenceClassification(cfg), fast


def test_tiny_transformer_trains_saves_and_loads(tmp_path):
    from complaint_router.data import load_fixture

    ds = load_fixture(n_per_class=20)  # no split: this test needs no learner exercise
    model, tok = _tiny(ds.texts, ds.labels)
    clf = TransformerClassifier(epochs=2, batch_size=16, lr=1e-3, model=model, tokenizer=tok)
    clf.fit(ds.texts, ds.labels)
    assert len(clf.history) == 2
    probs = clf.predict_proba(ds.texts[:4])
    assert probs.shape == (4, 4) and np.allclose(probs.sum(axis=1), 1, atol=1e-5)
    clf.save(tmp_path / "t")
    again = TransformerClassifier.load(tmp_path / "t")
    assert np.allclose(again.predict_proba(ds.texts[:4]), probs, atol=1e-5)
    assert again.params()["base_model"] == "distilbert-base-uncased"


@pytest.mark.exercise
def test_tiny_transformer_early_stopping_with_validation(splits):
    model, tok = _tiny(splits.train.texts, splits.train.labels)
    clf = TransformerClassifier(epochs=3, batch_size=16, lr=1e-3, patience=1, model=model,
                                tokenizer=tok)
    clf.fit(splits.train.texts, splits.train.labels, val=(splits.val.texts, splits.val.labels))
    assert all("val_macro_f1" in h for h in clf.history)


def test_untrained_transformer_refuses_to_predict():
    with pytest.raises(RuntimeError):
        TransformerClassifier().predict_proba(["x"])
