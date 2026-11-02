"""Voice agent turn: speech in, agent reply as text and speech out (OpenAI Agents SDK)."""
import io
import wave
from collections.abc import AsyncIterator
from dataclasses import dataclass

import numpy as np
import openai
from agents import Agent, OpenAIResponsesModel, Runner, TResponseInputItem
from agents.voice import (
    AudioInput,
    OpenAIVoiceModelProvider,
    TTSModelSettings,
    VoicePipeline,
    VoicePipelineConfig,
    VoiceWorkflowBase,
    VoiceWorkflowHelper,
)

SAMPLE_RATE = 24_000  # OpenAI TTS returns 24 kHz, 16-bit mono PCM
DEFAULT_MODEL = "gpt-5.4-mini"
FALLBACK_MODEL = "gpt-4o-mini"
VOICES = ["coral", "alloy", "ash", "ballad", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]
DEFAULT_INSTRUCTIONS = (
    "You are a friendly travel advisor. "
    "Keep spoken answers short, natural, and easy to follow. "
    "Keep responses to 2-3 sentences max."
)
NON_CHAT_MARKERS = ("audio", "realtime", "transcribe", "tts", "image", "search", "instruct", "embedding")


class InvalidApiKey(Exception):
    """OpenAI rejected the key or could not be reached."""


class VoiceTurnFailed(Exception):
    """The speech, agent or text-to-speech step failed."""


@dataclass
class VoiceTurn:
    transcription: str
    reply: str
    audio: np.ndarray | None  # None when the reply should be read aloud by the browser
    history: list
    model: str = ""


class ConversationWorkflow(VoiceWorkflowBase):
    """Runs one agent over a shared history and keeps the latest transcript and reply."""

    def __init__(self, agent: Agent, history: list[TResponseInputItem]):
        self.agent = agent
        self.history = list(history)
        self.transcription = ""
        self.reply = ""

    async def run(self, transcription: str) -> AsyncIterator[str]:
        self.transcription = transcription
        self.history.append({"role": "user", "content": transcription})
        result = Runner.run_streamed(self.agent, self.history)
        async for chunk in VoiceWorkflowHelper.stream_text_from(result):
            self.reply += chunk
            yield chunk
        self.history = result.to_input_list()


def list_chat_models(api_key: str) -> list[str]:
    """Return GPT chat models for this key, preferred default first."""
    try:
        model_ids = [model.id for model in openai.OpenAI(api_key=api_key, timeout=15).models.list()]
    except openai.AuthenticationError as error:
        raise InvalidApiKey("OpenAI rejected this API key. Check it and try again.") from error
    except openai.OpenAIError as error:
        raise InvalidApiKey(f"Could not reach OpenAI: {error}") from error
    return sort_chat_models(model_ids)


def sort_chat_models(model_ids: list[str]) -> list[str]:
    models = sorted(
        model_id for model_id in model_ids
        if model_id.startswith("gpt-") and not any(marker in model_id for marker in NON_CHAT_MARKERS)
    )
    for preferred in (FALLBACK_MODEL, DEFAULT_MODEL):
        if preferred in models:
            models.remove(preferred)
            models.insert(0, preferred)
    return models


async def run_turn(
    audio: np.ndarray,
    frame_rate: int,
    *,
    api_key: str,
    model: str,
    voice: str,
    instructions: str,
    history: list[TResponseInputItem],
) -> VoiceTurn:
    client = openai.AsyncOpenAI(api_key=api_key)
    agent = Agent(
        name="Voice Agent",
        instructions=instructions,
        model=OpenAIResponsesModel(model=model, openai_client=client),
    )
    workflow = ConversationWorkflow(agent, history)
    pipeline = VoicePipeline(
        workflow=workflow,
        config=VoicePipelineConfig(
            model_provider=OpenAIVoiceModelProvider(openai_client=client),
            tts_settings=TTSModelSettings(voice=voice),
            tracing_disabled=True,
            trace_include_sensitive_audio_data=False,
        ),
    )

    result = await pipeline.run(AudioInput(buffer=audio, frame_rate=frame_rate))
    chunks = []
    async for event in result.stream():
        if event.type == "voice_stream_event_audio" and event.data is not None:
            chunks.append(event.data)
        elif event.type == "voice_stream_event_error":
            raise VoiceTurnFailed(str(event.error))

    if not workflow.transcription.strip():
        raise VoiceTurnFailed("No speech was detected. Try speaking a bit louder or longer.")
    speech = np.concatenate(chunks).astype(np.int16) if chunks else np.zeros(0, dtype=np.int16)
    return VoiceTurn(workflow.transcription, workflow.reply, speech, workflow.history, model=model)


def wav_to_pcm(wav_bytes: bytes) -> tuple[np.ndarray, int]:
    """Decode WAV bytes into mono int16 samples and their sample rate."""
    with wave.open(io.BytesIO(wav_bytes)) as wav:
        channels, width, rate = wav.getnchannels(), wav.getsampwidth(), wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if width == 2:
        samples = np.frombuffer(frames, dtype=np.int16)
    elif width == 1:
        samples = ((np.frombuffer(frames, dtype=np.uint8).astype(np.int16) - 128) << 8)
    elif width == 4:
        samples = (np.frombuffer(frames, dtype=np.int32) >> 16).astype(np.int16)
    else:
        raise ValueError(f"Unsupported WAV sample width: {width} bytes")

    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return samples, rate


def pcm_to_wav(samples: np.ndarray, rate: int = SAMPLE_RATE) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(samples.astype(np.int16).tobytes())
    return buffer.getvalue()
