"""Turn class probabilities into a routing decision a complaints team can act on."""

from __future__ import annotations

import numpy as np


def route(probs: np.ndarray, labels: list[str], threshold: float = 0.5,
          margin: float = 0.1, top_k: int = 3) -> dict:
    """Decide whether one prediction is auto-routed or sent to a human.

    Returns {"label", "confidence", "route", "reason", "top"} where:
    - label/confidence: the most probable class and its probability (rounded to 4 places)
    - top: the top_k classes as [{"label", "probability"}], most probable first
    - route: "human" if confidence < threshold, or if the gap between the first and second
      probabilities is < margin; otherwise "auto"
    - reason: "low_confidence", "ambiguous" or "confident" (low confidence wins over ambiguous)
    """
    raise NotImplementedError("TODO week-10 confidence-based routing: see labs/")
