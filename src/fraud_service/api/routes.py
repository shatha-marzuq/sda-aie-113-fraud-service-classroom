"""
src/fraud_service/api/routes.py

تنبيه مهم من السلايد: كل الدوال هنا "def" عادية، مو "async def".
sklearn inference عملية CPU-bound؛ FastAPI يشغّل "def" داخل thread pool.
"async def" هنا يوقف الـ event loop كامل — السبب رقم 1 لـ"FastAPI بطيء".
الفرق مقاس فعليًا بالسلايد: p99 يقفز من 38ms إلى 2.4s لو غلطت هالغلطة.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from fraud_service.api.schemas import HealthResponse, PredictRequest, PredictResponse, ReadyResponse
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
    return scorer


@router.post("/predict", response_model=PredictResponse)
def predict(
    body: PredictRequest,
    request: Request,
    scorer: FraudScorer = Depends(get_scorer),
):
    score = scorer.score(body.to_domain())
    return PredictResponse(
        transaction_id=score.transaction_id,
        fraud_probability=round(score.probability, 6),
        decision=score.decision,
        model_version=score.model_version,
        trace_id=request.state.trace_id,
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request):
    """الحيوية (liveness): "هل العملية حية؟" — بدون أي I/O إطلاقاً.
    لو هذا الراوت يفحص النموذج، تحميل بطيء = القرين يقتل الحاوية
    منتصف التحميل = restart storm (بالضبط المذكور بسلايد 41)."""
    return HealthResponse(
        status="alive",
        git_sha=getattr(request.app.state, "git_sha", "dev"),
        started_at=getattr(request.app.state, "started_at", datetime.now(timezone.utc)).isoformat(),
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(request: Request):
    """الجاهزية (readiness): "أقدر أخدم صح الحين؟" — يفحص إن النموذج
    محمّل. يرجع 503 وقت الإحماء؛ موازن الأحمال يوجّه المرور بناءً عليه."""
    scorer = getattr(request.app.state, "scorer", None)
    if scorer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not ready",
            headers={"Retry-After": "5"},
        )
    return ReadyResponse(status="ready")
