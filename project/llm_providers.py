"""Connect to a chat model provider and create LangChain chat models.

Every hosted provider is reached through its OpenAI-compatible API, so adding
one only needs a new entry in PROVIDERS.
"""
from dataclasses import dataclass

import httpx
import ollama
import openai
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

AUTO = "auto"
CUSTOM = "custom"
OLLAMA = "ollama"
NON_CHAT_MARKERS = (
    "embed", "moderation", "whisper", "tts", "dall-e", "image", "audio",
    "realtime", "transcribe", "search", "instruct", "aqa",
)


@dataclass(frozen=True)
class Provider:
    label: str
    base_url: str
    default_model: str
    key_prefix: str | None = None
    key_check_url: str | None = None  # for providers whose model list is public


PROVIDERS = {
    "openai": Provider("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini", "sk-"),
    "anthropic": Provider("Anthropic (Claude)", "https://api.anthropic.com/v1/", "claude-haiku-5-5", "sk-ant-"),
    "gemini": Provider("Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-2.5-flash", "AIza"),
    "groq": Provider("Groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", "gsk_"),
    "openrouter": Provider(
        "OpenRouter", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini", "sk-or-",
        key_check_url="https://openrouter.ai/api/v1/key",
    ),
    "xai": Provider("xAI (Grok)", "https://api.x.ai/v1", "grok-3-mini", "xai-"),
    "deepseek": Provider("DeepSeek", "https://api.deepseek.com", "deepseek-chat"),
    "mistral": Provider("Mistral", "https://api.mistral.ai/v1", "mistral-small-latest"),
}

PROVIDER_LABELS = {
    AUTO: "Auto-detect from key",
    **{provider_id: provider.label for provider_id, provider in PROVIDERS.items()},
    CUSTOM: "Custom (OpenAI-compatible URL)",
    OLLAMA: "Ollama (local, free, no key)",
}


class ConnectionFailed(Exception):
    """The provider rejected the credentials or could not be reached."""


@dataclass(frozen=True)
class Connection:
    provider: str
    models: list[str]
    api_key: str | None = None
    base_url: str | None = None


def detect_provider(api_key: str) -> str | None:
    """Guess the provider from the key prefix, checking longer prefixes first."""
    by_prefix = sorted(
        ((p.key_prefix, provider_id) for provider_id, p in PROVIDERS.items() if p.key_prefix),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    return next((provider_id for prefix, provider_id in by_prefix if api_key.startswith(prefix)), None)


def connect(provider: str, api_key: str | None = None, base_url: str | None = None) -> Connection:
    if provider == OLLAMA:
        return Connection(OLLAMA, _ollama_models())

    api_key = (api_key or "").strip()
    if not api_key:
        raise ConnectionFailed("Please enter your API key.")

    if provider == AUTO:
        provider = detect_provider(api_key)
        if provider is None:
            raise ConnectionFailed("Couldn't recognise this key. Please pick the provider from the list.")

    if provider == CUSTOM:
        base_url = (base_url or "").strip()
        if not base_url:
            raise ConnectionFailed("Please enter the API base URL.")
        models = _remote_models(api_key, base_url, fallback_model=None)
    elif provider in PROVIDERS:
        preset = PROVIDERS[provider]
        base_url = preset.base_url
        if preset.key_check_url:
            _check_key(api_key, preset.key_check_url)
        models = _remote_models(api_key, base_url, fallback_model=preset.default_model)
    else:
        raise ConnectionFailed(f"Unknown provider '{provider}'.")

    return Connection(provider, models, api_key, base_url)


def create_chat_model(connection: Connection, model: str, temperature: float):
    if connection.provider == OLLAMA:
        return ChatOllama(model=model, temperature=temperature)
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=connection.api_key,
        base_url=connection.base_url,
    )


def provider_label(connection: Connection) -> str:
    return PROVIDER_LABELS.get(connection.provider, connection.provider)


def chat_models(model_ids: list[str], default_model: str | None = None) -> list[str]:
    """Drop non-chat models and put the default model first."""
    models = sorted(
        model_id.removeprefix("models/") for model_id in model_ids
        if not any(marker in model_id.lower() for marker in NON_CHAT_MARKERS)
    )
    if default_model:
        if default_model in models:
            models.remove(default_model)
        models.insert(0, default_model)
    return models


KEY_REJECTED = "This API key was rejected. Check the key and the provider."
KEY_REJECTED_STATUS_CODES = (400, 401, 403)


def _check_key(api_key: str, key_check_url: str):
    try:
        response = httpx.get(key_check_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
    except httpx.HTTPError as error:
        raise ConnectionFailed(f"Could not reach {key_check_url}. Check your internet.") from error
    if response.status_code in KEY_REJECTED_STATUS_CODES:
        raise ConnectionFailed(KEY_REJECTED)


def _remote_models(api_key: str, base_url: str, fallback_model: str | None) -> list[str]:
    client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=15)
    try:
        model_ids = [model.id for model in client.models.list()]
    except openai.NotFoundError as error:
        # No /models endpoint; the key is checked on the first message instead.
        if fallback_model is None:
            raise ConnectionFailed("This URL has no model list. Check the base URL.") from error
        model_ids = []
    except openai.APIStatusError as error:
        if error.status_code in KEY_REJECTED_STATUS_CODES:
            raise ConnectionFailed(KEY_REJECTED) from error
        raise ConnectionFailed(f"The provider returned an error: {error}") from error
    except openai.APIConnectionError as error:
        raise ConnectionFailed(f"Could not reach {base_url}. Check the URL and your internet.") from error

    models = chat_models(model_ids, fallback_model)
    if not models:
        raise ConnectionFailed("No chat models were found for this key.")
    return models


def _ollama_models() -> list[str]:
    try:
        response = ollama.Client(timeout=5).list()
    except (ConnectionError, ollama.ResponseError) as error:
        raise ConnectionFailed(
            "Ollama is not running. Install it from https://ollama.com/download and start it."
        ) from error
    models = [model.model for model in response.models]
    if not models:
        raise ConnectionFailed("Ollama has no models yet. Run: ollama pull llama3.2")
    return models
