import pytest
from fastapi.testclient import TestClient

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.app import create_app
from fraud_service.api.routes import get_scorer
from fraud_service.domain.entities import RawScore, Transaction
from fraud_service.service.scorer import FraudScorer


class ConstantModel:
    """A double, not a mock — implements the Model protocol, drives
    every policy branch, zero sklearn."""
    def __init__(self, p, version="test-1"):
        self._p, self.model_version = p, version

    def predict_proba(self, features):
        return RawScore(value=self._p)


@pytest.fixture
def client_factory():
    def _make(probability=0.10, threshold=0.85):
        app = create_app()
        scorer = FraudScorer(
            model=ConstantModel(probability),
            block_threshold=threshold,
        )
        app.dependency_overrides[get_scorer] = lambda: scorer
        return TestClient(app, raise_server_exceptions=False)
    return _make


@pytest.fixture(scope="session")
def real_model():
    return SklearnModel("models/fraud_xgb_v3.joblib")


@pytest.fixture
def sample_txn():
    return Transaction(
        transaction_id="TXN-TEST-00000001",
        amount_sar=250,
        channel="pos",
        merchant_category="grocery",
        timestamp="2026-09-01T03:30:00Z",
    )