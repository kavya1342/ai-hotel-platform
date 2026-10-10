from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Hotel Operations API"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    initial_manager_name: str = "Hotel Manager"
    initial_manager_email: str
    initial_manager_password: str
    gemini_api_key: str


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()