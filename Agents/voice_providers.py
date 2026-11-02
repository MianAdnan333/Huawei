"""Voice back-ends behind one interface: connect with a key, then answer recorded questions."""
import asyncio
from dataclasses import dataclass

import numpy as np

import gemini_voice
import voice_core
from voice_core import VoiceTurn


@dataclass(frozen=True)
class Connection:
    models: list[str]
    tts_model: str | None = None


class GeminiProvider:
    label = "Google Gemini (free key)"
    key_label = "Google AI Studio API key"
    key_placeholder = "AIza..."
    key_help = "Free at aistudio.google.com/apikey"
    env_var = "GEMINI_API_KEY"
    voices = gemini_voice.GEMINI_VOICES

    def connect(self, api_key: str) -> Connection:
        models = gemini_voice.list_models(api_key)
        return Connection(models.chat, models.tts[0] if models.tts else None)

    def run_turn(self, wav_bytes: bytes, *, api_key, connection, model, voice, instructions, history) -> VoiceTurn:
        candidates = [model] + [m for m in connection.models if m != model]
        return gemini_voice.run_turn(
            wav_bytes, api_key=api_key, models=candidates, instructions=instructions, history=history,
        )

    def speak(self, text: str, *, api_key, connection, voice) -> np.ndarray | None:
        if not connection.tts_model:
            return None
        return gemini_voice.speak(api_key, connection.tts_model, voice, text)


class OpenAIProvider:
    label = "OpenAI (paid key)"
    key_label = "OpenAI API key"
    key_placeholder = "sk-..."
    key_help = "Speech-to-text, the agent and text-to-speech all use this key."
    env_var = "OPENAI_API_KEY"
    voices = voice_core.VOICES

    def connect(self, api_key: str) -> Connection:
        return Connection(voice_core.list_chat_models(api_key))

    def run_turn(self, wav_bytes: bytes, *, api_key, connection, model, voice, instructions, history) -> VoiceTurn:
        samples, rate = voice_core.wav_to_pcm(wav_bytes)
        return asyncio.run(voice_core.run_turn(
            samples, rate, api_key=api_key, model=model, voice=voice, instructions=instructions, history=history,
        ))

    def speak(self, text: str, *, api_key, connection, voice) -> np.ndarray | None:
        return None  # run_turn already returns the spoken reply


PROVIDERS = {"gemini": GeminiProvider(), "openai": OpenAIProvider()}
