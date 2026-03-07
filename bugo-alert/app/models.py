from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index,
)
from sqlalchemy.orm import relationship
from app.database import Base


class Obituary(Base):
    __tablename__ = "obituaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(512), unique=True, nullable=False)
    title = Column(String(512), nullable=False)

    deceased_name = Column(String(100))
    age = Column(String(50))
    organization = Column(String(200))
    position = Column(String(200))
    relationship = Column(String(100))
    mourner_name = Column(String(100))
    funeral_hall = Column(String(200))
    room_number = Column(String(50))
    funeral_date = Column(String(100))
    funeral_time = Column(String(50))
    contact = Column(String(100))
    remarks = Column(Text)

    raw_text = Column(Text)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_obituaries_deceased", "deceased_name"),
        Index("ix_obituaries_org", "organization"),
        Index("ix_obituaries_published", "published_at"),
    )


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    keyword = Column(String(200), nullable=False)
    keyword_type = Column(String(20), default="general")  # person / org / general
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
    status = Column(String(20), default="sent")  # sent / failed

    obituary = relationship("Obituary")
    favorite = relationship("Favorite")
