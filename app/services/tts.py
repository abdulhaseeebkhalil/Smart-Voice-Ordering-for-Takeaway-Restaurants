from __future__ import annotations

import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def synthesize_speech(text: str) -> Optional[bytes]:
    if not settings.use_openai_tts:
        return None
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing, skipping TTS")
        return None
    try:
        from openai import OpenAI
    except ImportError as exc:
        logger.error("openai package missing: %s", exc)
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.audio.speech.create(
            model=settings.openai_tts_model,
            voice="alloy",
            input=text,
        )
    except Exception as exc:
        logger.error("OpenAI TTS failed: %s", exc)
        return None

    return response.content
