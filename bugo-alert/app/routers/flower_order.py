"""화환 주문 연동 stub — 협력업체 API 연동 전까지 안내 페이지를 제공한다."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Obituary

router = APIRouter(prefix="/flower")

PARTNER_VENDORS = [
    {
        "name": "근조화환 전문 1번가",
        "phone": "1588-0000",
        "url": "https://example.com/flower1",
        "note": "전국 당일배송, 3만원~",
    },
    {
        "name": "장례 화환 직배송",
        "phone": "1600-0000",
        "url": "https://example.com/flower2",
        "note": "근조화환·근조과일바구니, 5만원~",
    },
]


@router.get("/order/{obituary_id}")
async def flower_order_page(
    request: Request,
    obituary_id: int,
    db: Session = Depends(get_db),
):
    obit = db.query(Obituary).filter(Obituary.id == obituary_id).first()
    if obit is None:
        raise HTTPException(status_code=404, detail="부고를 찾을 수 없습니다")
    return request.app.state.templates.TemplateResponse(
        "flower_order.html",
        {
            "request": request,
            "obit": obit,
            "vendors": PARTNER_VENDORS,
        },
    )
