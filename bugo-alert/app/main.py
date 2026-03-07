"""BugoAlert — FastAPI 앱 엔트리포인트."""

from __future__ import annotations

import logging
import threading
import webbrowser
from contextlib import asynccontextmanager
from datetime import datetime
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

PORT = 8000


def _open_browser():
    """서버 준비 후 브라우저를 자동으로 연다."""
    import time
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORT}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("DB 테이블 초기화 완료")

    # 크롤링 상태 초기화
    app.state.crawl_status = {
        "last_run": None,
        "last_count": 0,
        "is_running": False,
        "last_error": None,
    }

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

    # 서버 시작 시 즉시 첫 크롤링 실행
    if settings.naver_client_id and settings.naver_client_id != "your_naver_client_id":
        scheduler.add_job(run_crawl_job, id="initial_crawl", replace_existing=True)
        logger.info("첫 크롤링 즉시 실행 예약됨")
    else:
        logger.warning("⚠ NAVER API 키 미설정 — .env 파일에 NAVER_CLIENT_ID/SECRET을 입력하세요")

    # 브라우저 자동 열기
    threading.Thread(target=_open_browser, daemon=True).start()

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
    """수동 크롤링 트리거."""
    from app.scheduler.jobs import crawl_and_notify

    status = app.state.crawl_status
    if status["is_running"]:
        return {"status": "busy", "message": "크롤링이 이미 진행 중입니다"}

    status["is_running"] = True
    try:
        count = await crawl_and_notify()
        status["last_run"] = datetime.now()
        status["last_count"] = count or 0
        status["last_error"] = None
        return {"status": "ok", "message": f"크롤링 완료 — 신규 {count or 0}건"}
    except Exception as e:
        status["last_error"] = str(e)
        return {"status": "error", "message": str(e)}
    finally:
        status["is_running"] = False


@app.get("/api/crawl-status")
async def crawl_status():
    """현재 크롤링 상태를 반환한다."""
    s = app.state.crawl_status
    return {
        "is_running": s["is_running"],
        "last_run": s["last_run"].strftime("%Y-%m-%d %H:%M:%S") if s["last_run"] else None,
        "last_count": s["last_count"],
        "last_error": s["last_error"],
    }
