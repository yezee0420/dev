from pydantic_settings import BaseSettings
from functools import lru_cache


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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
