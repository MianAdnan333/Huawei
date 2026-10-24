from dataclasses import dataclass

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from llm_providers import Connection, create_chat_model, provider_label
from ui.styles import hero

DEFAULT_SYSTEM_ROLE = "You are a helpful assistant."
SUGGESTIONS = [
    "Explain neural networks simply",
    "Write a Python function to reverse a string",
    "Give me 3 tips to learn faster",
]


@dataclass(frozen=True)
class ChatSettings:
    model: str
    temperature: float
    system_role: str


def render_chat(connection: Connection):
    settings = _render_sidebar(connection)
    history = st.session_state.setdefault("messages", [])

    suggestion = None
    if not history:
        suggestion = _render_welcome()

    for message in history:
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)

    prompt = st.chat_input("Message your assistant...") or suggestion
    if prompt:
        _answer(prompt, history, connection, settings)


def _render_sidebar(connection: Connection) -> ChatSettings:
    with st.sidebar:
        st.markdown("## 🤖 Assistant")
        st.markdown(
            f'<span class="status-pill">● Connected · {provider_label(connection)}</span>',
            unsafe_allow_html=True,
        )
        st.divider()

        model = st.selectbox("Model", connection.models, accept_new_options=True,
                             help="Pick from the list or type any model name.")
        temperature = st.slider(
            "Creativity", 0.0, 1.0, 0.5, 0.1,
            help="Lower gives focused answers, higher gives more creative ones.",
        )
        system_role = st.text_area("System role", DEFAULT_SYSTEM_ROLE, height=110)

        st.divider()
        new_chat, log_out = st.columns(2)
        if new_chat.button("New chat", icon=":material/add:", width="stretch"):
            st.session_state.messages = []
            st.rerun()
        if log_out.button("Log out", icon=":material/logout:", width="stretch"):
            st.session_state.clear()
            st.rerun()

    return ChatSettings(model, temperature, system_role.strip() or DEFAULT_SYSTEM_ROLE)


def _render_welcome() -> str | None:
    hero("💬", "How can I help you today?", "Ask anything, or try one of these:")
    clicked = None
    for column, suggestion in zip(st.columns(len(SUGGESTIONS)), SUGGESTIONS):
        if column.button(suggestion, width="stretch"):
            clicked = suggestion
    return clicked


def _answer(prompt: str, history: list, connection: Connection, settings: ChatSettings):
    history.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    chat = create_chat_model(connection, settings.model, settings.temperature)
    messages = [SystemMessage(content=settings.system_role), *history]

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(chunk.content for chunk in chat.stream(messages))
        except Exception as error:
            history.pop()
            st.error(f"Request failed: {error}")
            return

    history.append(AIMessage(content=reply))
    st.rerun()
