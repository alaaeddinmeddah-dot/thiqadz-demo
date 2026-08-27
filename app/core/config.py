from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ThiqaDZ"
    app_env: str = "local"
    database_url: str = "sqlite:///./thiqa.db"
    auto_seed_demo: bool = True
    demo_username: str = "demo"
    demo_password: str = "demo123"
    refused_delivery_loss_dzd: int = 700
    allowed_origins: list[str] = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://0.0.0.0:8000",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
