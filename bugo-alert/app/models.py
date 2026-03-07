from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Obituary(Base):
    __tablename__ = "obituaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(512), nullable=False)
    title = Column(String(512), nullable=False)

    # 핵심인물 (조문 대상) — 제목의 주인공
    key_person = Column(String(100))
    organization = Column(String(200))
    position = Column(String(200))

    # 고인 정보
    deceased_name = Column(String(100))
    deceased_age = Column(String(50))

    # 관계 (핵심인물 기준: 모친상, 부친상, 장인상 등)
    relationship = Column(String(100))

    # 기타 관계자 목록 (JSON 텍스트)
    related_persons = Column(Text)

    # 장례 정보
    funeral_hall = Column(String(200))
    room_number = Column(String(50))
    funeral_date = Column(String(100))
    funeral_time = Column(String(50))
    contact = Column(String(100))
    remarks = Column(Text)

    raw_text = Column(Text)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 중복 제거용 해시 (key_person + relationship + deceased_name)
    dedup_key = Column(String(200), unique=True, nullable=True)

    __table_args__ = (
        Index("ix_obituaries_key_person", "key_person"),
        Index("ix_obituaries_org", "organization"),
        Index("ix_obituaries_published", "published_at"),
        Index("ix_obituaries_dedup", "dedup_key"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    keyword_type = Column(String(20), default="general")
    email = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_favorites_keyword", "keyword"),
    )


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    obituary_id = Column(Integer, ForeignKey("obituaries.id"), nullable=False)
    favorite_id = Column(Integer, ForeignKey("favorites.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="sent")

    obituary = relationship("Obituary")
    favorite = relationship("Favorite")
