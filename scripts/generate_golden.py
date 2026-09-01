import csv
from pathlib import Path

from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.domain.entities import Transaction

model = SklearnModel("models/fraud_xgb_v3.joblib")
out = Path("models/golden_scores_v3.csv")

with open("data/transactions_sample.csv", newline="") as f_in, out.open("w", newline="") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.writer(f_out)
    writer.writerow(["transaction_id", "amount_sar", "channel", "merchant_category", "timestamp", "probability"])
    for row in reader:
        txn = Transaction(
            transaction_id=row["transaction_id"],
            amount_sar=float(row["amount_sar"]),
            merchant_category=row["merchant_category"],
            channel=row["channel"],
            timestamp=row["timestamp"],
        )
        p = model.predict_proba(txn.to_features()).value
        writer.writerow([row["transaction_id"], row["amount_sar"], row["channel"], row["merchant_category"], row["timestamp"], p])

print(f"Wrote {out}")