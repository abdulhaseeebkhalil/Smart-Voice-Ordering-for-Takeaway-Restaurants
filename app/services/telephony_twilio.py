from __future__ import annotations

from twilio.twiml.voice_response import Dial, Gather, VoiceResponse

from app.config import settings


def gather_speech(action_url: str, prompt: str | None = None) -> str:
    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=action_url,
        method="POST",
        speech_timeout="auto",
        language="en-US",
        action_on_empty_result=True,
    )
    if prompt:
        gather.say(prompt, voice=settings.twilio_voice)
    response.append(gather)
    if not prompt:
        response.say("Sorry, I did not hear you.", voice=settings.twilio_voice)
    return str(response)


def say_and_hangup(message: str) -> str:
    response = VoiceResponse()
    response.say(message, voice=settings.twilio_voice)
    response.hangup()
    return str(response)


def dial_fallback(number: str) -> str:
    response = VoiceResponse()
    if number:
        response.say(
            "Please hold while I transfer you to a team member.",
            voice=settings.twilio_voice,
        )
        response.append(Dial(number))
    else:
        response.say("Sorry, we could not take your order.", voice=settings.twilio_voice)
        response.hangup()
    return str(response)
