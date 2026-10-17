"""A small neural classifier written from scratch in PyTorch.

Vocabulary of unigrams and bigrams -> mean of learned embeddings (EmbeddingBag) ->
dropout -> hidden layer (ReLU) -> class logits. Trained with AdamW, cross-entropy and
early stopping on validation macro-F1. No pretrained weights, so it trains in seconds
on a laptop CPU and shows every moving part of a training loop.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import torch
from torch import nn

from complaint_router.metrics import macro_f1
from complaint_router.models.base import Classifier
from complaint_router.text import tokenize

PAD, UNK = "<pad>", "<unk>"


def features(text: str) -> list[str]:
    """Unigrams plus adjacent bigrams ("my_card"): cheap word-order signal."""
    tokens = tokenize(text)
    return tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:], strict=False)]


class Vocab:
    """Maps feature strings to integer ids. Id 0 is padding, id 1 is unknown."""

    def __init__(self, itos: list[str]) -> None:
        self.itos = itos
        self.stoi = {s: i for i, s in enumerate(itos)}

    def __len__(self) -> int:
        return len(self.itos)

    @classmethod
    def build(cls, texts: list[str], min_freq: int = 2, max_size: int = 50_000) -> Vocab:
        """Count `features(text)` over all texts; keep features seen at least `min_freq` times.

        Order: [PAD, UNK] first, then by count (desc), ties broken alphabetically, and stop
        at `max_size` entries in total (including PAD and UNK).
        """
        raise NotImplementedError("TODO week-08 build the vocabulary: see labs/")

    def encode(self, text: str) -> list[int]:
        """Ids of `features(text)`; unknown features map to UNK (1); empty text gives [UNK]."""
        raise NotImplementedError("TODO week-08 encode text to ids: see labs/")


class BagOfEmbeddings(nn.Module):
    """EmbeddingBag(mean) -> Dropout -> Linear -> ReLU -> Dropout -> Linear."""

    def __init__(self, vocab_size: int, n_classes: int, dim: int = 128, hidden: int = 256,
                 dropout: float = 0.3) -> None:
        super().__init__()
        self.embed = nn.EmbeddingBag(vocab_size, dim, mode="mean", padding_idx=0)
        self.drop = nn.Dropout(dropout)
        self.hidden = nn.Linear(dim, hidden)
        self.out = nn.Linear(hidden, n_classes)

    def forward(self, ids: torch.Tensor, offsets: torch.Tensor) -> torch.Tensor:
        """ids: 1-D tensor of all token ids in the batch, concatenated.
        offsets: 1-D tensor with the start position of each text in `ids`.
        Returns logits of shape (batch, n_classes).
        """
        raise NotImplementedError("TODO week-08 forward pass: see labs/")


def collate(encoded: list[list[int]]) -> tuple[torch.Tensor, torch.Tensor]:
    """Flatten a batch of id lists into (ids, offsets) for EmbeddingBag."""
    lengths = [len(e) for e in encoded]
    offsets = torch.tensor([0, *np.cumsum(lengths)[:-1].tolist()], dtype=torch.long)
    ids = torch.tensor([i for e in encoded for i in e], dtype=torch.long)
    return ids, offsets


def batches(encoded: list[list[int]], targets: list[int], batch_size: int,
            rng: random.Random | None) -> Iterator[tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
    order = list(range(len(encoded)))
    if rng is not None:
        rng.shuffle(order)
    for start in range(0, len(order), batch_size):
        idx = order[start:start + batch_size]
        ids, offsets = collate([encoded[i] for i in idx])
        yield ids, offsets, torch.tensor([targets[i] for i in idx], dtype=torch.long)


def train_epoch(model: nn.Module, batch_iter, optimizer: torch.optim.Optimizer,
                loss_fn: nn.Module) -> float:
    """One pass over the training batches. Returns the mean loss per example.

    For each (ids, offsets, y): put the model in training mode, zero the gradients,
    compute logits and loss, backpropagate, clip gradient norm to 1.0, step the optimiser.
    """
    raise NotImplementedError("TODO week-09 training loop: see labs/")


class MLPClassifier(Classifier):
    kind = "mlp"

    def __init__(self, dim: int = 128, hidden: int = 256, dropout: float = 0.3,
                 lr: float = 3e-3, weight_decay: float = 1e-4, epochs: int = 40,
                 batch_size: int = 64, patience: int = 5, min_freq: int = 1,
                 max_vocab: int = 50_000, seed: int = 42) -> None:
        self.dim, self.hidden, self.dropout = dim, hidden, dropout
        self.lr, self.weight_decay = lr, weight_decay
        self.epochs, self.batch_size, self.patience = epochs, batch_size, patience
        self.min_freq, self.max_vocab, self.seed = min_freq, max_vocab, seed
        self.vocab: Vocab | None = None
        self.net: BagOfEmbeddings | None = None
        self.labels: list[str] = []
        self.history: list[dict[str, float]] = []

    def params(self) -> dict[str, object]:
        return {"dim": self.dim, "hidden": self.hidden, "dropout": self.dropout, "lr": self.lr,
                "weight_decay": self.weight_decay, "epochs": self.epochs,
                "batch_size": self.batch_size, "patience": self.patience,
                "min_freq": self.min_freq, "max_vocab": self.max_vocab, "seed": self.seed}

    def _new_net(self) -> BagOfEmbeddings:
        assert self.vocab is not None
        return BagOfEmbeddings(len(self.vocab), len(self.labels), self.dim, self.hidden,
                               self.dropout)

    def fit(self, texts, labels, val=None) -> MLPClassifier:
        torch.manual_seed(self.seed)
        rng = random.Random(self.seed)  # noqa: S311 - shuffling, not security
        self.labels = sorted(set(labels))
        index = {label: i for i, label in enumerate(self.labels)}
        self.vocab = Vocab.build(texts, self.min_freq, self.max_vocab)
        self.net = self._new_net()
        encoded = [self.vocab.encode(t) for t in texts]
        targets = [index[y] for y in labels]
        optimizer = torch.optim.AdamW(self.net.parameters(), lr=self.lr,
                                      weight_decay=self.weight_decay)
        loss_fn = nn.CrossEntropyLoss()
        best_f1, best_state, stale = -1.0, None, 0
        self.history = []
        for epoch in range(1, self.epochs + 1):
            loss = train_epoch(self.net, batches(encoded, targets, self.batch_size, rng),
                               optimizer, loss_fn)
            row = {"epoch": epoch, "train_loss": round(loss, 5)}
            if val is not None and val[0]:
                f1 = macro_f1(val[1], self.predict(val[0]), labels=self.labels)
                row["val_macro_f1"] = round(f1, 5)
                if f1 > best_f1:
                    best_f1, stale = f1, 0
                    best_state = {k: v.clone() for k, v in self.net.state_dict().items()}
                else:
                    stale += 1
            self.history.append(row)
            if val is not None and stale >= self.patience:
                break
        if best_state is not None:
            self.net.load_state_dict(best_state)
        return self

    @torch.inference_mode()
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if self.net is None or self.vocab is None:
            raise RuntimeError("model is not trained")
        self.net.eval()
        out = []
        for start in range(0, len(texts), 512):
            ids, offsets = collate([self.vocab.encode(t) for t in texts[start:start + 512]])
            out.append(torch.softmax(self.net(ids, offsets), dim=1).numpy())
        return np.concatenate(out) if out else np.zeros((0, len(self.labels)))

    def save(self, directory: Path) -> None:
        assert self.net is not None and self.vocab is not None
        directory.mkdir(parents=True, exist_ok=True)
        torch.save(self.net.state_dict(), directory / "weights.pt")
        (directory / "vocab.json").write_text(json.dumps(self.vocab.itos))
        (directory / "model.json").write_text(json.dumps(
            {"labels": self.labels, "params": self.params(), "history": self.history}, indent=2))

    @classmethod
    def load(cls, directory: Path) -> MLPClassifier:
        state = json.loads((directory / "model.json").read_text())
        model = cls(**state["params"])
        model.labels = state["labels"]
        model.history = state.get("history", [])
        model.vocab = Vocab(json.loads((directory / "vocab.json").read_text()))
        model.net = model._new_net()
        model.net.load_state_dict(torch.load(directory / "weights.pt", weights_only=True))
        model.net.eval()
        return model
