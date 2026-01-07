from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text

from app.db import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    customer_name = Column(String, nullable=True)
    caller_phone = Column(String, nullable=False)
    order_type = Column(String, default="takeaway", nullable=False)
    items = Column(JSON, nullable=False)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    status = Column(String, default="received", nullable=False)
    raw_transcript = Column(Text, default="", nullable=False)
    confidence_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CallSession(Base):
    __tablename__ = "call_sessions"

    id = Column(String, primary_key=True, index=True)
    caller_phone = Column(String, nullable=True)
    transcript = Column(Text, default="", nullable=False)
    order_state = Column(JSON, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    llm_failures = Column(Integer, default=0, nullable=False)
    status = Column(String, default="in_progress", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
