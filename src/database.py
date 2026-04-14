"""
Database models and helper functions.
Uses SQLAlchemy with SQLite (easily swappable to PostgreSQL via DATABASE_URL).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import DATABASE_URL

# Ensure data directory exists
Path(DATABASE_URL.replace("sqlite:///", "")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Farmer(Base):
    """One row per registered farmer / subscriber."""

    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=False, unique=True)  # E.164 e.g. +919876543210
    language = Column(String(20), nullable=False, default="hindi")  # see SUPPORTED_LANGUAGES
    state = Column(String(60), nullable=False)
    district = Column(String(60), nullable=False)           # key in district_coords.py
    crop_types = Column(Text, default="[]")                 # JSON list: ["rice","wheat",...]
    has_cattle = Column(Boolean, default=False)
    notification_channel = Column(String(10), default="sms")  # sms | whatsapp | both
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_alerted_at = Column(DateTime, nullable=True)

    # --- helpers -----------------------------------------------------------

    @property
    def crops(self) -> List[str]:
        try:
            return json.loads(self.crop_types or "[]")
        except json.JSONDecodeError:
            return []

    @crops.setter
    def crops(self, value: List[str]) -> None:
        self.crop_types = json.dumps(value, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"<Farmer id={self.id} name={self.name!r} district={self.district!r}>"


class AlertLog(Base):
    """Audit log of every dispatched alert message."""

    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, nullable=False)
    farmer_phone = Column(String(20), nullable=False)
    channel = Column(String(10), nullable=False)            # sms | whatsapp | email
    language = Column(String(20), nullable=False)
    message_preview = Column(String(320), nullable=True)    # first 320 chars
    status = Column(String(20), nullable=False)             # sent | failed
    error_detail = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)


def init_db() -> None:
    """Create all tables if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """Return a new database session (caller must close it)."""
    return SessionLocal()


# ── CRUD helpers ────────────────────────────────────────────────────────────

def add_farmer(
    name: str,
    phone: str,
    language: str,
    state: str,
    district: str,
    crop_types: Optional[List[str]] = None,
    has_cattle: bool = False,
    notification_channel: str = "sms",
) -> Farmer:
    """
    Register a new farmer. Raises ValueError if phone already exists.
    Phone must be in E.164 format, e.g. +919876543210.
    """
    with get_session() as db:
        existing = db.query(Farmer).filter(Farmer.phone == phone).first()
        if existing:
            raise ValueError(f"Phone {phone} is already registered (id={existing.id}).")
        farmer = Farmer(
            name=name,
            phone=phone,
            language=language.lower(),
            state=state,
            district=district.lower(),
            has_cattle=has_cattle,
            notification_channel=notification_channel.lower(),
        )
        farmer.crops = crop_types or []
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
        return farmer


def get_active_farmers(district: Optional[str] = None) -> List[Farmer]:
    """Return all active farmers, optionally filtered by district."""
    with get_session() as db:
        query = db.query(Farmer).filter(Farmer.active == True)
        if district:
            query = query.filter(Farmer.district == district.lower())
        return query.all()


def get_active_districts() -> List[str]:
    """Return distinct districts with at least one active farmer."""
    with get_session() as db:
        rows = (
            db.query(Farmer.district)
            .filter(Farmer.active == True)
            .distinct()
            .all()
        )
        return [r[0] for r in rows]


def log_alert(
    farmer: Farmer,
    channel: str,
    language: str,
    message: str,
    status: str,
    error_detail: Optional[str] = None,
) -> None:
    with get_session() as db:
        entry = AlertLog(
            farmer_id=farmer.id,
            farmer_phone=farmer.phone,
            channel=channel,
            language=language,
            message_preview=message[:320],
            status=status,
            error_detail=error_detail,
        )
        db.add(entry)
        # update last_alerted_at on success
        if status == "sent":
            db.query(Farmer).filter(Farmer.id == farmer.id).update(
                {"last_alerted_at": datetime.utcnow()}
            )
        db.commit()
