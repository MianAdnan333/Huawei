import json
import unittest

import httpx
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from google.genai import errors

import gemini_voice
from gemini_voice import parse_reply, run_turn, sort_models, speak
from voice_core import VoiceTurnFailed

SPEECH = np.arange(10, dtype=np.int16).tobytes()


def api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"message": f"error {code}", "status": "X"}})


class FakeModels:
    def __init__(self, retired=(), reply=None, tts_fails=False, timeout=False, failing=None):
        self.retired, self.tts_fails, self.timeout, self.calls = set(retired), tts_fails, timeout, []
        self.failing = failing or {}  # model -> HTTP error code
        self.reply = reply or {"transcription": "Best time to visit Japan?", "reply": "Spring is lovely."}

    def generate_content(self, model, contents, config):
        self.calls.append(model)
        if self.timeout:
            raise httpx.ReadTimeout("timed out")
        if model in self.retired:
            raise api_error(404)
        if model in self.failing:
            raise api_error(self.failing[model])
        if "tts" in model:
            if self.tts_fails:
                raise api_error(429)
            part = SimpleNamespace(inline_data=SimpleNamespace(data=SPEECH))
            return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])
        return SimpleNamespace(text=json.dumps(self.reply))


def fake_client(fake_models):
    return patch.object(gemini_voice.genai, "Client", lambda api_key, http_options: SimpleNamespace(models=fake_models))


def fake_turn(fake_models, history=()):
    with fake_client(fake_models):
        return run_turn(
            b"RIFF-audio", api_key="AIza", models=["gemini-old", "gemini-new"],
            instructions="Be brief.", history=list(history),
        )


def fake_speak(fake_models):
    with fake_client(fake_models):
        return speak("AIza", "gemini-tts", "Kore", "Spring is lovely.")


class RunTurnTest(unittest.TestCase):
    def test_answers_with_text_first(self):
        turn = fake_turn(FakeModels())
        self.assertEqual((turn.transcription, turn.reply, turn.model), ("Best time to visit Japan?", "Spring is lovely.", "gemini-old"))
        self.assertIsNone(turn.audio)
        self.assertEqual([m["role"] for m in turn.history], ["user", "model"])

    def test_timeout_is_reported_not_hung(self):
        with self.assertRaises(VoiceTurnFailed) as caught:
            fake_turn(FakeModels(timeout=True))
        self.assertIn("took longer", str(caught.exception))

    def test_skips_retired_model(self):
        models = FakeModels(retired={"gemini-old"})
        turn = fake_turn(models)
        self.assertEqual(turn.model, "gemini-new")
        self.assertEqual(models.calls[:2], ["gemini-old", "gemini-new"])

    def test_speak_returns_pcm(self):
        np.testing.assert_array_equal(fake_speak(FakeModels()), np.arange(10, dtype=np.int16))

    def test_voice_failure_or_timeout_falls_back_to_browser_speech(self):
        self.assertIsNone(fake_speak(FakeModels(tts_fails=True)))
        self.assertIsNone(fake_speak(FakeModels(timeout=True)))

    def test_silence_is_reported(self):
        with self.assertRaises(VoiceTurnFailed):
            fake_turn(FakeModels(reply={"transcription": "", "reply": "?"}))

    def test_busy_or_out_of_quota_model_moves_to_next(self):
        for code in (429, 500, 503):
            with self.subTest(code=code):
                models = FakeModels(failing={"gemini-old": code})
                self.assertEqual(fake_turn(models).model, "gemini-new")

    def test_all_models_busy_gives_wait_message(self):
        with self.assertRaises(VoiceTurnFailed) as caught:
            fake_turn(FakeModels(failing={"gemini-old": 503, "gemini-new": 429}))
        self.assertIn("busy or out of free quota", str(caught.exception))

    def test_request_errors_are_not_retried_on_other_models(self):
        models = FakeModels(failing={"gemini-old": 400})
        with self.assertRaises(VoiceTurnFailed):
            fake_turn(models)
        self.assertEqual(models.calls, ["gemini-old"])

    def test_history_is_extended_not_mutated(self):
        previous = [{"role": "user", "text": "Hi"}, {"role": "model", "text": "Hello!"}]
        turn = fake_turn(FakeModels(), history=previous)
        self.assertEqual(len(turn.history), 4)
        self.assertEqual(len(previous), 2)


class SortModelsTest(unittest.TestCase):
    def test_splits_chat_and_tts_models(self):
        generate = ["generateContent"]
        models = sort_models([
            ("gemini-2.5-flash", generate), ("gemini-3.8-flash", generate), ("gemini-3-pro-preview", generate),
            ("gemini-2.5-flash-preview-tts", generate), ("gemini-2.5-flash-image", generate),
            ("gemini-embedding-001", ["embedContent"]), ("gemma-3-27b-it", generate),
        ])
        self.assertEqual(models.chat, ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-3-pro-preview"])
        self.assertEqual(models.tts, ["gemini-2.5-flash-preview-tts"])


class ParseReplyTest(unittest.TestCase):
    def test_valid_and_invalid_json(self):
        self.assertEqual(parse_reply('{"transcription": " hi ", "reply": "hello"}'), ("hi", "hello"))
        self.assertEqual(parse_reply("not json"), ("", ""))
        self.assertEqual(parse_reply(None), ("", ""))


if __name__ == "__main__":
    unittest.main()
