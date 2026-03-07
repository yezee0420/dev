"""즐겨찾기(키워드 알림) CRUD 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Favorite

router = APIRouter(prefix="/favorites")


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
    fav = Favorite(keyword=keyword, keyword_type=keyword_type, email=email)
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
    if fav:
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
    if fav:
        db.delete(fav)
        db.commit()

    if request.headers.get("HX-Request"):
        favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
        return request.app.state.templates.TemplateResponse(
            "partials/favorites_list.html",
            {"request": request, "favorites": favorites},
        )

    return RedirectResponse("/favorites", status_code=303)
