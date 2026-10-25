import os
from dataclasses import dataclass

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from gemini_models import GeminiModels, ModelListError, fetch_models
from rag_engine import SUPPORTED_TYPES, AnswerFailed, answer_question, build_index, source_label
from ui_styles import (
    apply_theme, doc_card, empty_state, hero, onboarding_steps, panel_title, side_title, topbar,
)

st.set_page_config(
    page_title="Multi-Doc RAG Workspace",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="auto",
)

SUGGESTIONS = [
    "Summarize this document",
    "List the key points",
    "What names, dates or numbers are mentioned?",
]


@dataclass
class Settings:
    api_key: str
    models: GeminiModels | None
    model_error: str | None
    chat_model: str | None = None
    chat_options: list[str] | None = None
    embedding_model: str | None = None
    chunk_size: int = 1000
    chunk_overlap: int = 150
    k: int = 4
    temperature: float = 0.2


@st.cache_data(ttl=3600, show_spinner=False)
def get_models(api_key: str) -> GeminiModels:
    return fetch_models(api_key)


def render_sidebar() -> Settings:
    with st.sidebar:
        st.markdown('<div class="side-brand">✨ Workspace</div>', unsafe_allow_html=True)

        side_title("Appearance")
        dark = st.toggle("Dark mode", value=True)
        apply_theme(dark)

        side_title("Connection")
        api_key = st.text_input(
            "Google Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""),
            placeholder="Paste your key", help="Get a free key at aistudio.google.com",
        ).strip()

        models, model_error = None, None
        if api_key:
            try:
                with st.spinner("Checking API key..."):
                    models = get_models(api_key)
            except ModelListError as error:
                model_error = str(error)
        settings = Settings(api_key, models, model_error)

        if models and models.chat and models.embedding:
            side_title("Models")
            unavailable = st.session_state.setdefault("unavailable_models", set())
            settings.chat_options = [m for m in models.chat if m not in unavailable] or models.chat
            if "next_chat_model" in st.session_state:
                st.session_state.chat_model = st.session_state.pop("next_chat_model")
            if st.session_state.get("chat_model") not in settings.chat_options:
                st.session_state.pop("chat_model", None)
            settings.chat_model = st.selectbox("Chat model", settings.chat_options, key="chat_model")
            settings.embedding_model = st.selectbox("Embedding model", models.embedding)

            with st.expander("⚙️ Retrieval settings"):
                settings.chunk_size = st.slider("Chunk size (characters)", 300, 2000, 1000, step=100)
                settings.chunk_overlap = st.slider("Chunk overlap", 0, 500, 150, step=25)
                settings.k = st.slider("Retrieved chunks (k)", 1, 10, 4)
                settings.temperature = st.slider("Temperature", 0.0, 1.0, 0.2, step=0.05)

            st.write("")
            if st.button("🗑️ Clear chat", width="stretch", disabled=not st.session_state.get("messages")):
                st.session_state.messages = []
                st.rerun()

    return settings


def render_document_panel(settings: Settings):
    with st.container(border=True, key="doc_panel"):
        panel_title("📄", "Document", "Upload one file to chat with it.")
        uploaded = st.file_uploader(
            "Upload a document", type=SUPPORTED_TYPES, label_visibility="collapsed",
        )

        if uploaded is None:
            for key in ("index", "file_sig", "messages"):
                st.session_state.pop(key, None)
            st.caption("Supported: PDF, DOCX, CSV, XLSX, XLS. Scanned (image-only) PDFs have no text to read.")
            return

        file_sig = (uploaded.name, uploaded.size, settings.chunk_size, settings.chunk_overlap, settings.embedding_model)
        if st.session_state.get("file_sig") != file_sig:
            with st.spinner("Reading and indexing your document..."):
                try:
                    embeddings = GoogleGenerativeAIEmbeddings(
                        model=f"models/{settings.embedding_model}", google_api_key=settings.api_key,
                    )
                    st.session_state.index = build_index(
                        uploaded.getvalue(), uploaded.name, settings.chunk_size, settings.chunk_overlap, embeddings,
                    )
                    st.session_state.file_sig = file_sig
                    st.session_state.messages = []
                except Exception as error:
                    for key in ("index", "file_sig"):
                        st.session_state.pop(key, None)
                    st.error(f"Could not process this file: {error}")
                    return

        index = st.session_state.index
        doc_card(uploaded.name, uploaded.size, index.sections, index.chunks, settings.embedding_model)


def render_message(message: dict):
    avatar = "🧑" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        sources = message.get("sources")
        if sources:
            with st.expander(f"📎 Sources ({len(sources)})"):
                for label, text in sources:
                    st.markdown(f"**{label}**")
                    st.caption(text[:500] + ("…" if len(text) > 500 else ""))


def ask(question: str, settings: Settings, history):
    messages = st.session_state.messages
    messages.append({"role": "user", "content": question})

    with history:
        render_message(messages[-1])
        with st.chat_message("assistant", avatar="✨"):
            with st.spinner("Searching your document..."):
                candidates = [settings.chat_model] + [m for m in settings.chat_options if m != settings.chat_model]
                try:
                    answer = answer_question(
                        question, st.session_state.index, settings.k, candidates,
                        lambda model: ChatGoogleGenerativeAI(
                            model=model, google_api_key=settings.api_key, temperature=settings.temperature,
                        ),
                    )
                except AnswerFailed as failure:
                    st.session_state.unavailable_models.update(failure.unavailable_models)
                    messages.pop()
                    st.error(f"Could not answer: {failure}")
                    return
                except Exception as error:
                    messages.pop()
                    st.error(f"Could not search the document: {error}")
                    return

    st.session_state.unavailable_models.update(answer.unavailable_models)
    messages.append({
        "role": "assistant",
        "content": answer.text,
        "sources": [(source_label(doc), doc.page_content) for doc in answer.sources],
    })
    if answer.model != settings.chat_model:
        st.session_state.next_chat_model = answer.model
        st.toast(f"{settings.chat_model} isn't available for your key. Switched to {answer.model}.", icon="🔄")
    st.rerun()


def render_chat_panel(settings: Settings):
    with st.container(border=True, key="chat_panel"):
        panel_title("💬", "Chat", f"Answers come only from your document · {settings.chat_model}")

        if "index" not in st.session_state:
            empty_state("📂", "No document yet", "Upload a file on the left to start asking questions.")
            return

        messages = st.session_state.setdefault("messages", [])
        history = st.container(height=470, border=False)
        suggestion = None
        with history:
            if not messages:
                empty_state("✨", "Your document is ready", "Ask a question below, or try one of these:")
                for column, text in zip(st.columns(len(SUGGESTIONS)), SUGGESTIONS):
                    if column.button(text, width="stretch"):
                        suggestion = text
            for message in messages:
                render_message(message)

        question = st.chat_input("Ask a question about your document...") or suggestion
        if question:
            ask(question, settings, history)


settings = render_sidebar()

if not settings.api_key or settings.model_error:
    topbar(False, "Not connected")
    hero()
    if settings.model_error:
        st.error(f"🔑 {settings.model_error}")
    onboarding_steps()
    st.stop()

if not settings.models.chat or not settings.models.embedding:
    topbar(False, "No models available")
    st.error("This API key has no Gemini chat or embedding models available.")
    st.stop()

topbar(True, "Connected to Gemini")
hero(compact=True)
left, right = st.columns([5, 7], gap="large")
with left:
    render_document_panel(settings)
with right:
    render_chat_panel(settings)
