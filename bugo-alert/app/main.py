"""BugoAlert — FastAPI 앱 엔트리포인트."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import init_db
from app.scheduler.jobs import run_crawl_job
from app.routers import obituaries, favorites, flower_order

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("DB 테이블 초기화 완료")

    settings = get_settings()
    scheduler.add_job(
        run_crawl_job,
        "interval",
        minutes=settings.crawl_interval_minutes,
        id="crawl_obituaries",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("스케줄러 시작 (주기=%d분)", settings.crawl_interval_minutes)

    yield

    scheduler.shutdown(wait=False)
    logger.info("스케줄러 종료")


app = FastAPI(title="BugoAlert", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(obituaries.router)
app.include_router(favorites.router)
app.include_router(flower_order.router)


@app.get("/api/crawl-now")
async def trigger_crawl():
    """수동 크롤링 트리거 (디버그/테스트용)."""
    from app.scheduler.jobs import crawl_and_notify
    await crawl_and_notify()
    return {"status": "ok", "message": "크롤링 완료"}
