"""
src/fraud_service/api/schemas.py

عقد النقل (wire contract). extra="forbid" يخلي أي حقل غريب يرجع 422
بصوت عالي، بدل ما يُتجاهل بصمت (قصة amount_sr المذكورة بالسلايد:
عميل أرسل amount_sr بدل amount_sar لمدة 3 أسابيع والنموذج يسجّل درجة
افتراضية بصمت — لو كان extra="forbid" مفعّل، كانت طلعت 422 من أول طلب).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from fraud_service.domain.entities import Decision, Transaction


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(min_length=8, max_length=64)
    amount_sar: float = Field(gt=0, le=1_000_000)
    channel: str
    merchant_category: str
    timestamp: datetime

    def to_domain(self) -> Transaction:
        """الجسر الوحيد بين شكل الشبكة (wire format) والكيان بالـ domain.
        السكيمات ما تتسرب للداخل أبداً — التحويل يصير هنا فقط، سطرين."""
        return Transaction(
            transaction_id=self.transaction_id,
            amount_sar=self.amount_sar,
            merchant_category=self.merchant_category,
            channel=self.channel,
            timestamp=self.timestamp.isoformat(),
        )


class PredictResponse(BaseModel):
    transaction_id: str
    fraud_probability: float = Field(ge=0, le=1)
    decision: Decision
    model_version: str
    trace_id: str


class ErrorBody(BaseModel):
    code: str
    message: str
    trace_id: str


class ErrorEnvelope(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    git_sha: str
    started_at: str


class ReadyResponse(BaseModel):
    status: str
