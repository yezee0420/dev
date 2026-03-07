"""부고 목록/검색/상세 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Obituary

router = APIRouter()


def _search_query(db: Session, q: str | None = None):
    query = db.query(Obituary).order_by(Obituary.published_at.desc())
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
    return query


@router.get("/")
async def index(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
):
    per_page = 20
    query = _search_query(db)
    total = query.count()
    obituaries = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, (total + per_page - 1) // per_page)

    crawl_status = getattr(request.app.state, "crawl_status", {})

    return request.app.state.templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "obituaries": obituaries,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "crawl_status": crawl_status,
        },
    )


@router.get("/search")
async def search(
    request: Request,
    q: str = Query(""),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
):
    per_page = 20
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
        raise HTTPException(status_code=404, detail="부고를 찾을 수 없습니다")
    return request.app.state.templates.TemplateResponse(
        "detail.html",
        {"request": request, "obit": obit},
    )
