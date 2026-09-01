from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="FRAUD_",
        env_file=".env",
        extra="forbid",
    )

    model_path: Path = Field(
        default=Path("models/fraud_xgb_v3.joblib"),
        description="joblib bundle",
    )
    block_threshold: float = Field(
        default=0.85, ge=0.5, le=0.99,
        description="Risk-approved block threshold",
    )
    log_level: str = Field(default="INFO")
    git_sha: str = Field(default="dev")
    registry_token: SecretStr | None = Field(default=None)

    @field_validator("model_path")
    @classmethod
    def model_file_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"artefact not found: {v}")
        return v