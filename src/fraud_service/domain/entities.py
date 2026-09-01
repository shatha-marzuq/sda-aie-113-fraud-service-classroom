import dataclasses
import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


# Same column names and order the model was trained on - shared by
# training and serving so they can never quietly disagree.
FEATURE_COLS = ["amount_log", "channel", "mcc", "hour_of_day", "is_night"]


@dataclass
class FeatureVector:
    amount_log: float
    channel: str
    mcc: str
    hour_of_day: int
    is_night: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount_log": self.amount_log,
            "channel": self.channel,
            "mcc": self.mcc,
            "hour_of_day": self.hour_of_day,
            "is_night": self.is_night,
        }

    @property
    def values(self) -> dict[str, Any]:
        return self.to_dict()


@dataclass
class RawScore:
    value: float


@dataclass
class Transaction:
    transaction_id: str
    amount_sar: float
    merchant_category: str
    channel: str
    timestamp: str  # raw string as read from the CSV

    def to_features(self) -> FeatureVector:
        # Mirrors notebook_v1.ipynb exactly - same transformations, same
        # column names, so training and serving never disagree on a feature.
        amount_log = math.log1p(self.amount_sar)
        mcc = self.merchant_category.strip().upper().replace(" ", "_")
        hour_of_day = datetime.fromisoformat(self.timestamp).hour
        is_night = 1 if hour_of_day < 6 else 0

        return FeatureVector(
            amount_log=amount_log,
            channel=self.channel,
            mcc=mcc,
            hour_of_day=hour_of_day,
            is_night=is_night,
        )

    def model_dump(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class FraudScore:
    transaction_id: str
    probability: float
    decision: Decision
    model_version: str