import io
import unittest

import pandas as pd
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.runnables import RunnableLambda

from rag_engine import AnswerFailed, answer_question, build_index, load_documents, source_label

CSV_BYTES = b"section,detail\nEducation,BSc Computer Science\nSkills,Python\n"


def excel_bytes() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="First", index=False)
        pd.DataFrame({"b": [2]}).to_excel(writer, sheet_name="Second", index=False)
    return buffer.getvalue()


def fake_llm(failing_models=(), other_error_models=()):
    def make(model):
        def run(_prompt):
            if model in failing_models:
                raise RuntimeError(f"Error calling model '{model}' (NOT_FOUND): 404 NOT_FOUND")
            if model in other_error_models:
                raise RuntimeError("429 RESOURCE_EXHAUSTED")
            return f"answer from {model}"
        return RunnableLambda(run)
    return make


class LoadDocumentsTest(unittest.TestCase):
    def test_csv_gives_one_document_per_row(self):
        docs = load_documents(CSV_BYTES, "resume.csv")
        self.assertEqual(len(docs), 2)
        self.assertIn("BSc Computer Science", docs[0].page_content)

    def test_excel_gives_one_document_per_sheet(self):
        docs = load_documents(excel_bytes(), "book.xlsx")
        self.assertEqual([d.metadata["sheet"] for d in docs], ["First", "Second"])

    def test_unsupported_type_is_rejected(self):
        with self.assertRaises(ValueError):
            load_documents(b"x", "notes.txt")


class AnswerQuestionTest(unittest.TestCase):
    def setUp(self):
        self.index = build_index(CSV_BYTES, "resume.csv", 1000, 100, DeterministicFakeEmbedding(size=16))

    def test_index_counts(self):
        self.assertEqual((self.index.sections, self.index.chunks), (2, 2))

    def test_falls_back_past_unavailable_models(self):
        answer = answer_question("education?", self.index, 2, ["old", "new"], fake_llm(failing_models={"old"}))
        self.assertEqual((answer.text, answer.model, answer.unavailable_models), ("answer from new", "new", ["old"]))
        self.assertEqual(len(answer.sources), 2)

    def test_other_errors_stop_immediately(self):
        with self.assertRaises(AnswerFailed) as caught:
            answer_question("q", self.index, 1, ["a", "b"], fake_llm(other_error_models={"a"}))
        self.assertIn("RESOURCE_EXHAUSTED", str(caught.exception))

    def test_all_models_unavailable(self):
        with self.assertRaises(AnswerFailed) as caught:
            answer_question("q", self.index, 1, ["a", "b"], fake_llm(failing_models={"a", "b"}))
        self.assertEqual(caught.exception.unavailable_models, ["a", "b"])


class SourceLabelTest(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(source_label(Document(page_content="", metadata={"page": 0})), "Page 1")
        self.assertEqual(source_label(Document(page_content="", metadata={"sheet": "Q1"})), "Sheet: Q1")
        self.assertEqual(source_label(Document(page_content="", metadata={"row": 4})), "Row 5")
        self.assertEqual(source_label(Document(page_content="")), "Document")


if __name__ == "__main__":
    unittest.main()
