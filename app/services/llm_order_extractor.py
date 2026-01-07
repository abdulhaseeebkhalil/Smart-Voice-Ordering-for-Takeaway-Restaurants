from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.schemas import OrderDraft, OrderDraftItem
from app.services.menu import menu_lookup, menu_prompt, normalize_name

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    order: Dict[str, Any]
    missing_fields: List[str]
    question: Optional[str]
    raw_response: str
    error: Optional[str] = None


def extract_or_question(
    transcript: str,
    menu: Dict[str, Any],
    current_order_state: Optional[Dict[str, Any]] = None,
) -> ExtractionResult:
    current_order_state = current_order_state or {}

    try:
        response_text = _call_llm(transcript, menu, current_order_state)
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return ExtractionResult(
            order=current_order_state,
            missing_fields=["items"],
            question="Sorry, I had trouble understanding. Could you repeat your order?",
            raw_response="",
            error=str(exc),
        )

    parsed = parse_llm_response(response_text)
    order_data = parsed.get("order") or {}
    missing_fields = parsed.get("missing_fields") or []
    question = parsed.get("question")

    merged_order = merge_order_state(current_order_state, order_data)
    validated_order, computed_missing, auto_question = validate_order_draft(merged_order, menu)

    if computed_missing:
        missing_fields = computed_missing
        question = question or auto_question

    return ExtractionResult(
        order=validated_order,
        missing_fields=missing_fields,
        question=question,
        raw_response=response_text,
        error=None,
    )


def _call_llm(transcript: str, menu: Dict[str, Any], current_order_state: Dict[str, Any]) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package missing") from exc

    system_prompt = (
        "You are an AI order-taking assistant. "
        "Only use items from the provided menu. "
        "If the caller asks for something not on the menu, "
        "politely offer the closest alternatives from the menu. "
        "Respond in strict JSON with keys: order, missing_fields, question. "
        "The order object should include customer_name (optional), order_type, "
        "and items (array). Each item has name, item_id (if known), quantity, size, "
        "modifiers, addons, special_instructions. "
        "If information is missing, list it in missing_fields and ask one concise follow-up question."
    )

    user_prompt = (
        f"Menu:\n{menu_prompt(menu)}\n\n"
        f"Existing order state (JSON): {json.dumps(current_order_state)}\n"
        f"Caller said: {transcript}\n"
        "Return JSON only."
    )

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content or ""


def parse_llm_response(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return {}


def merge_order_state(existing: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(existing)
    for key, value in incoming.items():
        if value in (None, "", [], {}):
            continue
        if key == "items" and isinstance(value, list):
            merged["items"] = value
        else:
            merged[key] = value
    return merged


def validate_order_draft(
    order_data: Dict[str, Any],
    menu: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[str], Optional[str]]:
    order = OrderDraft(**order_data)
    missing: List[str] = []
    question: Optional[str] = None

    if not order.items:
        missing.append("items")
        question = "What would you like to order?"
        return order.model_dump(), missing, question

    lookup = menu_lookup(menu)
    for index, item in enumerate(order.items):
        missing.extend(_validate_item(item, index, lookup, menu, order))

    if missing and not question:
        question = build_question(missing, order, menu)

    return order.model_dump(), missing, question


def _validate_item(
    item: OrderDraftItem,
    index: int,
    lookup: Dict[str, Dict[str, Any]],
    menu: Dict[str, Any],
    order: OrderDraft,
) -> List[str]:
    missing: List[str] = []
    if not item.name:
        missing.append(f"items[{index}].name")
        return missing

    normalized = normalize_name(item.name)
    menu_item = lookup.get(normalized)
    if not menu_item:
        missing.append(f"items[{index}].menu_item")
        return missing

    if not item.item_id:
        item.item_id = menu_item.get("id")

    if not item.quantity:
        missing.append(f"items[{index}].quantity")

    variants = menu_item.get("variants") or []
    if variants and not item.size:
        missing.append(f"items[{index}].size")

    if variants and item.size and item.size not in variants:
        missing.append(f"items[{index}].size")

    return missing


def build_question(missing_fields: List[str], order: OrderDraft, menu: Dict[str, Any]) -> str:
    if "items" in missing_fields:
        return "What would you like to order?"

    for field in missing_fields:
        if field.endswith(".menu_item"):
            index = int(field.split("[")[1].split("]")[0])
            item_name = order.items[index].name if index < len(order.items) else "that item"
            alternatives = closest_menu_items(item_name or "", menu)
            if alternatives:
                return (
                    f"Sorry, we do not have {item_name}. "
                    f"We do have {', '.join(alternatives)}. Which would you like?"
                )
            return f"Sorry, we do not have {item_name}. What would you like instead?"

        if field.endswith(".quantity"):
            return "How many would you like?"

        if field.endswith(".size"):
            index = int(field.split("[")[1].split("]")[0])
            item_name = order.items[index].name if index < len(order.items) else "that item"
            return f"What size would you like for the {item_name}?"

    return "Could you clarify your order?"


def closest_menu_items(name: str, menu: Dict[str, Any]) -> List[str]:
    names = [
        item.get("name", "")
        for category in menu.get("categories", [])
        for item in category.get("items", [])
    ]
    normalized_map = {normalize_name(n): n for n in names}
    matches = get_close_matches(normalize_name(name), list(normalized_map.keys()), n=2, cutoff=0.4)
    return [normalized_map[m] for m in matches]
