"""알림 채널의 공통 인터페이스. 향후 SMS/카카오/앱푸시 추가 시 이 클래스를 상속한다."""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.models import Obituary, Favorite


class BaseNotifier(ABC):
    @abstractmethod
    async def send(self, obituary: Obituary, favorite: Favorite) -> bool:
        """알림을 발송하고 성공 여부를 반환한다."""
        ...
