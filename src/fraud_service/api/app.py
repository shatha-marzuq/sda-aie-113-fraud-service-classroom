import math
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import structlog
from fraud_service.adapters.sklearn_model import SklearnModel
from fraud_service.api.routes import router
from fraud_service.api.schemas import ErrorBody, ErrorEnvelope
from fraud_service.config import Settings
from fraud_service.domain.entities import FeatureVector
from fraud_service.logging_setup import configure_logging, log
from fraud_service.service.scorer import FraudScorer


def _warmup_features() -> FeatureVector:

    return FeatureVector(amount_log=0.0, channel="POS", mcc="0000", hour_of_day=12, is_night=0)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    configure_logging(settings.log_level)

    t0 = time.perf_counter()

    model = SklearnModel(str(settings.model_path))
    model.predict_proba(_warmup_features())  # warm-up

    log.info(
        f"model_loaded version={model.model_version} "
        f"seconds={round(time.perf_counter() - t0, 3)}"
    )

    app.state.scorer = FraudScorer(model=model, block_threshold=settings.block_threshold)
    app.state.started_at = datetime.now(UTC)
    app.state.git_sha = settings.git_sha
    yield
    log.info("shutdown_complete")


async def trace_and_timing_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = str(uuid.uuid4())
    request.state.trace_id = trace_id

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        trace_id=trace_id, path=request.url.path, method=request.method
    )

    t0 = time.perf_counter()

    response = await call_next(request)

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    log.info("http_request", status=response.status_code, latency_ms=latency_ms)

    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Response-Time-Ms"] = str(latency_ms)
    return response


def _json_safe(value: Any) -> Any:
    """422 error bodies echo back the raw input value. If that value is a
    non-finite float (inf/-inf/nan), strict JSON serialization crashes with
    a 500 instead of returning the 422 the client actually earned."""
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.middleware("http")(trace_and_timing_middleware)
    app.include_router(router, prefix="/v1")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = exc.errors()
        for error in errors:
            if "input" in error:
                error["input"] = _json_safe(error["input"])
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(errors)},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        
        trace_id = getattr(request.state, "trace_id", "unknown")
        log.exception(f"unhandled_exception trace_id={trace_id}")
        return JSONResponse(
            status_code=500,
            content=ErrorEnvelope(
                error=ErrorBody(
                    code="INTERNAL_ERROR",
                    message="Something went wrong. Reference the trace_id when reporting this.",
                    trace_id=trace_id,
                )
            ).model_dump(),
        )

    return app


app = create_app()