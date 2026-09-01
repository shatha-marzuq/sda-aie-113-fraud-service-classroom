import csv
from fraud_service.domain.entities import Transaction
from fraud_service.adapters.sklearn_model import SklearnModel

model = SklearnModel("models/fraud_xgb_v3.joblib")
with open("data/transactions_sample.csv", newline="") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i >= 10:
            break
        t = Transaction(
            transaction_id=row["transaction_id"],
            amount_sar=float(row["amount_sar"]),
            merchant_category=row["merchant_category"],
            channel=row["channel"],
            timestamp=row["timestamp"],
        )
        f_ = t.to_features()
        p = model.predict_proba(f_)
        print(row["transaction_id"], f_, "->", p.value)