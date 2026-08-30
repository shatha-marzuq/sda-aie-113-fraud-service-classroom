import csv
from pathlib import Path

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.domain.entities import Transaction
from fraud_service.service.scorer import FraudScorer

DATA_PATH = Path("data/transactions_sample.csv")
MODEL_PATH = Path("models/fraud_xgb_v3.joblib")
OUTPUT_PATH = Path("scored.csv")
BLOCK_THRESHOLD = 0.85


def main() -> None:
    model = SklearnModel(str(MODEL_PATH))
    scorer = FraudScorer(model=model, block_threshold=BLOCK_THRESHOLD)

    counts = {"ALLOW": 0, "REVIEW": 0, "BLOCK": 0}

    with DATA_PATH.open(newline="") as f_in, OUTPUT_PATH.open(
        "w", newline=""
    ) as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(
            ["transaction_id", "probability", "decision", "model_version"]
        )

        for row in reader:
            txn = Transaction(
                transaction_id=row["transaction_id"],
                amount_sar=float(row["amount_sar"]),
                merchant_category=row["merchant_category"],
                channel=row["channel"],
                timestamp=row["timestamp"],
            )
            score = scorer.score(txn)
            counts[score.decision.value] += 1
            writer.writerow(
                [
                    score.transaction_id,
                    score.probability,
                    score.decision.value,
                    score.model_version,
                ]
            )

    print(
        f"Loaded model {model.model_version} - "
        f"Scored {sum(counts.values())} transactions -> {OUTPUT_PATH} "
        f"(block: {counts['BLOCK']}, review: {counts['REVIEW']}, "
        f"allow: {counts['ALLOW']})"
    )


if __name__ == "__main__":
    main()