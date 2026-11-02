import asyncio
import io
import unittest
import wave
from unittest.mock import patch

import numpy as np
from agents.voice import STTModel, TTSModel, VoiceModelProvider

import voice_core
from voice_core import (
    DEFAULT_MODEL, FALLBACK_MODEL, VoiceTurnFailed, pcm_to_wav, run_turn, sort_chat_models, wav_to_pcm,
)


def make_wav(samples: np.ndarray, channels: int = 1, width: int = 2, rate: int = 16_000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())
    return buffer.getvalue()


class FakeSTT(STTModel):
    def __init__(self, text):
        self.text = text

    @property
    def model_name(self):
        return "fake-stt"

    async def transcribe(self, input, settings, trace_include_sensitive_data, trace_include_sensitive_audio_data):
        return self.text

    async def create_session(self, *args, **kwargs):
        raise NotImplementedError


class FakeTTS(TTSModel):
    @property
    def model_name(self):
        return "fake-tts"

    async def run(self, text, settings):
        yield np.full(480, 7, dtype=np.int16).tobytes()


class FakeProvider(VoiceModelProvider):
    def __init__(self, transcription, **kwargs):
        self.transcription = transcription

    def get_stt_model(self, model_name):
        return FakeSTT(self.transcription)

    def get_tts_model(self, model_name):
        return FakeTTS()


class FakeRunResult:
    def __init__(self, history):
        self.history = history

    def to_input_list(self):
        return self.history + [{"role": "assistant", "content": "Visit in spring."}]


async def fake_stream_text(result):
    for chunk in ("Visit ", "in spring."):
        yield chunk


def run_fake_turn(transcription="When should I visit Japan?", history=()):
    with patch.object(voice_core, "OpenAIVoiceModelProvider", lambda **kw: FakeProvider(transcription)), \
         patch.object(voice_core.Runner, "run_streamed", lambda agent, history: FakeRunResult(list(history))), \
         patch.object(voice_core.VoiceWorkflowHelper, "stream_text_from", fake_stream_text):
        return asyncio.run(run_turn(
            np.zeros(2400, dtype=np.int16), 24_000, api_key="sk-test", model="gpt-x", voice="coral",
            instructions="Be brief.", history=list(history),
        ))


class RunTurnTest(unittest.TestCase):
    def test_returns_transcript_reply_audio_and_history(self):
        turn = run_fake_turn()
        self.assertEqual(turn.transcription, "When should I visit Japan?")
        self.assertEqual(turn.reply, "Visit in spring.")
        self.assertEqual(turn.audio.dtype, np.int16)
        self.assertGreater(len(turn.audio), 0)
        self.assertEqual([item["role"] for item in turn.history], ["user", "assistant"])

    def test_keeps_previous_history_without_mutating_it(self):
        previous = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
        turn = run_fake_turn(history=previous)
        self.assertEqual(len(turn.history), 4)
        self.assertEqual(len(previous), 2)

    def test_silence_is_reported(self):
        with self.assertRaises(VoiceTurnFailed):
            run_fake_turn(transcription="  ")


class AudioConversionTest(unittest.TestCase):
    def test_round_trip(self):
        samples = np.array([0, 1000, -1000, 32767], dtype=np.int16)
        decoded, rate = wav_to_pcm(pcm_to_wav(samples, 24_000))
        self.assertEqual(rate, 24_000)
        np.testing.assert_array_equal(decoded, samples)

    def test_stereo_is_mixed_to_mono(self):
        stereo = np.array([100, 300, -200, -400], dtype=np.int16)
        decoded, _ = wav_to_pcm(make_wav(stereo, channels=2))
        np.testing.assert_array_equal(decoded, [200, -300])

    def test_8_bit_audio_is_converted(self):
        decoded, _ = wav_to_pcm(make_wav(np.array([128, 255, 0], dtype=np.uint8), width=1))
        self.assertEqual(decoded.dtype, np.int16)
        self.assertEqual(decoded[0], 0)


class SortChatModelsTest(unittest.TestCase):
    def test_keeps_chat_models_with_preferred_first(self):
        ids = ["gpt-4o", "whisper-1", FALLBACK_MODEL, DEFAULT_MODEL, "gpt-4o-mini-tts", "gpt-realtime"]
        self.assertEqual(sort_chat_models(ids), [DEFAULT_MODEL, FALLBACK_MODEL, "gpt-4o"])

    def test_without_default_model_fallback_comes_first(self):
        self.assertEqual(sort_chat_models(["gpt-4o", FALLBACK_MODEL]), [FALLBACK_MODEL, "gpt-4o"])


if __name__ == "__main__":
    unittest.main()
