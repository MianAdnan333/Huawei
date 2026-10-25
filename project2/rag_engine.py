"""Load documents, build a FAISS index and answer questions over it."""
import os
import tempfile
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd
from langchain_community.document_loaders import CSVLoader, Docx2txtLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_text_splitters import RecursiveCharacterTextSplitter

from gemini_models import is_model_unavailable

SUPPORTED_TYPES = ["pdf", "docx", "csv", "xlsx", "xls"]

PROMPT = ChatPromptTemplate.from_template(
    """You are a highly capable AI workspace assistant. Answer the user's question accurately using ONLY the retrieved context below. If you cannot answer based on the context, politely explain that the document doesn't contain that information.

Context:
{context}

Question:
{question}

Answer:"""
)


@dataclass
class DocumentIndex:
    vectorstore: FAISS
    sections: int
    chunks: int


@dataclass
class Answer:
    text: str
    model: str
    sources: list[Document]
    unavailable_models: list[str] = field(default_factory=list)


class AnswerFailed(Exception):
    def __init__(self, message: str, unavailable_models: list[str]):
        super().__init__(message)
        self.unavailable_models = unavailable_models


def load_documents(file_bytes: bytes, file_name: str) -> list[Document]:
    ext = file_name.rsplit(".", 1)[-1].lower()
    if ext not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported file format: .{ext}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == "pdf":
            return PyPDFLoader(tmp_path).load()
        if ext == "docx":
            return Docx2txtLoader(tmp_path).load()
        if ext == "csv":
            return CSVLoader(tmp_path).load()
        sheets = pd.read_excel(tmp_path, sheet_name=None)
        return [
            Document(
                page_content=f"Sheet: {sheet_name}\n" + df.to_string(index=False),
                metadata={"source": file_name, "sheet": sheet_name},
            )
            for sheet_name, df in sheets.items()
        ]
    finally:
        os.unlink(tmp_path)


def build_index(
    file_bytes: bytes, file_name: str, chunk_size: int, chunk_overlap: int, embeddings: Embeddings
) -> DocumentIndex:
    documents = load_documents(file_bytes, file_name)
    if not any(doc.page_content.strip() for doc in documents):
        raise ValueError("No text found in this file. Scanned PDFs (images only) are not supported.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    return DocumentIndex(FAISS.from_documents(chunks, embeddings), len(documents), len(chunks))


def answer_question(
    question: str, index: DocumentIndex, k: int, models: list[str], make_llm: Callable[[str], Runnable]
) -> Answer:
    """Answer from the top-k chunks, moving to the next model when one is unavailable."""
    sources = index.vectorstore.similarity_search(question, k=k)
    context = "\n\n".join(doc.page_content for doc in sources)

    unavailable = []
    for model in models:
        chain = PROMPT | make_llm(model) | StrOutputParser()
        try:
            text = chain.invoke({"context": context, "question": question})
            return Answer(text, model, sources, unavailable)
        except Exception as error:
            if not is_model_unavailable(error):
                raise AnswerFailed(str(error), unavailable) from error
            unavailable.append(model)
    raise AnswerFailed("None of the available Gemini models could answer.", unavailable)


def source_label(doc: Document) -> str:
    meta = doc.metadata
    if "page" in meta:
        return f"Page {meta['page'] + 1}"
    if "sheet" in meta:
        return f"Sheet: {meta['sheet']}"
    if "row" in meta:
        return f"Row {meta['row'] + 1}"
    return "Document"
