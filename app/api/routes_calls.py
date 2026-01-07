from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import CallSession, Order
from app.schemas import Order as OrderSchema
from app.services.llm_order_extractor import ExtractionResult, extract_or_question
from app.services.menu import price_items
from app.services.printer_escpos import print_order
from app.services.telephony_twilio import dial_fallback, gather_speech, say_and_hangup
from app.utils.formatting import format_order_summary, now_utc

logger = logging.getLogger(__name__)

router = APIRouter()


def _action_url(path: str) -> str:
    return f"{settings.base_url.rstrip('/')}{path}"


def _get_or_create_session(db: Session, session_id: str, caller_phone: Optional[str]) -> CallSession:
    session = db.query(CallSession).filter(CallSession.id == session_id).first()
    if session:
        if caller_phone and not session.caller_phone:
            session.caller_phone = caller_phone
            db.add(session)
            db.commit()
        return session
    session = CallSession(id=session_id, caller_phone=caller_phone or "")
    db.add(session)
    db.commit()
    return session


def _append_transcript(session: CallSession, text: str) -> None:
    if not text:
        return
    combined = f"{session.transcript} {text}".strip()
    session.transcript = combined


def _build_order(
    order_state: dict,
    caller_phone: str,
    transcript: str,
    status: str,
    menu: dict,
) -> OrderSchema:
    timestamp = now_utc()
    order_id = str(uuid.uuid4())
    items = order_state.get("items", [])
    totals = price_items(items, menu=menu)
    return OrderSchema(
        order_id=order_id,
        timestamp=timestamp,
        customer_name=order_state.get("customer_name"),
        caller_phone=caller_phone,
        order_type=order_state.get("order_type") or "takeaway",
        items=items,
        subtotal=totals.get("subtotal"),
        tax=totals.get("tax"),
        total=totals.get("total"),
        status=status,
        raw_transcript=transcript,
        confidence_notes=order_state.get("confidence_notes"),
    )


def _save_order(db: Session, order: OrderSchema) -> Order:
    model = Order(
        id=order.order_id,
        timestamp=order.timestamp,
        customer_name=order.customer_name,
        caller_phone=order.caller_phone,
        order_type=order.order_type,
        items=[item.model_dump() for item in order.items],
        subtotal=order.subtotal,
        tax=order.tax,
        total=order.total,
        status=order.status,
        raw_transcript=order.raw_transcript,
        confidence_notes=order.confidence_notes,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def _should_fallback(result: ExtractionResult, session: CallSession) -> bool:
    if result.error:
        session.llm_failures += 1
    return session.llm_failures >= settings.llm_max_retries


@router.post("/twilio/voice")
def twilio_voice(
    CallSid: str = Form(...),
    From: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
) -> Response:
    _get_or_create_session(db, CallSid, From)
    greeting = (
        f"Hello! Thanks for calling {settings.restaurant_name}. "
        "I can take your order."
    )
    twiml = gather_speech(_action_url("/twilio/process"), greeting)
    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/process")
def twilio_process(
    CallSid: str = Form(...),
    From: Optional[str] = Form(default=None),
    SpeechResult: Optional[str] = Form(default=None),
    Confidence: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    request: Request,
) -> Response:
    session = _get_or_create_session(db, CallSid, From)
    session.attempts += 1

    if not SpeechResult:
        db.add(session)
        db.commit()
        twiml = gather_speech(_action_url("/twilio/process"), "Sorry, I did not catch that. What would you like?")
        return Response(content=twiml, media_type="application/xml")

    _append_transcript(session, SpeechResult)

    menu = request.app.state.menu
    if menu is None:
        logger.error("Menu not loaded")
        twiml = say_and_hangup("Sorry, we cannot take orders right now.")
        return Response(content=twiml, media_type="application/xml")

    order_state = session.order_state or {}
    if Confidence:
        order_state["confidence_notes"] = f"Confidence: {Confidence}"

    result = extract_or_question(SpeechResult, menu, order_state)

    if _should_fallback(result, session):
        session.status = "fallback"
        db.add(session)
        db.commit()
        twiml = dial_fallback(settings.fallback_forward_number)
        return Response(content=twiml, media_type="application/xml")

    existing_notes = order_state.get("confidence_notes")
    if existing_notes and "confidence_notes" not in result.order:
        result.order["confidence_notes"] = existing_notes

    if result.raw_response:
        note = result.order.get("confidence_notes") or ""
        combined = f"{note}\nLLM: {result.raw_response}".strip()
        result.order["confidence_notes"] = combined

    session.order_state = result.order
    db.add(session)
    db.commit()

    if result.missing_fields:
        question = result.question or "Could you clarify your order?"
        twiml = gather_speech(_action_url("/twilio/process"), question)
        return Response(content=twiml, media_type="application/xml")

    draft_order = _build_order(
        session.order_state,
        session.caller_phone or From or "",
        session.transcript,
        "received",
        menu,
    )
    summary = format_order_summary(draft_order)
    confirmation = f"You ordered {summary}. Is that correct?"
    twiml = gather_speech(_action_url("/twilio/confirm"), confirmation)
    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/confirm")
def twilio_confirm(
    CallSid: str = Form(...),
    From: Optional[str] = Form(default=None),
    SpeechResult: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
    request: Request,
) -> Response:
    session = _get_or_create_session(db, CallSid, From)

    response = (SpeechResult or "").lower()
    if not response:
        twiml = gather_speech(_action_url("/twilio/confirm"), "Please say yes or no.")
        return Response(content=twiml, media_type="application/xml")
    if any(word in response for word in ["yes", "correct", "right", "yeah", "yep"]):
        if not session.order_state:
            twiml = say_and_hangup("Sorry, I could not find your order. Please call again.")
            return Response(content=twiml, media_type="application/xml")

        menu = request.app.state.menu
        draft = _build_order(
            session.order_state,
            session.caller_phone or From or "",
            session.transcript,
            "confirmed",
            menu,
        )
        saved = _save_order(db, draft)

        try:
            print_order(draft)
            saved.status = "printed"
            db.add(saved)
            db.commit()
        except Exception as exc:
            logger.error("Printing failed: %s", exc)

        session.status = "completed"
        db.add(session)
        db.commit()

        twiml = say_and_hangup("Great! Your order is placed. Thank you!")
        return Response(content=twiml, media_type="application/xml")

    twiml = gather_speech(_action_url("/twilio/process"), "Okay, please tell me the order again.")
    return Response(content=twiml, media_type="application/xml")
