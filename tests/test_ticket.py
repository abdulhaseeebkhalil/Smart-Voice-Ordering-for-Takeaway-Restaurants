from datetime import datetime

from app.schemas import Order, OrderItem
from app.utils.formatting import format_ticket


def test_ticket_formatting():
    order = Order(
        order_id="abc-123",
        timestamp=datetime(2024, 1, 1, 12, 0),
        caller_phone="+15551234567",
        items=[
            OrderItem(
                item_id="fries",
                name="Seasoned Fries",
                quantity=1,
                size="large",
                modifiers=[],
                addons=["cheese sauce"],
                special_instructions="extra crispy",
            )
        ],
        raw_transcript="large fries",
    )
    ticket = format_ticket(order)
    assert "Seasoned Fries" in ticket
    assert "extra crispy" in ticket
