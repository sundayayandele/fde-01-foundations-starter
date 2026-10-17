import pytest
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)


@pytest.fixture
def with_models(model_dir, monkeypatch):
    monkeypatch.setattr(main.settings, "model_dir", str(model_dir))
    monkeypatch.setattr(main.settings, "serve_model", "fixture/baseline")
    main._models.clear()
    yield
    main._models.clear()


def test_live_and_ui():
    assert client.get("/health/live").json() == {"status": "ok"}
    r = client.get("/")
    assert r.status_code == 200 and "Complaint router" in r.text


def test_ready_without_models():
    body = client.get("/health/ready").json()
    assert body["status"] == "ready" and body["models"] == 0
    assert body["default_available"] is False


def test_predict_without_models_is_503():
    r = client.post("/api/v1/predict", json={"text": "my card is lost"})
    assert r.status_code == 503 and "no trained model" in r.json()["detail"]
    assert client.get("/api/v1/models").json() == []


@pytest.mark.parametrize("payload", [{"text": ""}, {"text": "x" * 5001}, {}, {"text": "   "}])
def test_predict_validation(payload):
    assert client.post("/api/v1/predict", json=payload).status_code == 422


def test_batch_validation():
    assert client.post("/api/v1/predict/batch", json={"texts": []}).status_code == 422
    assert client.post("/api/v1/predict/batch",
                       json={"texts": ["x"] * 257}).status_code == 422
    assert client.post("/api/v1/predict/batch", json={"texts": ["ok", " "]}).status_code == 422


def test_metrics_exposed():
    client.get("/health/live")
    text = client.get("/metrics/").text
    assert "http_requests_total" in text


@pytest.mark.exercise
def test_models_listed(with_models):
    models = client.get("/api/v1/models").json()
    assert [m["name"] for m in models] == ["fixture/baseline", "fixture/mlp"]
    assert models[0]["default"] is True and models[0]["labels"] == 4
    assert client.get("/health/ready").json()["default_available"] is True


@pytest.mark.exercise
def test_predict_default_and_named_model(with_models):
    r = client.post("/api/v1/predict", json={"text": "my visa card was stolen"})
    body = r.json()
    assert r.status_code == 200
    assert body["model"] == "fixture/baseline" and body["label"] == "lost_card"
    assert body["route"] in {"auto", "human"} and len(body["top"]) == 3
    r = client.post("/api/v1/predict", json={"text": "refund this fee", "model": "fixture/mlp"})
    assert r.json()["model"] == "fixture/mlp"
    assert client.post("/api/v1/predict", json={"text": "x", "model": "nope/x"}).status_code == 404
    assert "predictions_total" in client.get("/metrics/").text


@pytest.mark.exercise
def test_predict_batch(with_models):
    r = client.post("/api/v1/predict/batch",
                    json={"texts": ["where is my new card", "the wire failed"]})
    body = r.json()
    assert body["count"] == 2 and [i["label"] for i in body["items"]] == \
        ["card_arrival", "transfer_failed"]


@pytest.mark.exercise
def test_default_falls_back_when_serve_model_missing(with_models, monkeypatch):
    monkeypatch.setattr(main.settings, "serve_model", "banking77/baseline")
    r = client.post("/api/v1/predict", json={"text": "my card has not arrived"})
    assert r.json()["model"] == "fixture/baseline"
