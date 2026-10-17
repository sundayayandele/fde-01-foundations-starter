"""Baseline: TF-IDF features + logistic regression (scikit-learn)."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from complaint_router.models.base import Classifier
from complaint_router.text import normalise


def build_pipeline(c: float = 10.0, max_features: int = 50_000, seed: int = 42) -> Pipeline:
    """TF-IDF on word 1-2-grams and character 2-5-grams, then multinomial logistic regression.

    - word vectoriser: analyzer="word", ngram_range=(1, 2), sublinear_tf=True, min_df=1,
      max_features=max_features, preprocessor=normalise
    - char vectoriser: analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2,
      max_features=max_features, preprocessor=normalise
    - combine them with FeatureUnion as steps "word" and "char"
    - classifier: LogisticRegression(C=c, max_iter=3000, random_state=seed)
    Return Pipeline([("features", union), ("clf", classifier)]).
    """
    raise NotImplementedError("TODO week-06 TF-IDF + logistic regression pipeline: see labs/")


class BaselineClassifier(Classifier):
    kind = "baseline"

    def __init__(self, c: float = 10.0, max_features: int = 50_000, seed: int = 42) -> None:
        self.c = c
        self.max_features = max_features
        self.seed = seed
        self.pipeline: Pipeline | None = None
        self.labels: list[str] = []

    def fit(self, texts, labels, val=None) -> BaselineClassifier:
        self.pipeline = build_pipeline(self.c, self.max_features, self.seed)
        self.pipeline.fit(texts, labels)
        self.labels = [str(x) for x in self.pipeline.classes_]
        return self

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        if self.pipeline is None:
            raise RuntimeError("model is not trained")
        return self.pipeline.predict_proba(texts)

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "labels": self.labels, "params": self.params()},
                    directory / "model.joblib")

    @classmethod
    def load(cls, directory: Path) -> BaselineClassifier:
        # Only load bundles you trained yourself: joblib files can execute code on load.
        state = joblib.load(directory / "model.joblib")
        model = cls(**state["params"])
        model.pipeline = state["pipeline"]
        model.labels = state["labels"]
        return model

    def params(self) -> dict[str, object]:
        return {"c": self.c, "max_features": self.max_features, "seed": self.seed}
