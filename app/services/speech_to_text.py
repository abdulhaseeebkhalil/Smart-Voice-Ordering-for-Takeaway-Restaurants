from __future__ import annotations

import io
import logging
from typing import Optional

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def transcribe_audio(audio_url: str) -> Optional[str]:
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY missing, skipping transcription")
        return None

    try:
        from openai import OpenAI
    except ImportError as exc:
        logger.error("openai package missing: %s", exc)
        return None

    try:
        response = requests.get(audio_url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to download audio: %s", exc)
        return None

    audio_bytes = io.BytesIO(response.content)
    audio_bytes.name = "audio.wav"

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_bytes,
        )
    except Exception as exc:
        logger.error("OpenAI transcription failed: %s", exc)
        return None

    return getattr(result, "text", None)
