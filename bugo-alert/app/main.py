"""BugoAlert — FastAPI 앱 엔트리포인트."""

from __future__ import annotations

import asyncio
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


def _open_browser():
    """서버 준비 후 브라우저를 연다. 이미 열려 있으면 새 탭을 만들지 않고 기존 창을 포커스한다."""
    import time
    time.sleep(1.5)
    port = get_settings().port
    webbrowser.open(f"http://localhost:{port}", new=0)


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
        "started_at": None,
        "duration_seconds": None,
        "api_calls_this_run": 0,
    }

    settings = get_settings()
    scheduler.add_job(
        run_crawl_job,
        "interval",
        minutes=settings.crawl_interval_minutes,
        id="crawl_obituaries",
        replace_existing=True,
        args=[app],
    )
    scheduler.start()
    logger.info("스케줄러 시작 (주기=%d분)", settings.crawl_interval_minutes)

    # 서버 시작 시 즉시 첫 크롤링 실행
    if settings.naver_client_id and settings.naver_client_id != "your_naver_client_id":
        scheduler.add_job(run_crawl_job, id="initial_crawl", replace_existing=True, args=[app])
        logger.info("첫 크롤링 즉시 실행 예약됨")
    else:
        logger.warning("⚠ NAVER API 키 미설정 — .env 파일에 NAVER_CLIENT_ID/SECRET을 입력하세요")

    threading.Thread(target=_open_browser, daemon=True).start()

    yield

    scheduler.shutdown(wait=False)
    logger.info("스케줄러 종료")


app = FastAPI(title="BugoAlert", lifespan=lifespan)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.state.templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _format_funeral_date(val: str | None) -> str:
    """대시보드용: '9일' → '3월 9일', 이미 '3월 9일'이면 그대로."""
    if not val or not val.strip():
        return val or ""
    val = val.strip()
    if "월" in val:
        return val
    import re
    if re.match(r"^\d{1,2}일$", val):
        return f"{datetime.now().month}월 {val}"
    return val


def _format_funeral_date_full(val: str | None) -> str:
    """세부 페이지용: 항상 '2026년 3월 9일' 형식으로 연·월·일 전체 표시."""
    if not val or not val.strip():
        return val or ""
    val = val.strip()
    now = datetime.now()
    import re
    # 이미 "2026년 3월 1일" 형식이면 그대로
    if re.search(r"\d{4}\s*년", val):
        return val
    # "3월 9일" → "2026년 3월 9일"
    m = re.match(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", val)
    if m:
        return f"{now.year}년 {m.group(1)}월 {m.group(2)}일"
    # "9일" → "2026년 3월 9일"
    if re.match(r"^\d{1,2}\s*일$", val):
        return f"{now.year}년 {now.month}월 {val}"
    return val


app.state.templates.env.filters["format_funeral_date"] = _format_funeral_date
app.state.templates.env.filters["format_funeral_date_full"] = _format_funeral_date_full

app.include_router(obituaries.router)
app.include_router(favorites.router)
app.include_router(flower_order.router)


_crawl_lock = asyncio.Lock()


@app.get("/api/crawl-now")
async def trigger_crawl():
    """수동 크롤링 트리거 (동시 실행 방지)."""
    from app.scheduler.jobs import crawl_and_notify

    status = app.state.crawl_status

    if _crawl_lock.locked():
        return {"status": "busy", "message": "크롤링이 이미 진행 중입니다"}

    async with _crawl_lock:
        status["is_running"] = True
        status["started_at"] = datetime.now()
        status["duration_seconds"] = None
        status["api_calls_this_run"] = 0
        try:
            result = await crawl_and_notify()
            count = result.get("new_count", 0)
            status["last_run"] = datetime.now()
            status["last_count"] = count
            status["last_error"] = None
            if isinstance(result, dict):
                status["duration_seconds"] = result.get("duration_seconds")
                status["api_calls_this_run"] = result.get("api_calls", 0)
            return {"status": "ok", "message": f"크롤링 완료 — 신규 {count}건"}
        except Exception as e:
            status["last_error"] = str(e)
            return {"status": "error", "message": str(e)}
        finally:
            status["is_running"] = False


@app.get("/api/cleanup-now")
async def trigger_cleanup():
    """데이터 정리 수동 실행 — 중복 제거, 병합, 품질 보정."""
    from app.deduplication import run_cleanup
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        result = run_cleanup(db=db)
        return {
            "status": "ok",
            "message": f"병합 {result['merged']}건, 삭제 {result['deleted']}건, 보정 {result['corrected']}건",
            "merged": result["merged"],
            "deleted": result["deleted"],
            "corrected": result["corrected"],
            "total_changes": result["total_changes"],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@app.get("/api/crawl-status")
async def crawl_status():
    """현재 크롤링 상태를 반환한다."""
    s = app.state.crawl_status
    return {
        "is_running": s["is_running"],
        "last_run": s["last_run"].strftime("%Y-%m-%d %H:%M:%S") if s["last_run"] else None,
        "last_count": s["last_count"],
        "last_error": s["last_error"],
        "started_at": s["started_at"].strftime("%Y-%m-%d %H:%M:%S") if s.get("started_at") else None,
        "duration_seconds": s.get("duration_seconds"),
        "api_calls_this_run": s.get("api_calls_this_run", 0),
    }


@app.get("/health")
async def health_check():
    """헬스체크 — DB 연결 확인."""
    from sqlalchemy import text
    from app.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
