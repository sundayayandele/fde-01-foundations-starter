"""The interface every model implements, so training, evaluation and serving are generic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np


class Classifier(ABC):
    """Text classifier with calibrated-ish class probabilities."""

    kind: str = "base"
    labels: list[str]

    @abstractmethod
    def fit(self, texts: list[str], labels: list[str],
            val: tuple[list[str], list[str]] | None = None) -> Classifier: ...

    @abstractmethod
    def predict_proba(self, texts: list[str]) -> np.ndarray:
        """Shape (n_texts, n_labels); rows sum to 1; columns follow `self.labels`."""

    @abstractmethod
    def save(self, directory: Path) -> None: ...

    @classmethod
    @abstractmethod
    def load(cls, directory: Path) -> Classifier: ...

    def predict(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        probs = self.predict_proba(texts)
        return [self.labels[i] for i in probs.argmax(axis=1)]

    def params(self) -> dict[str, object]:
        """Hyper-parameters recorded in the bundle metadata."""
        return {}
