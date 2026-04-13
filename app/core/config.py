"""FastAPI configuration layer.

Keeps new ASGI settings isolated from legacy Flask config and allows
incremental migration with minimal coupling.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the FastAPI application."""

    app_name: str = "questionsapp-fastapi"
    app_version: str = "1.0.0"
    api_prefix: str = Field(default="/eduportal/questions")

    # Middleware/infrastructure
    enable_cors: bool = True
    cors_allow_origins: list[str] = ["*"]
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # HTTP compatibility behavior
    include_request_id_header: bool = True

    model_config = SettingsConfigDict(
        env_prefix="FASTAPI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
