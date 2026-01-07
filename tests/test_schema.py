from datetime import datetime

from app.schemas import Order, OrderItem


def test_order_schema_valid():
    order = Order(
        order_id="123",
        timestamp=datetime.utcnow(),
        caller_phone="+15551234567",
        items=[
            OrderItem(
                item_id="margherita",
                name="Margherita Pizza",
                quantity=2,
                size="medium",
                modifiers=["extra cheese"],
                addons=[],
            )
        ],
        raw_transcript="Two medium margherita pizzas",
    )
    assert order.items[0].quantity == 2
