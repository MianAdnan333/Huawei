import unittest

from gemini_models import PREFERRED_EMBEDDING_MODEL, sort_models


class SortModelsTest(unittest.TestCase):
    def test_splits_chat_and_embedding_models(self):
        models = sort_models([
            ("models/gemini-3-pro", ["generateContent"]),
            ("models/gemini-3.8-flash", ["generateContent", "countTokens"]),
            (f"models/{PREFERRED_EMBEDDING_MODEL}", ["embedContent"]),
            ("models/gemini-2.5-flash-image", ["generateContent"]),
            ("models/gemma-3-27b-it", ["generateContent"]),
            ("models/imagen-4", ["predict"]),
        ])
        self.assertEqual(models.chat, ["gemini-3.8-flash", "gemini-3-pro"])
        self.assertEqual(models.embedding, [PREFERRED_EMBEDDING_MODEL])

    def test_newest_stable_flash_comes_first(self):
        names = [
            "gemini-2.5-flash", "gemini-3.8-flash", "gemini-3.8-flash-lite",
            "gemini-4-flash-preview", "gemini-3-pro", "gemini-3.10-flash",
        ]
        models = sort_models([(f"models/{name}", ["generateContent"]) for name in names])
        self.assertEqual(
            models.chat[:4],
            ["gemini-3.10-flash", "gemini-3.8-flash", "gemini-2.5-flash", "gemini-4-flash-preview"],
        )

    def test_no_embedding_models(self):
        models = sort_models([("models/gemini-3-flash", ["generateContent"])])
        self.assertEqual(models.chat, ["gemini-3-flash"])
        self.assertEqual(models.embedding, [])


if __name__ == "__main__":
    unittest.main()
