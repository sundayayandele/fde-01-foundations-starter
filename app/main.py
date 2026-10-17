"""Complaint-routing API: predict a label, decide auto-route or human review, serve a small UI.

Complaint text is never logged or stored by this service; only counts and timings are
exported as metrics.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel, Field

from complaint_router import __version__
from complaint_router.config import get_settings
from complaint_router.models.base import Classifier
from complaint_router.registry import list_bundles, load_bundle
from complaint_router.routing import route

settings = get_settings()
app = FastAPI(title="Complaint router", version=__version__,
              description="Routes complaint text to a product/intent, or to a human when unsure.")
app.mount("/metrics", make_asgi_app())

UI = Path(__file__).parent / "static" / "index.html"

REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "route", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "route"])
PREDICTIONS = Counter("predictions_total", "Predictions made", ["model", "route"])
CONFIDENCE = Histogram("prediction_confidence", "Top-class probability", ["model"],
                       buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0))
INFERENCE = Histogram("model_inference_seconds", "Model inference time per request", ["model"],
                      buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5))

_models: dict[str, tuple[Classifier, dict]] = {}
_lock = threading.Lock()


def bundles() -> dict[str, dict]:
    return {b["name"]: b for b in list_bundles(Path(settings.model_dir))}


def get_model(name: str | None) -> tuple[str, Classifier, dict]:
    available = bundles()
    if not available:
        raise HTTPException(status_code=503, detail="no trained model available; "
                            "run `complaint-router train` or use an image with baked models")
    name = name or (settings.serve_model if settings.serve_model in available
                    else sorted(available)[0])
    if name not in available:
        raise HTTPException(status_code=404, detail=f"unknown model {name!r}; "
                            f"available: {sorted(available)}")
    with _lock:
        if name not in _models:
            _models[name] = load_bundle(Path(available[name]["path"]))
    model, meta = _models[name]
    return name, model, meta


@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    path = getattr(request.scope.get("route"), "path", "unmatched")
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui() -> str:
    return UI.read_text(encoding="utf-8")


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict:
    """Ready once the model directory is readable. Reports how many models are available;
    prediction endpoints return 503 while there are none (see ADR-005)."""
    available = bundles()
    return {"status": "ready", "version": __version__, "environment": settings.environment,
            "models": len(available), "default_model": settings.serve_model,
            "default_available": settings.serve_model in available}


@app.get("/api/v1/models")
def models() -> list[dict]:
    return [{"name": n, "kind": b["kind"], "dataset": b["dataset"], "target": b["target"],
             "dataset_version": b["dataset_version"], "labels": len(b["labels"]),
             "metrics": {k: v for k, v in b.get("metrics", {}).items() if k.startswith("test_")},
             "created_at": b["created_at"], "default": n == settings.serve_model}
            for n, b in sorted(bundles().items())]


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=settings.max_text_chars)
    model: str | None = Field(default=None, description="<dataset>/<kind>; default SERVE_MODEL")


class BatchRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=settings.max_batch)
    model: str | None = None


def _decide(name: str, model: Classifier, texts: list[str]) -> list[dict]:
    t0 = time.perf_counter()
    probs = model.predict_proba(texts)
    INFERENCE.labels(name).observe(time.perf_counter() - t0)
    out = []
    for p in probs:
        decision = route(p, model.labels, settings.route_threshold, settings.route_margin)
        PREDICTIONS.labels(name, decision["route"]).inc()
        CONFIDENCE.labels(name).observe(decision["confidence"])
        out.append(decision)
    return out


@app.post("/api/v1/predict")
def predict(req: PredictRequest) -> dict:
    if not req.text.strip():
        raise HTTPException(status_code=422, detail="text is blank")
    name, model, meta = get_model(req.model)
    t0 = time.perf_counter()
    decision = _decide(name, model, [req.text])[0]
    return {"model": name, "target": meta["target"], **decision,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 2)}


@app.post("/api/v1/predict/batch")
def predict_batch(req: BatchRequest) -> dict:
    if any(len(t) > settings.max_text_chars or not t.strip() for t in req.texts):
        raise HTTPException(status_code=422, detail="each text must be non-blank and at most "
                            f"{settings.max_text_chars} characters")
    name, model, meta = get_model(req.model)
    decisions = _decide(name, model, req.texts)
    return {"model": name, "target": meta["target"], "count": len(decisions),
            "auto": sum(d["route"] == "auto" for d in decisions), "items": decisions}
