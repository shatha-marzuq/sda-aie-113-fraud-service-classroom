import dataclasses

import pytest

from fraud_service.domain.entities import Transaction

pytestmark = pytest.mark.behavioural


def _score(model, txn: Transaction) -> float:
    return model.predict_proba(txn.to_features()).value


def test_invariance_to_merchant_casing(real_model, sample_txn):
    a = _score(real_model, sample_txn)
    b = _score(
        real_model,
        dataclasses.replace(sample_txn, merchant_category=sample_txn.merchant_category.upper()),
    )
    assert a == pytest.approx(b, abs=1e-9)


def test_directional_amount(real_model, sample_txn):
    small = _score(real_model, dataclasses.replace(sample_txn, amount_sar=50.0))
    large = _score(real_model, dataclasses.replace(sample_txn, amount_sar=50_000.0))
    assert large >= small - 1e-6
    