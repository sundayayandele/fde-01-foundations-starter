import numpy as np
import pytest

from complaint_router.routing import route

pytestmark = pytest.mark.exercise
LABELS = ["card_arrival", "lost_card", "refund"]


def test_confident_prediction_is_auto_routed():
    d = route(np.array([0.1, 0.8, 0.1]), LABELS)
    assert d == {"label": "lost_card", "confidence": 0.8, "route": "auto", "reason": "confident",
                 "top": [{"label": "lost_card", "probability": 0.8},
                         {"label": "card_arrival", "probability": 0.1},
                         {"label": "refund", "probability": 0.1}]}


def test_low_confidence_goes_to_human():
    d = route(np.array([0.45, 0.35, 0.2]), LABELS, threshold=0.5)
    assert (d["route"], d["reason"]) == ("human", "low_confidence")


def test_close_call_goes_to_human():
    d = route(np.array([0.55, 0.5, 0.0]), LABELS, threshold=0.5, margin=0.1)
    assert (d["route"], d["reason"]) == ("human", "ambiguous")


def test_top_k_and_single_class():
    assert len(route(np.array([0.2, 0.3, 0.5]), LABELS, top_k=2)["top"]) == 2
    d = route(np.array([1.0]), ["only"])
    assert (d["label"], d["route"]) == ("only", "auto")
