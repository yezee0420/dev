from pathlib import Path

from pydantic_settings import BaseSettings

_BASE_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = _BASE_DIR / ".env"
_DEFAULT_DB = f"sqlite:///{_BASE_DIR / 'bugo.db'}"


class Settings(BaseSettings):
    naver_client_id: str = ""
    naver_client_secret: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    crawl_interval_minutes: int = 60

    database_url: str = _DEFAULT_DB

    model_config = {"env_file": str(_ENV_PATH), "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        # 상대 경로 DB URL을 절대 경로로 변환 (실행 위치와 무관하게 동일 DB 사용)
        url = _settings.database_url
        if url.startswith("sqlite:///./") or url == "sqlite:///./bugo.db":
            _settings.database_url = _DEFAULT_DB
    return _settings
