import json
import pathlib

import pytest

MALFORMED = sorted(pathlib.Path("payloads/malformed").glob("*.json"))


@pytest.mark.integration
def test_predict_contract(client_factory, sample_txn):
    client = client_factory(probability=0.93)  # forces BLOCK
    r = client.post("/v1/predict", json=sample_txn.model_dump())
    assert r.status_code == 200
    assert r.json()["decision"] == "BLOCK"
    assert "X-Trace-Id" in r.headers
    assert 0 <= r.json()["fraud_probability"] <= 1


@pytest.mark.integration
@pytest.mark.parametrize("payload_file", MALFORMED)
def test_malformed_corpus_rejected(client_factory, payload_file):
    r = client_factory().post(
        "/v1/predict",
        content=payload_file.read_bytes(),
        headers={"content-type": "application/json"},
    )
    assert 400 <= r.status_code < 500, payload_file.name


@pytest.mark.integration
def test_predict_500_no_stack_trace(client_factory, sample_txn, monkeypatch):
    client = client_factory()

    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure")

    from fraud_service.service.scorer import FraudScorer
    monkeypatch.setattr(FraudScorer, "score", boom)
    r = client.post("/v1/predict", json=sample_txn.model_dump())
    assert r.status_code == 500
    body = r.json()
    assert "RuntimeError" not in json.dumps(body)
    assert "simulated failure" not in json.dumps(body)
    assert "trace_id" in body["error"]


@pytest.mark.integration
def test_ready_503_when_no_scorer(client_factory):
    app = client_factory().app
    app.dependency_overrides.clear()
    from fastapi.testclient import TestClient
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/v1/ready")
    assert r.status_code == 503