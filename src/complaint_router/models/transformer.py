"""Fine-tuned pretrained transformer (Hugging Face), e.g. distilbert-base-uncased.

Optional: install with `pip install -e ".[transformer]"`. Weights are downloaded from the
Hugging Face Hub on first use. Plain PyTorch loop (no Trainer) so every step is visible:
AdamW, linear warm-up and decay, early stopping on validation macro-F1.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
import torch

from complaint_router.metrics import macro_f1
from complaint_router.models.base import Classifier
from complaint_router.text import normalise


class TransformerClassifier(Classifier):
    kind = "transformer"

    def __init__(self, base_model: str = "distilbert-base-uncased", max_length: int = 64,
                 lr: float = 5e-5, epochs: int = 4, batch_size: int = 32,
                 warmup_ratio: float = 0.1, weight_decay: float = 0.01, patience: int = 2,
                 seed: int = 42, *, model=None, tokenizer=None) -> None:
        self.base_model, self.max_length = base_model, max_length
        self.lr, self.epochs, self.batch_size = lr, epochs, batch_size
        self.warmup_ratio, self.weight_decay = warmup_ratio, weight_decay
        self.patience, self.seed = patience, seed
        self.model = model          # injectable for tests (tiny offline models)
        self.tokenizer = tokenizer
        self.labels: list[str] = []
        self.history: list[dict[str, float]] = []

    def params(self) -> dict[str, object]:
        return {"base_model": self.base_model, "max_length": self.max_length, "lr": self.lr,
                "epochs": self.epochs, "batch_size": self.batch_size,
                "warmup_ratio": self.warmup_ratio, "weight_decay": self.weight_decay,
                "patience": self.patience, "seed": self.seed}

    def _encode(self, texts: list[str]):
        return self.tokenizer([normalise(t) for t in texts], truncation=True, padding=True,
                              max_length=self.max_length, return_tensors="pt")

    def fit(self, texts, labels, val=None) -> TransformerClassifier:
        from transformers import (  # lazy: optional dependency
            AutoModelForSequenceClassification,
            AutoTokenizer,
            get_linear_schedule_with_warmup,
        )

        torch.manual_seed(self.seed)
        rng = random.Random(self.seed)  # noqa: S311 - shuffling, not security
        self.labels = sorted(set(labels))
        index = {label: i for i, label in enumerate(self.labels)}
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if self.model is None:
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.base_model, num_labels=len(self.labels),
                id2label=dict(enumerate(self.labels)), label2id=index)
        targets = [index[y] for y in labels]
        steps = math.ceil(len(texts) / self.batch_size) * self.epochs
        no_decay = ("bias", "LayerNorm.weight", "layer_norm.weight")
        groups = [
            {"params": [p for n, p in self.model.named_parameters()
                        if not any(k in n for k in no_decay)], "weight_decay": self.weight_decay},
            {"params": [p for n, p in self.model.named_parameters()
                        if any(k in n for k in no_decay)], "weight_decay": 0.0},
        ]
        optimizer = torch.optim.AdamW(groups, lr=self.lr)
        scheduler = get_linear_schedule_with_warmup(optimizer, int(steps * self.warmup_ratio),
                                                    steps)
        best_f1, best_state, stale = -1.0, None, 0
        self.history = []
        for epoch in range(1, self.epochs + 1):
            self.model.train()
            order = list(range(len(texts)))
            rng.shuffle(order)
            total = 0.0
            for start in range(0, len(order), self.batch_size):
                idx = order[start:start + self.batch_size]
                batch = self._encode([texts[i] for i in idx])
                y = torch.tensor([targets[i] for i in idx])
                out = self.model(**batch, labels=y)
                out.loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                total += out.loss.item() * len(idx)
            row = {"epoch": epoch, "train_loss": round(total / len(texts), 5)}
            if val is not None and val[0]:
                f1 = macro_f1(val[1], self.predict(val[0]), labels=self.labels)
                row["val_macro_f1"] = round(f1, 5)
                if f1 > best_f1:
                    best_f1, stale = f1, 0
                    best_state = {k: v.detach().clone() for k, v in
                                  self.model.state_dict().items()}
                else:
                    stale += 1
            self.history.append(row)
            if val is not None and stale >= self.patience:
                break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        return self

    @torch.inference_mode()
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("model is not trained")
        self.model.eval()
        out = []
        for start in range(0, len(texts), 64):
            batch = self._encode(texts[start:start + 64])
            out.append(torch.softmax(self.model(**batch).logits, dim=1).numpy())
        return np.concatenate(out) if out else np.zeros((0, len(self.labels)))

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(directory / "hf")
        self.tokenizer.save_pretrained(directory / "hf")
        (directory / "model.json").write_text(json.dumps(
            {"labels": self.labels, "params": self.params(), "history": self.history}, indent=2))

    @classmethod
    def load(cls, directory: Path) -> TransformerClassifier:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        state = json.loads((directory / "model.json").read_text())
        model = cls(**state["params"],
                    model=AutoModelForSequenceClassification.from_pretrained(directory / "hf"),
                    tokenizer=AutoTokenizer.from_pretrained(directory / "hf"))
        model.labels = state["labels"]
        model.history = state.get("history", [])
        model.model.eval()
        return model
