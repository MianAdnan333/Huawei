"""Voice turn with a free Google AI Studio key: Gemini hears the audio, replies, and speaks."""
import json
import logging
import re
import time
from dataclasses import dataclass

import httpx
import numpy as np
from google import genai
from google.genai import errors, types

from voice_core import InvalidApiKey, VoiceTurn, VoiceTurnFailed

log = logging.getLogger("voice_agent")

ANSWER_TIMEOUT_SECONDS = 60
SPEECH_TIMEOUT_SECONDS = 45
# Retired (404), out of per-model free quota (429) or overloaded (500/503): another model may still work
TRY_NEXT_MODEL_CODES = (404, 429, 500, 503)
GEMINI_VOICES = ["Kore", "Puck", "Charon", "Aoede", "Fenrir", "Leda", "Orus", "Zephyr"]
NON_CHAT_MARKERS = ("tts", "image", "live", "audio", "embedding", "robotics", "computer-use")
UNSTABLE_MARKERS = ("preview", "exp", "lite")
VERSION_PATTERN = re.compile(r"gemini-(\d+)(?:\.(\d+))?")

REPLY_SCHEMA = {
    "type": "object",
    "properties": {
        "transcription": {"type": "string", "description": "Exactly what the user said in the audio."},
        "reply": {"type": "string", "description": "Your spoken answer to the user."},
    },
    "required": ["transcription", "reply"],
}
AUDIO_PROMPT = (
    "Listen to the user's audio. Return what they said as `transcription` and your answer as `reply`. "
    "If the audio has no clear speech, return an empty transcription."
)


@dataclass(frozen=True)
class GeminiVoiceModels:
    chat: list[str]
    tts: list[str]


def list_models(api_key: str) -> GeminiVoiceModels:
    client = make_client(api_key, 20)
    try:
        models = [(m.name.removeprefix("models/"), m.supported_actions or []) for m in client.models.list()]
    except errors.APIError as error:
        raise InvalidApiKey(f"Google rejected this API key: {error.message}") from error
    return sort_models(models)


def sort_models(models: list[tuple[str, list[str]]]) -> GeminiVoiceModels:
    """Split into chat and text-to-speech models, newest stable Flash first."""
    generators = [name for name, actions in models if "generateContent" in actions and name.startswith("gemini")]
    chat = [name for name in generators if not any(marker in name for marker in NON_CHAT_MARKERS)]
    tts = [name for name in generators if "tts" in name]
    return GeminiVoiceModels(sorted(chat, key=_newest_flash_first), sorted(tts, key=_newest_flash_first))


def make_client(api_key: str, timeout_seconds: int) -> genai.Client:
    # One attempt only: silent retries on a busy free tier look like a frozen app
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        timeout=timeout_seconds * 1000, retry_options=types.HttpRetryOptions(attempts=1),
    ))


def run_turn(
    wav_bytes: bytes,
    *,
    api_key: str,
    models: list[str],
    instructions: str,
    history: list[dict],
) -> VoiceTurn:
    """Transcribe and answer the recorded question; the reply is spoken later by `speak`."""
    client = make_client(api_key, ANSWER_TIMEOUT_SECONDS)
    contents = [_to_content(message) for message in history] + [
        types.Content(role="user", parts=[
            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav"),
            types.Part.from_text(text=AUDIO_PROMPT),
        ])
    ]
    config = types.GenerateContentConfig(
        system_instruction=instructions,
        response_mime_type="application/json",
        response_schema=REPLY_SCHEMA,
    )

    last_error = None
    for model in models:
        started = time.monotonic()
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
            log.info("answer from %s in %.1fs", model, time.monotonic() - started)
            break
        except errors.APIError as error:
            log.warning("%s failed after %.1fs: %s", model, time.monotonic() - started, error)
            if error.code not in TRY_NEXT_MODEL_CODES:
                raise VoiceTurnFailed(f"Gemini error ({error.code}): {error.message}") from error
            last_error = error
        except httpx.TimeoutException as error:
            raise VoiceTurnFailed(
                f"{model} took longer than {ANSWER_TIMEOUT_SECONDS}s to answer. "
                "Try again, or pick a Flash model in the sidebar."
            ) from error
        except httpx.HTTPError as error:
            raise VoiceTurnFailed(f"Could not reach Google: {error}") from error
    else:
        busy = last_error is not None and last_error.code in (429, 500, 503)
        raise VoiceTurnFailed(
            "All Gemini models on this key are busy or out of free quota right now. Wait a minute and try again."
            if busy else "None of the Gemini models for this key could answer."
        )

    transcription, reply = parse_reply(response.text)
    if not transcription:
        raise VoiceTurnFailed("No speech was detected. Try speaking a bit louder or longer.")

    new_history = history + [{"role": "user", "text": transcription}, {"role": "model", "text": reply}]
    return VoiceTurn(transcription, reply, None, new_history, model=model)


def speak(api_key: str, tts_model: str, voice: str, text: str) -> np.ndarray | None:
    """Return 24 kHz int16 speech, or None so the browser reads the reply instead."""
    client = make_client(api_key, SPEECH_TIMEOUT_SECONDS)
    started = time.monotonic()
    try:
        response = client.models.generate_content(
            model=tts_model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
                    ),
                ),
            ),
        )
        pcm = response.candidates[0].content.parts[0].inline_data.data
    except (errors.APIError, httpx.HTTPError, AttributeError, IndexError, TypeError) as error:
        log.warning("voice from %s failed after %.1fs, using browser voice: %s", tts_model, time.monotonic() - started, error)
        return None
    log.info("voice from %s in %.1fs", tts_model, time.monotonic() - started)
    return np.frombuffer(pcm, dtype=np.int16) if pcm else None


def parse_reply(text: str | None) -> tuple[str, str]:
    try:
        data = json.loads(text or "")
    except json.JSONDecodeError:
        return "", ""
    return str(data.get("transcription", "")).strip(), str(data.get("reply", "")).strip()


def _to_content(message: dict) -> types.Content:
    return types.Content(role=message["role"], parts=[types.Part.from_text(text=message["text"])])


def _newest_flash_first(name: str) -> tuple[bool, tuple[int, int], str]:
    match = VERSION_PATTERN.match(name)
    newest_first = (-int(match.group(1)), -int(match.group(2) or 0)) if match else (0, 0)
    is_stable_flash = "flash" in name and not any(marker in name for marker in UNSTABLE_MARKERS)
    return (not is_stable_flash, newest_first, name)
