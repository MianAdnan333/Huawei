import streamlit as st

from llm_providers import CUSTOM, OLLAMA, PROVIDER_LABELS, ConnectionFailed, connect
from ui.styles import hero


def render_login():
    hero("🤖", "Your Custom Assistant", "Connect any AI provider with your API key")

    with st.container(border=True):
        provider = st.selectbox(
            "Provider",
            options=list(PROVIDER_LABELS),
            format_func=PROVIDER_LABELS.get,
            help="Auto-detect works for OpenAI, Anthropic, Gemini, Groq, OpenRouter and xAI keys.",
        )

        with st.form("login"):
            api_key = base_url = None
            if provider == OLLAMA:
                st.info("Runs on this computer with no key. Make sure the Ollama app is running.")
            else:
                api_key = st.text_input("API key", type="password", placeholder="Paste your API key")
            if provider == CUSTOM:
                base_url = st.text_input(
                    "API base URL",
                    placeholder="https://api.example.com/v1",
                    help="Any service with an OpenAI-compatible API.",
                )

            submitted = st.form_submit_button("Connect", type="primary", icon=":material/login:", width="stretch")

        if submitted:
            with st.spinner("Checking connection..."):
                try:
                    st.session_state.connection = connect(provider, api_key, base_url)
                except ConnectionFailed as error:
                    st.error(str(error))
                    return
            st.rerun()

    st.caption("🔒 Your key is kept only for this browser session and is never saved to disk.")
