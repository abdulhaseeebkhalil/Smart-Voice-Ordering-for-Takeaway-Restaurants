from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import verify_dashboard_password
from app.db import get_db
from app.models import Order
from app.schemas import OrderResponse
from app.services.printer_escpos import print_order

router = APIRouter()


def _order_to_schema(order: Order) -> OrderResponse:
    return OrderResponse(
        order_id=order.id,
        timestamp=order.timestamp,
        customer_name=order.customer_name,
        caller_phone=order.caller_phone,
        order_type=order.order_type,
        items=order.items,
        subtotal=order.subtotal,
        tax=order.tax,
        total=order.total,
        status=order.status,
        raw_transcript=order.raw_transcript,
        confidence_notes=order.confidence_notes,
    )


@router.get("/dashboard")
def dashboard() -> FileResponse:
    path = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"
    return FileResponse(path)


@router.get("/api/orders", response_model=List[OrderResponse])
def list_orders(
    db: Session = Depends(get_db),
    _: None = Depends(verify_dashboard_password),
) -> List[OrderResponse]:
    orders = db.query(Order).order_by(Order.timestamp.desc()).all()
    return [_order_to_schema(order) for order in orders]


@router.get("/api/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_dashboard_password),
) -> OrderResponse:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_to_schema(order)


@router.post("/api/orders/{order_id}/reprint")
def reprint_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(verify_dashboard_password),
) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    print_order(_order_to_schema(order))
    order.status = "printed"
    db.add(order)
    db.commit()
    return {"status": "printed"}
