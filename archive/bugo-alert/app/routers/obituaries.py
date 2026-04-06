"""부고 목록/검색/상세 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from app.database import get_db
from app.models import Obituary

router = APIRouter()

PER_PAGE_OPTIONS = (10, 20, 50, 100)

# 정렬 가능한 컬럼 → 모델 속성
SORT_COLUMNS = {
    "key_person": Obituary.key_person,
    "organization": Obituary.organization,
    "relationship": Obituary.relationship,
    "deceased_name": Obituary.deceased_name,
    "funeral_hall": Obituary.funeral_hall,
    "funeral_date": Obituary.funeral_date,
    "published_at": Obituary.published_at,
}


def _valid_per_page(v: int) -> int:
    return v if v in PER_PAGE_OPTIONS else 20


def _search_query(db: Session, q: str | None = None, sort: str | None = None, order: str = "desc"):
    query = db.query(Obituary)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Obituary.key_person.ilike(pattern),
                Obituary.organization.ilike(pattern),
                Obituary.deceased_name.ilike(pattern),
                Obituary.funeral_hall.ilike(pattern),
                Obituary.title.ilike(pattern),
                Obituary.position.ilike(pattern),
                Obituary.related_persons.ilike(pattern),
            )
        )
    # 정렬
    col = SORT_COLUMNS.get(sort) if sort else None
    if col is not None:
        query = query.order_by(desc(col) if order == "desc" else asc(col))
    else:
        query = query.order_by(Obituary.published_at.desc())
    return query


@router.get("/")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=10, le=100),
    sort: str | None = Query(None),
    order: str = Query("desc"),
):
    per_page = _valid_per_page(per_page)
    if sort and sort not in SORT_COLUMNS:
        sort = None
    if order not in ("asc", "desc"):
        order = "desc"

    query = _search_query(db, sort=sort, order=order)
    total = query.count()
    obituaries = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    crawl_status = getattr(request.app.state, "crawl_status", {})

    # 정렬 링크용 base URL (page, per_page 유지)
    base = f"/?page={page}&per_page={per_page}"

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "obituaries": obituaries,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "per_page": per_page,
            "per_page_options": PER_PAGE_OPTIONS,
            "crawl_status": crawl_status,
            "sort": sort,
            "order": order,
            "base_url": base,
        },
    )


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(""),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=10, le=100),
):
    per_page = _valid_per_page(per_page)
    q_result = _search_query(db, q)
    total = q_result.count()
    obituaries = q_result.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    template = "partials/obituary_table.html" if request.headers.get("HX-Request") else "search.html"
    return request.app.state.templates.TemplateResponse(
        template,
        {
            "request": request,
            "obituaries": obituaries,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "per_page": per_page,
            "per_page_options": PER_PAGE_OPTIONS,
            "q": q,
        },
    )


@router.get("/obituary/{obituary_id}")
async def detail(
    request: Request,
    obituary_id: int,
    db: Session = Depends(get_db),
):
    obit = db.query(Obituary).filter(Obituary.id == obituary_id).first()
    if obit is None:
        if request.headers.get("HX-Request"):
            return request.app.state.templates.TemplateResponse(
                "partials/obituary_detail.html",
                {"request": request, "obit": None},
            )
        raise HTTPException(status_code=404, detail="부고를 찾을 수 없습니다")
    # 대시보드 스플릿 뷰: HTMX 요청 시 partial만 반환
    if request.headers.get("HX-Request"):
        return request.app.state.templates.TemplateResponse(
            "partials/obituary_detail.html",
            {"request": request, "obit": obit},
        )
    return request.app.state.templates.TemplateResponse(
        "detail.html",
        {"request": request, "obit": obit},
    )
