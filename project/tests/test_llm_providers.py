import unittest
from unittest.mock import patch

import llm_providers
from llm_providers import (
    AUTO, CUSTOM, OLLAMA, PROVIDERS, ConnectionFailed, chat_models, connect, detect_provider,
)


class DetectProviderTest(unittest.TestCase):
    def test_recognises_known_prefixes(self):
        cases = {
            "sk-ant-abc": "anthropic",
            "sk-or-v1-abc": "openrouter",
            "sk-proj-abc": "openai",
            "gsk_abc": "groq",
            "AIzaabc": "gemini",
            "xai-abc": "xai",
        }
        for key, provider in cases.items():
            with self.subTest(key=key):
                self.assertEqual(detect_provider(key), provider)

    def test_unknown_prefix_returns_none(self):
        self.assertIsNone(detect_provider("abc123"))


class ChatModelsTest(unittest.TestCase):
    def test_drops_non_chat_models_and_puts_default_first(self):
        ids = ["whisper-1", "gpt-4o", "text-embedding-3-small", "gpt-4o-mini"]
        self.assertEqual(chat_models(ids, "gpt-4o-mini"), ["gpt-4o-mini", "gpt-4o"])

    def test_strips_gemini_models_prefix(self):
        self.assertEqual(chat_models(["models/gemini-2.5-flash"]), ["gemini-2.5-flash"])

    def test_default_is_added_when_list_is_empty(self):
        self.assertEqual(chat_models([], "deepseek-chat"), ["deepseek-chat"])


class ConnectTest(unittest.TestCase):
    def test_empty_key_is_rejected(self):
        with self.assertRaises(ConnectionFailed):
            connect("openai", "   ")

    def test_auto_with_unknown_key_asks_for_provider(self):
        with self.assertRaises(ConnectionFailed):
            connect(AUTO, "abc123")

    def test_custom_requires_base_url(self):
        with self.assertRaises(ConnectionFailed):
            connect(CUSTOM, "key", "  ")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ConnectionFailed):
            connect("other", "key")

    def test_auto_uses_detected_provider_url(self):
        with patch.object(llm_providers, "_remote_models", return_value=["m"]) as remote:
            connection = connect(AUTO, "  gsk_test  ")
        self.assertEqual(connection.provider, "groq")
        self.assertEqual(connection.api_key, "gsk_test")
        remote.assert_called_once_with("gsk_test", PROVIDERS["groq"].base_url, fallback_model=PROVIDERS["groq"].default_model)

    def test_custom_uses_given_url(self):
        with patch.object(llm_providers, "_remote_models", return_value=["m"]):
            connection = connect(CUSTOM, "key", " https://api.example.com/v1 ")
        self.assertEqual(connection.base_url, "https://api.example.com/v1")

    def test_ollama_not_running_is_reported(self):
        with patch.object(llm_providers.ollama.Client, "list", side_effect=ConnectionError):
            with self.assertRaises(ConnectionFailed):
                connect(OLLAMA)


if __name__ == "__main__":
    unittest.main()
