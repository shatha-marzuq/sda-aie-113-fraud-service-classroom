from datetime import UTC, datetime
from typing import cast
from fraud_service.logging_setup import log
from fastapi import APIRouter, Depends, HTTPException, Request

from fraud_service.api.schemas import (
    HealthResponse,
    PredictRequest,
    PredictResponse,
    ReadyResponse,
)
from fraud_service.service.scorer import FraudScorer

router = APIRouter()


def get_scorer(request: Request) -> FraudScorer:
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:  # startup incomplete/failed
        raise HTTPException(
            status_code=503,
            detail="Model not ready",
            headers={"Retry-After": "5"},
        )
    return cast(FraudScorer, scorer)


@router.post("/predict", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    request: Request,
    scorer: FraudScorer = Depends(get_scorer),
) -> PredictResponse:
    score = scorer.score(body.to_domain())

    log.info(
        "prediction_served",
        decision=score.decision.value,
        probability_bucket=round(score.probability, 1),
        model_version=score.model_version,
    )
    # ABSENT by design: customer_id, amount, raw features

    return PredictResponse(
        transaction_id=score.transaction_id,
        fraud_probability=round(score.probability, 6),
        decision=score.decision,
        model_version=score.model_version,
        trace_id=request.state.trace_id,
    )

@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
  
    return HealthResponse(
        status="alive",
        git_sha=getattr(request.app.state, "git_sha", "dev"),
        started_at=getattr(request.app.state, "started_at", datetime.now(UTC)).isoformat(),
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request) -> ReadyResponse:
   
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not ready",
            headers={"Retry-After": "5"},
        )
    return ReadyResponse(status="ready")