import json
import logging
import os

import streamlit as st
from dotenv import find_dotenv, load_dotenv

from voice_core import DEFAULT_INSTRUCTIONS, SAMPLE_RATE, InvalidApiKey, pcm_to_wav
from voice_providers import PROVIDERS, Connection
from voice_styles import apply_theme, hero, section_label, side_title, tips, topbar

load_dotenv(find_dotenv(), override=True)

log = logging.getLogger("voice_agent")
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[voice] %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)

st.set_page_config(page_title="Voice Agent", page_icon="🎙️", layout="centered", initial_sidebar_state="auto")

EXAMPLES = ["Plan a weekend in Istanbul", "Best time to visit Japan?", "Cheap beach trips in Asia"]

state = st.session_state
state.setdefault("turns", [])
state.setdefault("history", [])
state.setdefault("recorder_key", 0)


@st.cache_data(ttl=3600, show_spinner=False)
def connect(provider_id: str, api_key: str) -> Connection:
    return PROVIDERS[provider_id].connect(api_key)


def reset_conversation():
    state.turns, state.history = [], []


def browser_speech(text: str, autoplay: bool):
    """Read the reply aloud with the browser's built-in voice (free, no API call)."""
    # The reply is model output: keep it a JS string literal with no "<" that could end the script
    safe_text = json.dumps(text).replace("<", "\\u003c")
    st.iframe(f"""
        <button id="say" style="border:0;border-radius:999px;padding:8px 16px;cursor:pointer;font:600 14px Inter,sans-serif;
            color:#fff;background:linear-gradient(135deg,#6366f1,#a855f7,#ec4899)">🔊 Read aloud</button>
        <script>
            const say = () => {{ speechSynthesis.cancel(); speechSynthesis.speak(new SpeechSynthesisUtterance({safe_text})); }};
            document.getElementById("say").onclick = say;
            {"say();" if autoplay else ""}
        </script>
    """, height=46)


def microphone_check():
    """Explain why recording can't start; the recorder itself fails silently."""
    st.iframe("""
        <div id="mic" style="font:500 13px Inter,sans-serif;color:#98a1b9;padding:6px 2px"></div>
        <script>
            const show = (html, color) => { const el = document.getElementById("mic"); el.innerHTML = html; el.style.color = color; };
            const page = window.parent;
            if (!page.isSecureContext || !page.navigator.mediaDevices) {
                show("⚠️ The microphone only works on <b>http://localhost</b> or an <b>https://</b> address. "
                    + "Open <b>http://localhost:8501</b> instead of the Network URL.", "#f59e0b");
            } else if (page.navigator.permissions) {
                page.navigator.permissions.query({ name: "microphone" }).then(status => {
                    const render = () => status.state === "denied"
                        ? show("⚠️ Microphone is blocked. Click the 🔒 / ⓘ icon left of the address bar → "
                            + "<b>Microphone: Allow</b>, then reload the page.", "#f59e0b")
                        : show("👆 Tap the purple 🎤 button to start speaking, tap the red ⏹ button when you are done. Allow microphone access if your browser asks.", "#98a1b9");
                    render();
                    status.onchange = render;
                }).catch(() => show("👆 Tap the purple 🎤 button to start, the red ⏹ button to send.", "#98a1b9"));
            }
        </script>
    """, height=52)


with st.sidebar:
    st.markdown('<div class="side-brand">🎙️ Voice Agent</div>', unsafe_allow_html=True)

    side_title("Appearance")
    apply_theme(st.toggle("Dark mode", value=True))

    side_title("Connection")
    provider_id = st.selectbox("Provider", list(PROVIDERS), format_func=lambda p: PROVIDERS[p].label)
    provider = PROVIDERS[provider_id]
    if state.get("provider_id") != provider_id:
        state.provider_id = provider_id
        reset_conversation()

    api_key = st.text_input(
        provider.key_label, type="password", value=os.getenv(provider.env_var, ""),
        placeholder=provider.key_placeholder, help=provider.key_help, key=f"key_{provider_id}",
    ).strip()

    connection, key_error = None, None
    if api_key:
        try:
            with st.spinner("Checking API key..."):
                connection = connect(provider_id, api_key)
        except InvalidApiKey as error:
            key_error = str(error)

    if connection and connection.models:
        side_title("Agent")
        model_key = f"model_{provider_id}"
        if "next_model" in state:
            state[model_key] = state.pop("next_model")
        if state.get(model_key) not in connection.models:
            state.pop(model_key, None)
        model = st.selectbox("Model", connection.models, key=model_key)
        voice = st.selectbox("Voice", provider.voices, format_func=str.title)
        instructions = st.text_area("Personality", DEFAULT_INSTRUCTIONS, height=130)
        if provider_id == "gemini" and not connection.tts_model:
            st.caption("🔊 No Gemini voice model on this key, so your browser reads answers aloud.")
        st.write("")
        st.button("🗑️ New conversation", width="stretch", on_click=reset_conversation, disabled=not state.turns)

if not api_key or key_error or not (connection and connection.models):
    topbar(False, "Not connected")
    hero(f"Paste your {provider.key_label} in the sidebar, then ask your question out loud.")
    if key_error:
        st.error(f"🔑 {key_error}")
    elif api_key:
        st.error("This key has no chat models available.")
    tips(EXAMPLES)
    st.stop()

topbar(True, f"Connected · {model}")
hero("Tap the purple 🎤 button below, ask your question, then tap ⏹. The answer is spoken back to you.")

with st.container(key="recorder_panel"):
    recording = st.audio_input("🎤 Tap the button to record your question", sample_rate=SAMPLE_RATE, key=f"recorder_{state.recorder_key}")
    microphone_check()

if recording is not None:
    with st.spinner("Listening to your question and writing an answer..."):
        try:
            turn = provider.run_turn(
                recording.getvalue(), api_key=api_key, connection=connection, model=model, voice=voice,
                instructions=instructions.strip() or DEFAULT_INSTRUCTIONS, history=state.history,
            )
        except Exception as error:
            st.error(f"Something went wrong: {error}")
            turn = None
    state.recorder_key += 1
    if turn is not None:
        state.history = turn.history
        audio = pcm_to_wav(turn.audio) if turn.audio is not None and len(turn.audio) else None
        # Show the text reply right away; the voice is generated on the next run
        state.turns.append({"you": turn.transcription, "reply": turn.reply, "audio": audio, "voice_pending": audio is None})
        state.autoplay_last = True
        if turn.model and turn.model != model:
            state.next_model = turn.model
            st.toast(f"{model} is busy or unavailable right now. Switched to {turn.model}.", icon="🔄")
        st.rerun()

if not state.turns:
    tips(EXAMPLES)
else:
    section_label("Conversation")
    autoplay = state.pop("autoplay_last", False)
    for index, turn in enumerate(state.turns):
        is_latest = index == len(state.turns) - 1
        with st.chat_message("user", avatar="🧑"):
            st.markdown(turn["you"])
        with st.chat_message("assistant", avatar="🎙️"):
            st.markdown(turn["reply"])
            if turn.get("voice_pending"):
                with st.spinner("🔊 Generating voice..."):
                    speech = provider.speak(turn["reply"], api_key=api_key, connection=connection, voice=voice)
                turn["voice_pending"] = False
                turn["audio"] = pcm_to_wav(speech) if speech is not None and len(speech) else None
                state.autoplay_last = True
                st.rerun()
            if turn["audio"]:
                st.audio(turn["audio"], format="audio/wav", autoplay=autoplay and is_latest)
            else:
                browser_speech(turn["reply"], autoplay=autoplay and is_latest)
