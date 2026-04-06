from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    naver_client_id: str = ""
    naver_client_secret: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    crawl_interval_minutes: int = 60

    database_url: str = "sqlite:///./bugo.db"

    model_config = {"env_file": str(_ENV_PATH), "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
