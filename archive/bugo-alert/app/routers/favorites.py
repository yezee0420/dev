"""즐겨찾기(키워드 알림) CRUD 라우터."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Favorite

router = APIRouter(prefix="/favorites")

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_favorite_input(keyword: str, email: str) -> None:
    keyword = keyword.strip()
    if not keyword or len(keyword) > 200:
        raise HTTPException(status_code=400, detail="키워드는 1~200자로 입력하세요")
    if not _EMAIL_RE.match(email.strip()):
        raise HTTPException(status_code=400, detail="올바른 이메일 형식이 아닙니다")


@router.get("")
async def favorites_page(request: Request, db: Session = Depends(get_db)):
    favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
    return request.app.state.templates.TemplateResponse(
        "favorites.html",
        {"request": request, "favorites": favorites},
    )


@router.post("/add")
async def add_favorite(
    request: Request,
    keyword: str = Form(...),
    keyword_type: str = Form("general"),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    _validate_favorite_input(keyword, email)

    fav = Favorite(keyword=keyword.strip(), keyword_type=keyword_type, email=email.strip())
    db.add(fav)
    db.commit()

    if request.headers.get("HX-Request"):
        db.refresh(fav)
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        return request.app.state.templates.TemplateResponse(
            "partials/favorites_list.html",
            {"request": request, "favorites": favorites},
        )

    return RedirectResponse("/favorites", status_code=303)


@router.post("/toggle/{fav_id}")
async def toggle_favorite(
    request: Request,
    fav_id: int,
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="즐겨찾기를 찾을 수 없습니다")

    fav.is_active = not fav.is_active
    db.commit()

    if request.headers.get("HX-Request"):
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        return request.app.state.templates.TemplateResponse(
            "partials/favorites_list.html",
            {"request": request, "favorites": favorites},
        )

    return RedirectResponse("/favorites", status_code=303)


@router.delete("/delete/{fav_id}")
async def delete_favorite(
    request: Request,
    fav_id: int,
    db: Session = Depends(get_db),
):
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(status_code=404, detail="즐겨찾기를 찾을 수 없습니다")

    db.delete(fav)
    db.commit()

    if request.headers.get("HX-Request"):
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        return request.app.state.templates.TemplateResponse(
            "partials/favorites_list.html",
            {"request": request, "favorites": favorites},
        )

    return RedirectResponse("/favorites", status_code=303)
