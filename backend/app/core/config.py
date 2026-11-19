import json
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Inventory Intelligence API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./inventory_intelligence.db"
    secret_key: str = "replace-this-development-secret-before-deployment"
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("["):
                parsed = json.loads(value)
                if not isinstance(parsed, list):
                    raise ValueError("CORS_ORIGINS must be a JSON array or comma-separated origins.")
                return parsed
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def validate_runtime(self) -> None:
        if self.environment.lower() in {"production", "prod"}:
            if self.secret_key == "replace-this-development-secret-before-deployment":
                raise RuntimeError("Set SECRET_KEY to a strong random value before production.")
            if len(self.secret_key) < 32:
                raise RuntimeError("Production SECRET_KEY must be at least 32 characters.")
            if not self.cors_origins or "*" in self.cors_origins:
                raise RuntimeError("Production CORS origins must be explicit.")


settings = Settings()
settings.validate_runtime()
