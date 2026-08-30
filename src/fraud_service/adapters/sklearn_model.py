import joblib
import pandas as pd

from fraud_service.domain.entities import FeatureVector, RawScore


class SklearnModel:
    def __init__(self, model_path: str):
        bundle = joblib.load(model_path)
        self.pipeline = bundle["pipeline"]
        self.model_version = bundle["version"]

    def predict_proba(self, features: FeatureVector) -> RawScore:
        row = pd.DataFrame([features.to_dict()])
        proba = self.pipeline.predict_proba(row)[0][1]
        return RawScore(value=float(proba))