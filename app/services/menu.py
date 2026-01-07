from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings


class MenuError(ValueError):
    pass


def load_menu(path: str) -> Dict[str, Any]:
    menu_path = Path(path)
    if not menu_path.exists():
        raise MenuError(f"Menu file not found: {menu_path}")
    data = json.loads(menu_path.read_text())
    validate_menu(data)
    return data


def validate_menu(menu: Dict[str, Any]) -> None:
    if "categories" not in menu or not isinstance(menu["categories"], list):
        raise MenuError("Menu must include categories list")
    for category in menu["categories"]:
        if "name" not in category or "items" not in category:
            raise MenuError("Each category requires name and items")
        if not isinstance(category["items"], list):
            raise MenuError("Category items must be a list")
        for item in category["items"]:
            if "id" not in item or "name" not in item:
                raise MenuError("Each item requires id and name")


def all_items(menu: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for category in menu.get("categories", []):
        for item in category.get("items", []):
            items.append(item)
    return items


def menu_lookup(menu: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    for item in all_items(menu):
        key = normalize_name(item.get("name", ""))
        if key:
            lookup[key] = item
    return lookup


def normalize_name(text: str) -> str:
    return "".join(ch.lower() for ch in text if ch.isalnum() or ch.isspace()).strip()


def menu_prompt(menu: Dict[str, Any]) -> str:
    lines = []
    for category in menu.get("categories", []):
        lines.append(f"Category: {category.get('name')}")
        for item in category.get("items", []):
            line = f"- {item.get('name')}"
            variants = item.get("variants") or []
            addons = item.get("addons") or []
            if variants:
                line += f" | sizes: {', '.join(variants)}"
            if addons:
                line += f" | addons: {', '.join(addons)}"
            lines.append(line)
    return "\n".join(lines)


def price_items(items: List[Dict[str, Any]], menu: Dict[str, Any]) -> Dict[str, float | None]:
    lookup = menu_lookup(menu)
    subtotal = 0.0
    priced_any = False
    for item in items:
        name = item.get("name", "")
        quantity = item.get("quantity") or 0
        menu_item = lookup.get(normalize_name(name))
        if not menu_item or menu_item.get("price") is None:
            continue
        priced_any = True
        try:
            qty = int(quantity)
        except (TypeError, ValueError):
            qty = 0
        subtotal += float(menu_item.get("price", 0.0)) * qty

    if not priced_any:
        return {"subtotal": None, "tax": None, "total": None}

    tax = round(subtotal * settings.tax_rate, 2)
    return {"subtotal": round(subtotal, 2), "tax": tax, "total": round(subtotal + tax, 2)}
