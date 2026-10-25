"""List the Gemini chat and embedding models available to an API key."""
import re
from dataclasses import dataclass

from google import genai
from google.genai import errors

PREFERRED_EMBEDDING_MODEL = "gemini-embedding-001"
NON_TEXT_CHAT_MARKERS = ("image", "tts", "audio", "live", "robotics", "computer-use")
UNSTABLE_MARKERS = ("preview", "exp", "lite")
VERSION_PATTERN = re.compile(r"gemini-(\d+(?:\.\d+)?)")


class ModelListError(Exception):
    """Google rejected the key or the model list could not be fetched."""


@dataclass(frozen=True)
class GeminiModels:
    chat: list[str]
    embedding: list[str]


def fetch_models(api_key: str) -> GeminiModels:
    client = genai.Client(api_key=api_key)
    try:
        models = [(model.name, model.supported_actions or []) for model in client.models.list()]
    except errors.ClientError as error:
        raise ModelListError(f"Google rejected this API key: {error.message}") from error
    except errors.APIError as error:
        raise ModelListError(f"Could not reach Google: {error.message}") from error
    return sort_models(models)


def sort_models(models: list[tuple[str, list[str]]]) -> GeminiModels:
    """Split models into text chat and embedding lists.

    Chat models are ordered newest stable Flash first, since Google keeps listing
    older models that new keys can no longer call.
    """
    chat, embedding = [], []
    for name, actions in models:
        name = name.removeprefix("models/")
        if "embedContent" in actions:
            embedding.append(name)
        elif (
            "generateContent" in actions
            and name.startswith("gemini")
            and not any(marker in name for marker in NON_TEXT_CHAT_MARKERS)
        ):
            chat.append(name)
    return GeminiModels(
        chat=sorted(chat, key=_chat_sort_key),
        embedding=_preferred_first(sorted(embedding), PREFERRED_EMBEDDING_MODEL),
    )


def _chat_sort_key(name: str) -> tuple[bool, tuple[int, int], str]:
    match = VERSION_PATTERN.match(name)
    major, _, minor = match.group(1).partition(".") if match else ("0", "", "0")
    newest_first = (-int(major), -int(minor or 0))
    is_stable_flash = "flash" in name and not any(marker in name for marker in UNSTABLE_MARKERS)
    return (not is_stable_flash, newest_first, name)


def is_model_unavailable(error: Exception) -> bool:
    """True when Google refuses a listed model, e.g. one retired for new keys."""
    message = str(error)
    return "NOT_FOUND" in message or "no longer available" in message


def _preferred_first(names: list[str], preferred: str) -> list[str]:
    if preferred in names:
        names.remove(preferred)
        names.insert(0, preferred)
    return names
