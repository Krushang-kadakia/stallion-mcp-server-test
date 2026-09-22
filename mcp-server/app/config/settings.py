from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    backend_base_url: str = "https://api.dev.batman.co.in"
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    http_timeout: float = 30.0
    jwt_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
