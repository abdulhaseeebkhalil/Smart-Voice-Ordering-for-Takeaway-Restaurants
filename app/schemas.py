from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrderItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: str
    name: str
    quantity: int = Field(..., ge=1)
    size: Optional[str] = None
    modifiers: List[str] = Field(default_factory=list)
    addons: List[str] = Field(default_factory=list)
    special_instructions: Optional[str] = None


class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    timestamp: datetime
    customer_name: Optional[str] = None
    caller_phone: str
    order_type: str = "takeaway"
    items: List[OrderItem]
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    status: str = "received"
    raw_transcript: str = ""
    confidence_notes: Optional[str] = None


class OrderDraftItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    item_id: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[int] = None
    size: Optional[str] = None
    modifiers: List[str] = Field(default_factory=list)
    addons: List[str] = Field(default_factory=list)
    special_instructions: Optional[str] = None


class OrderDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customer_name: Optional[str] = None
    order_type: Optional[str] = None
    items: List[OrderDraftItem] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    special_instructions: Optional[str] = None
    confidence_notes: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    order_id: str
    timestamp: datetime
    customer_name: Optional[str] = None
    caller_phone: str
    order_type: str
    items: List[OrderItem]
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    status: str
    raw_transcript: str
    confidence_notes: Optional[str] = None
