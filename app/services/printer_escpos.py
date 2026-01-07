from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.schemas import Order
from app.utils.formatting import format_ticket

logger = logging.getLogger(__name__)


def _ensure_print_dir() -> Path:
    path = Path("./data/prints")
    path.mkdir(parents=True, exist_ok=True)
    return path


def print_order(order: Order) -> None:
    ticket = format_ticket(order)
    mode = settings.printer_mode.lower()

    if mode == "dryrun":
        path = _ensure_print_dir() / f"order_{order.order_id}.txt"
        path.write_text(ticket)
        logger.info("Dry-run print saved to %s", path)
        return

    try:
        from escpos.printer import Network, Usb
    except ImportError as exc:
        logger.error("python-escpos is not installed: %s", exc)
        return

    if mode == "usb":
        if settings.printer_usb_vendor_id is None or settings.printer_usb_product_id is None:
            logger.error("USB printer IDs are not configured")
            return
        printer = Usb(settings.printer_usb_vendor_id, settings.printer_usb_product_id)
    elif mode == "network":
        if not settings.printer_network_host:
            logger.error("Network printer host is not configured")
            return
        printer = Network(settings.printer_network_host, port=settings.printer_network_port)
    else:
        logger.error("Unsupported printer mode: %s", settings.printer_mode)
        return

    printer.text(ticket + "\n")
    printer.cut()
    logger.info("Order %s printed", order.order_id)
