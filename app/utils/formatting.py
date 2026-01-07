from __future__ import annotations

from datetime import datetime
from typing import Iterable

from app.config import settings
from app.schemas import Order


def _line_wrap(text: str, width: int = 32) -> Iterable[str]:
    words = text.split()
    line = []
    count = 0
    for word in words:
        if count + len(word) + (1 if line else 0) > width:
            yield " ".join(line)
            line = [word]
            count = len(word)
        else:
            line.append(word)
            count += len(word) + (1 if line else 0)
    if line:
        yield " ".join(line)


def format_order_summary(order: Order) -> str:
    parts = []
    for item in order.items:
        base = f"{item.quantity}x {item.name}"
        if item.size:
            base += f" ({item.size})"
        parts.append(base)
        for modifier in item.modifiers + item.addons:
            parts.append(f"- {modifier}")
        if item.special_instructions:
            parts.append(f"- {item.special_instructions}")
    return "; ".join(parts)


def format_ticket(order: Order) -> str:
    order_time = order.timestamp.strftime("%Y-%m-%d %H:%M")
    short_id = order.order_id.split("-")[0]
    lines = [
        settings.restaurant_name,
        "-" * 32,
        f"Time: {order_time}",
        f"Order: {short_id}",
        f"Phone: {order.caller_phone}",
        "-" * 32,
    ]

    for item in order.items:
        header = f"{item.quantity}x {item.name}"
        if item.size:
            header += f" ({item.size})"
        lines.append(header)
        for modifier in item.modifiers + item.addons:
            for line in _line_wrap(f"* {modifier}"):
                lines.append(line)
        if item.special_instructions:
            for line in _line_wrap(f"! {item.special_instructions}"):
                lines.append(line)

    if order.subtotal is not None:
        lines.append("-" * 32)
        lines.append(f"Subtotal: ${order.subtotal:.2f}")
        if order.tax is not None:
            lines.append(f"Tax: ${order.tax:.2f}")
        if order.total is not None:
            lines.append(f"Total: ${order.total:.2f}")

    lines.append("-" * 32)
    lines.append("Thank you!")
    return "\n".join(lines)


def now_utc() -> datetime:
    return datetime.utcnow()
