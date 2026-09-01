import csv
import pathlib

import pytest

pytestmark = pytest.mark.behavioural


def _score(model, txn_dict):
    from fraud_service.domain.entities import Transaction
    txn = Transaction(**txn_dict)
    return model.predict_proba(txn.to_features()).value


def test_invariance_to_merchant_casing(real_model, sample_txn):
    a = _score(real_model, sample_txn)
    b = _score(real_model, {**sample_txn, "merchant_category": "GROCERY"})
    assert a == pytest.approx(b, abs=1e-9)


def test_directional_amount(real_model, sample_txn):
    small = _score(real_model, {**sample_txn, "amount_sar": 50.0})
    large = _score(real_model, {**sample_txn, "amount_sar": 50_000.0})
    assert large >= small - 1e-6


GOLDEN_PATH = pathlib.Path("models/golden_scores_v3.csv")


@pytest.mark.slow
@pytest.mark.skipif(not GOLDEN_PATH.exists(), reason="golden file not generated yet")
def test_golden_scores(real_model):
    with GOLDEN_PATH.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            txn = {
                "transaction_id": row["transaction_id"],
                "amount_sar": float(row["amount_sar"]),
                "channel": row["channel"],
                "merchant_category": row["merchant_category"],
                "timestamp": row["timestamp"],
            }
            expected = float(row["probability"])
            actual = _score(real_model, txn)
            assert actual == pytest.approx(expected, abs=1e-6), row["transaction_id"]