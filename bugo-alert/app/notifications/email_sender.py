"""SMTP 이메일 알림 발송 모듈."""

from __future__ import annotations

import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.config import get_settings
from app.models import Obituary, Favorite
from app.notifications.base import BaseNotifier

logger = logging.getLogger(__name__)


def _build_html(obit: Obituary) -> str:
    rows = [
        ("핵심인물", obit.key_person or "-"),
        ("소속", obit.organization or "-"),
        ("직급/직위", obit.position or "-"),
        ("관계", obit.relationship or "-"),
        ("고인", obit.deceased_name or "-"),
        ("나이", obit.deceased_age or "-"),
        ("장례식장", obit.funeral_hall or "-"),
        ("호실", obit.room_number or "-"),
        ("발인일", obit.funeral_date or "-"),
        ("발인시간", obit.funeral_time or "-"),
        ("연락처", obit.contact or "-"),
        ("관계자", obit.related_persons or "-"),
    ]
    table_rows = "".join(
        f'<tr><td style="padding:6px 12px;font-weight:bold;background:#f3f4f6">{k}</td>'
        f'<td style="padding:6px 12px">{v}</td></tr>'
        for k, v in rows
    )
    person_label = obit.key_person or "새 부고"
    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#1f2937">부고 알림 — {person_label}</h2>
      <p style="color:#6b7280">즐겨찾기 키워드 매칭으로 발송된 알림입니다.</p>
      <table style="border-collapse:collapse;width:100%;border:1px solid #e5e7eb">
        {table_rows}
      </table>
      <p style="margin-top:16px">
        <a href="{obit.source_url}" style="color:#2563eb">기사 원문 보기</a>
      </p>
    </div>
    """


class EmailNotifier(BaseNotifier):
    async def send(self, obituary: Obituary, favorite: Favorite) -> bool:
        settings = get_settings()
        if not settings.smtp_user or not settings.smtp_password:
            logger.warning("SMTP 설정 누락 — 이메일 발송 건너뜀")
            return False

        person = obituary.key_person or "새 부고"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[부고알림] {person} ({obituary.organization or ''}) {obituary.relationship or ''} — 키워드: {favorite.keyword}"
        msg["From"] = settings.smtp_from or settings.smtp_user
        msg["To"] = favorite.email

        html = _build_html(obituary)
        msg.attach(MIMEText(html, "html", "utf-8"))

        try:
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                start_tls=True,
            )
            logger.info("이메일 발송 성공 → %s (키워드=%s)", favorite.email, favorite.keyword)
            return True
        except Exception as exc:
            logger.error("이메일 발송 실패: %s", exc)
            return False
